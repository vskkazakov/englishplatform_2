from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse, JsonResponse
from .forms import CustomUserCreationForm, LoginForm, EmailVerificationForm, VerificationCodeForm
from django.urls import reverse
from .models import VerificationCode
import random
from django.core.mail import send_mail

@csrf_protect
def index(request):
    """Главная страница авторизации с поддержкой верификации по email"""
    # Если пользователь уже авторизован - перенаправляем на главную
    if request.method == 'GET':
        for key in ['verification_email', 'verification_purpose', 'email_verified']:
            request.session.pop(key, None)
    if request.user.is_authenticated:
        return redirect('/')
    if 'verification_email' in request.session and not request.session.get('email_verified', False):
        return handle_verification_stage(request)

    # Обработка POST-запросов
    if request.method == 'POST':
        if 'register_final' in request.POST:
            return handle_registration(request)
        if 'register_final' in request.POST:
            return handle_registration(request)
        elif 'login_final' in request.POST:
            return handle_login(request)
        elif 'register' in request.POST:
            return handle_initial_registration(request)
        elif 'login' in request.POST:
            return handle_initial_login(request)
    
    # Начальный этап - выбор регистрации/входа
    registration_form = EmailVerificationForm(prefix='reg')
    login_form = EmailVerificationForm(prefix='login')
    
    context = {
        'stage': 'initial',
        'registration_form': registration_form,
        'login_form': login_form,
        'show_registration': True
    }
    return render(request, 'authen/authen.html', context)

def handle_initial_registration(request):
    """Обработка начального этапа регистрации (отправка кода)"""
    form = EmailVerificationForm(request.POST, prefix='reg')
    if form.is_valid():
        email = form.cleaned_data['email']
        form.send_verification_code('register')
        request.session['verification_email'] = email
        request.session['verification_purpose'] = 'register'
        request.session['email_verified'] = False  # сбросить флаг проверки
        messages.success(request, 'Код подтверждения отправлен на ваш email.')
        # Показываем форму для ввода кода — НЕ делать redirect, а рендерить нужную страницу:
        code_form = VerificationCodeForm(email=email, purpose='register')
        context = {
            'stage': 'verification',
            'code_form': code_form,
            'email': email
        }
        return render(request, 'authen/authen.html', context)
    else:
        for error in form.errors.values():
            messages.error(request, error)
    
    # Если форма невалидна, показываем начальную страницу с ошибками
    login_form = EmailVerificationForm(prefix='login')
    context = {
        'stage': 'initial',
        'registration_form': form,
        'login_form': login_form,
        'show_registration': True
    }
    return render(request, 'authen/authen.html', context)

def handle_initial_login(request):
    """Обработка начального этапа входа (отправка кода)"""
    form = EmailVerificationForm(request.POST, prefix='login')
    if form.is_valid():
        # Отправляем код и сохраняем email в сессии
        email = form.cleaned_data['email']
        form.send_verification_code('login')
        request.session['verification_email'] = email
        request.session['verification_purpose'] = 'login'
        request.session['email_verified'] = False

        messages.success(request, 'Код подтверждения отправлен на ваш email')

        # Показываем форму для ввода кода (НЕ redirect!)
        code_form = VerificationCodeForm(email=email, purpose='login')
        context = {
            'stage': 'verification',
            'code_form': code_form,
            'email': email
        }
        return render(request, 'authen/authen.html', context)

    else:
        for error in form.errors.values():
            messages.error(request, error)

        # Если форма невалидна, показываем начальную страницу с ошибками
        registration_form = EmailVerificationForm(prefix='reg')
        context = {
            'stage': 'initial',
            'registration_form': registration_form,
            'login_form': form,
            'show_registration': False
        }
        return render(request, 'authen/authen.html', context)


def handle_verification_stage(request):
    """Обработка этапа верификации кода"""
    email = request.session.get('verification_email')
    purpose = request.session.get('verification_purpose')
    
    if not email or not purpose:
        messages.error(request, 'Сессия устарела. Начните сначала.')
        return redirect('authen:index')
    
    # Обработка отправки кода
    if request.method == 'POST' and 'verify_code' in request.POST:
        form = VerificationCodeForm(
            request.POST, 
            email=email, 
            purpose=purpose
        )
        
        if form.is_valid():
            request.session['email_verified'] = True
            # Для регистрации - показываем форму регистрации
            if purpose == 'register':
                registration_form = CustomUserCreationForm(
                    initial={'email': email}
                )
                context = {
                    'stage': 'registration',
                    'registration_form': registration_form,
                    'email': email
                }
                return render(request, 'authen/authen.html', context)
            
            # Для входа - показываем форму входа
            elif purpose == 'login':
                login_form = LoginForm(initial={'email': email})
                context = {
                    'stage': 'login',
                    'login_form': login_form,
                    'email': email
                }
                return render(request, 'authen/authen.html', context)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    # Показ формы ввода кода
    code_form = VerificationCodeForm(email=email, purpose=purpose)
    context = {
        'stage': 'verification',
        'code_form': code_form,
        'email': email
    }
    return render(request, 'authen/authen.html', context)

def handle_registration(request):
    """Обработка финального этапа регистрации"""
    if not request.session.get('email_verified', False):
        messages.error(request, 'Верификация не пройдена')
        return redirect('authen:index')
    
    email = request.session['verification_email']
    
    if request.method == 'POST':
        # Создаем пользователя напрямую из POST-данных
        first_name = request.POST.get('first_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')
        
        # Простейшая валидация
        errors = []
        if not first_name:
            errors.append("Имя обязательно")
        if password1 != password2:
            errors.append("Пароли не совпадают")
        if not password1:
            errors.append("Пароль обязателен")
        if not role:
            errors.append("Выберите роль")
            
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Создаем пользователя
                user = User.objects.create_user(
                    username=email,  # используем email как username
                    email=email,
                    password=password1,
                    first_name=first_name
                )
                
                # Создаем профиль
                from .models import UserProfile
                profile = UserProfile.objects.create(user=user, role=role)
                
                # Очищаем сессию
                for key in ['verification_email', 'verification_purpose', 'email_verified']:
                    if key in request.session:
                        del request.session[key]
                
                # Входим
                login(request, user)
                messages.success(request, f'Добро пожаловать, {first_name}!')
                return redirect('/')
                
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    
    # Если GET запрос или есть ошибки, показываем форму
    context = {
        'stage': 'registration',
        'email': email
    }
    return render(request, 'authen/authen.html', context)

def handle_login(request):
    """Обработка финального этапа входа"""
    if not request.session.get('email_verified', False):
        messages.error(request, 'Верификация не пройдена')
        return redirect('authen:index')
    
    email = request.session['verification_email']
    login_form = LoginForm(request.POST)
    
    if login_form.is_valid():
        password = login_form.cleaned_data['password']
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Очищаем сессию верификации
                    for key in ['verification_email', 'verification_purpose', 'email_verified']:
                        if key in request.session:
                            del request.session[key]
                    
                    login(request, user)
                    messages.success(
                        request,
                        f'Добро пожаловать, {user.first_name}! Вы успешно вошли в систему.'
                    )
                    return redirect('/')
                else:
                    messages.error(request, 'Ваш аккаунт заблокирован.')
            else:
                messages.error(request, 'Неверный пароль. Попробуйте еще раз.')
        except User.DoesNotExist:
            messages.error(
                request,
                'Пользователь с таким email не найден. Проверьте правильность написания или зарегистрируйтесь.'
            )
        except Exception as e:
            messages.error(request, f'Ошибка при входе: {str(e)}')
    else:
        messages.error(request, 'Пожалуйста, исправьте ошибки в форме входа.')
    
    context = {
        'stage': 'login',
        'login_form': login_form,
        'email': email
    }
    return render(request, 'authen/authen.html', context)

def resend_code(request):
    """Повторная отправка кода подтверждения"""
    if request.method == 'POST' and 'verification_email' in request.session:
        email = request.session['verification_email']
        purpose = request.session['verification_purpose']
        
        # Удаляем старые коды для этого email
        VerificationCode.objects.filter(email=email, purpose=purpose).delete()
        
        # Генерируем и отправляем новый код
        code = ''.join(random.choices('0123456789', k=6))
        VerificationCode.objects.create(
            email=email,
            code=code,
            purpose=purpose
        )
        
        # Отправка email (в реальном проекте настройте EMAIL_BACKEND)
        send_mail(
            'Код подтверждения',
            f'Ваш новый код подтверждения: {code}',
            'krivkokazakov@yandex.ru',
            [email],
            fail_silently=False,
        )
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Не удалось отправить код'})

def logout_view(request):
    """Выход пользователя из системы"""
    if request.user.is_authenticated:
        logout(request)
        for key in ['verification_email', 'verification_purpose', 'email_verified']:
            request.session.pop(key, None)
        messages.success(request, "Вы успешно вышли из системы.")
    else:
        messages.info(request, 'Вы не были авторизованы.')
    
    return redirect('authen:index')

def test_db_connection(request):
    """Тестовая функция для проверки подключения к базе данных"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        # Проверяем количество пользователей
        users_count = User.objects.count()
        
        # Получаем последних пользователей
        recent_users = User.objects.order_by('-date_joined')[:3]
        
        html_response = f"""
        <h2>Статус подключения к базе данных</h2>
        <p><strong>Версия БД:</strong> {db_version[0] if db_version else 'SQLite'}</p>
        <p><strong>Количество пользователей:</strong> {users_count}</p>
        
        <h3>Последние пользователи:</h3>
        <table border="1">
            <tr><th>Имя</th><th>Email</th><th>Дата регистрации</th></tr>
            {''.join([f'<tr><td>{user.first_name or "Не указано"}</td><td>{user.email}</td><td>{user.date_joined.strftime("%d.%m.%Y %H:%M")}</td></tr>' for user in recent_users])}
        </table>
        
        <p><a href="/authen/">← Вернуться к авторизации</a> | <a href="/admin/">Админ панель</a></p>
        
        <p><strong>Система готова к использованию.</strong></p>
        """
        return HttpResponse(html_response)
    except Exception as e:
        error_html = f"""
        <h2>Ошибка подключения к базе данных</h2>
        <p><strong>Ошибка:</strong> {str(e)}</p>
        
        <h3>Возможные причины:</h3>
        <ul>
            <li>База данных не настроена</li>
            <li>Миграции не выполнены</li>
            <li>Неверные настройки подключения</li>
        </ul>
        
        <p><a href="/authen/">← Вернуться к авторизации</a></p>
        """
        return HttpResponse(error_html)
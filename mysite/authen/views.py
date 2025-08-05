from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
from .forms import CustomUserCreationForm, LoginForm
from django.urls import reverse

@csrf_protect
def index(request):
    """Главная страница авторизации - обработка GET и POST запросов"""
    if request.method == 'POST':
        # Определяем, какая форма была отправлена
        if 'register' in request.POST:
            return handle_registration(request)
        elif 'login' in request.POST:
            return handle_login(request)
    
    # GET запрос - показываем пустые формы
    registration_form = CustomUserCreationForm()
    login_form = LoginForm()
    
    context = {
        'registration_form': registration_form,
        'login_form': login_form,
        'show_registration': True  # По умолчанию показываем регистрацию
    }
    return render(request, 'authen/authen.html', context)

def handle_registration(request):
    registration_form = CustomUserCreationForm(request.POST)
    login_form = LoginForm()
    
    if registration_form.is_valid():
        try:
            user = registration_form.save()
            # После сохранения пользователя сразу логиним его
            login(request, user)
            messages.success(
                request,
                f'Регистрация прошла успешно! Добро пожаловать, {user.first_name}.'
            )
            return redirect('/')  # Переход на главную страницу
        except Exception as e:
            messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
    else:
        for field, errors in registration_form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    context = {
        'registration_form': registration_form,
        'login_form': login_form,
        'show_registration': True,
    }
    return render(request, 'authen/authen.html', context)

def handle_login(request):
    registration_form = CustomUserCreationForm()
    login_form = LoginForm(request.POST)
    
    if login_form.is_valid():
        email = login_form.cleaned_data['email']
        password = login_form.cleaned_data['password']
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(
                        request,
                        f'Добро пожаловать, {user.first_name}! Вы успешно вошли в систему.'
                    )
                    return redirect('/')  # Переход на главную страницу под авторизованным
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
        'registration_form': registration_form,
        'login_form': login_form,
        'show_registration': False,
    }
    return render(request, 'authen/authen.html', context)


def logout_view(request):
    """Выход пользователя из системы"""
    if request.user.is_authenticated:
        user_name = request.user.first_name
        logout(request)
        messages.success(request, f'До свидания, {user_name}! Вы успешно вышли из системы.')
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

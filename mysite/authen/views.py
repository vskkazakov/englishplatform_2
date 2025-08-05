from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
from .forms import CustomUserCreationForm, LoginForm

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
    """Обработка регистрации нового пользователя"""
    registration_form = CustomUserCreationForm(request.POST)
    login_form = LoginForm()

    if registration_form.is_valid():
        try:
            # Сохраняем нового пользователя в базу данных
            user = registration_form.save()

            messages.success(
                request, 
                f'Регистрация прошла успешно! Пользователь {user.first_name} создан. '
                f'Теперь вы можете войти в систему.'
            )

            # Переключаемся на форму входа после успешной регистрации
            context = {
                'registration_form': CustomUserCreationForm(),
                'login_form': login_form,
                'show_registration': False
            }
            return render(request, 'authen/authen.html', context)

        except Exception as e:
            messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
    else:
        messages.error(request, 'Пожалуйста, исправьте ошибки в форме регистрации.')

    context = {
        'registration_form': registration_form,
        'login_form': login_form,
        'show_registration': True
    }
    return render(request, 'authen/authen.html', context)

def handle_login(request):
    """Обработка входа пользователя в систему"""
    registration_form = CustomUserCreationForm()
    login_form = LoginForm(request.POST)

    if login_form.is_valid():
        email = login_form.cleaned_data['email']
        password = login_form.cleaned_data['password']

        try:
            # Ищем пользователя по email в базе данных
            user_obj = User.objects.get(email=email)

            # Аутентификация по username (который равен email)
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                if user.is_active:
                    # Успешный вход
                    login(request, user)

                    messages.success(
                        request, 
                        f'Добро пожаловать, {user.first_name}! Вы успешно вошли в систему.'
                    )

                    # Можно перенаправить на главную страницу или профиль
                    return redirect('/')  # Перенаправляем на главную страницу
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
        'show_registration': False  # Показываем форму входа
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
        <html>
        <head>
            <title>Тест базы данных</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .success {{ color: #28a745; }}
                .info {{ color: #17a2b8; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>🔍 Тест подключения к базе данных</h2>

            <h3 class="success">✅ Подключение работает!</h3>
            <p><strong>Версия БД:</strong> {db_version[0] if db_version else 'SQLite'}</p>

            <h3>📊 Статистика:</h3>
            <p><strong>Количество пользователей:</strong> {users_count}</p>

            <h3>👥 Последние зарегистрированные пользователи:</h3>
            <table>
                <tr><th>Имя</th><th>Email</th><th>Дата регистрации</th></tr>
        """

        for user in recent_users:
            html_response += f"""
                <tr>
                    <td>{user.first_name or 'Не указано'}</td>
                    <td>{user.email}</td>
                    <td>{user.date_joined.strftime('%d.%m.%Y %H:%M')}</td>
                </tr>
            """

        html_response += f"""
            </table>

            <h3 class="info">🔗 Навигация:</h3>
            <p>
                <a href="/authen/">← Вернуться к авторизации</a> | 
                <a href="/admin/">Админ панель</a>
            </p>

            <h3>✅ Базовая система работает!</h3>
            <p>Система готова к использованию.</p>
        </body>
        </html>
        """

        return HttpResponse(html_response)

    except Exception as e:
        error_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h2>❌ Ошибка подключения к базе данных</h2>
            <p><strong>Ошибка:</strong> {str(e)}</p>
            <p><strong>Возможные причины:</strong></p>
            <ul>
                <li>База данных не запущена</li>
                <li>Неверные данные подключения в settings.py</li>
                <li>Не установлены необходимые пакеты</li>
                <li>Не выполнены миграции</li>
            </ul>
            <p><a href="/authen/">← Вернуться к авторизации</a></p>
        </body>
        </html>
        """
        return HttpResponse(error_html)

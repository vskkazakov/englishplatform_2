from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import VerificationCode
import random
from django.core.mail import send_mail

class EmailVerificationForm(forms.Form):
    """Форма для запроса кода подтверждения"""
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )

    def send_verification_code(self, purpose):
        email = self.cleaned_data['email']
        code = ''.join(random.choices('0123456789', k=6))
        
        # Удаляем старые коды для этого email
        VerificationCode.objects.filter(email=email).delete()
        
        # Создаем новый код
        VerificationCode.objects.create(
            email=email,
            code=code,
            purpose=purpose
        )
        
        # Отправка email (в реальном проекте настройте EMAIL_BACKEND)
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {code}',
            'krivkokazakov@yandex.ru',
            [email],
            fail_silently=False,
        )
        return code

class VerificationCodeForm(forms.Form):
    """Форма для ввода кода подтверждения"""
    code = forms.CharField(
        label="Код подтверждения",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите код из письма'
        })
    )
    
    def __init__(self, *args, email=None, purpose=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email
        self.purpose = purpose
    
    def clean_code(self):
        code = self.cleaned_data['code']
        try:
            v_code = VerificationCode.objects.get(
                email=self.email,
                code=code,
                purpose=self.purpose,
                is_used=False
            )
            if not v_code.is_valid():
                raise ValidationError("Код устарел. Запросите новый.")
            v_code.is_used = True
            v_code.save()
            return code
        except VerificationCode.DoesNotExist:
            raise ValidationError("Неверный код подтверждения")

class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации пользователя"""
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.RadioSelect, label="Роль")
    
    # ОДНО объявление email - скрытое поле
    email = forms.EmailField(
        required=True, 
        label="Email",
        widget=forms.HiddenInput()
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы и русские метки
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
        self.fields['role'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите роль'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль'
        })
        
        # Меняем метки на русские
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"
        
        # Убираем стандартные help_text
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def clean_email(self):
        """Проверяем уникальность email"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        
        # Генерируем уникальное имя пользователя
        base_username = user.email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user.username = username
        
        if commit:
            user.save()
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.save()
        return user

class LoginForm(forms.Form):
    """Форма входа в систему"""
    # ОДНО объявление email - скрытое поле
    email = forms.EmailField(widget=forms.HiddenInput())
    
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

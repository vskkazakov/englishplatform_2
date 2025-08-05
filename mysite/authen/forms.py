from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации пользователя"""
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.RadioSelect, label="Роль")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'email', 'password1', 'password2', 'role')  # Добавил first_name

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
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.save()
        return user

class LoginForm(forms.Form):
    """Форма входа в систему"""
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class VerificationCode(models.Model):
    email = models.EmailField(verbose_name="Email")
    code = models.CharField(max_length=6, verbose_name="Код подтверждения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_used = models.BooleanField(default=False, verbose_name="Использован")
    purpose = models.CharField(
        max_length=10, 
        choices=[('register', 'Регистрация'), ('login', 'Вход')],
        verbose_name="Назначение"
    )

    class Meta:
        verbose_name = "Код подтверждения"
        verbose_name_plural = "Коды подтверждения"
        indexes = [
            models.Index(fields=['email', 'code']),
        ]

    def __str__(self):
        return f"{self.email} - {self.code}"
    
    def is_valid(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).seconds < 600 and not self.is_used

class UserProfile(models.Model):
    """
    Расширенный профиль пользователя
    Связан с встроенной моделью User через OneToOneField
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )

    # Дополнительные поля профиля
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Телефон",
        help_text="Формат: +7 (XXX) XXX-XX-XX"
    )

    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Дата рождения"
    )

    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True,
        verbose_name="Аватар",
        help_text="Загрузите фото профиля"
    )

    bio = models.TextField(
        max_length=500, 
        blank=True,
        verbose_name="О себе",
        help_text="Расскажите немного о себе"
    )

    # Настройки уведомлений
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Email уведомления"
    )

    # Статистика
    registration_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="IP регистрации"
    )

    last_login_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="Последний IP входа"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания профиля"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    ROLE_CHOICES = [
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name="Роль пользователя"
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        ordering = ['-created_at']

    def __str__(self):
        return f"Профиль {self.user.get_full_name() or self.user.username}"

    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        return self.user.get_full_name()

    def get_age(self):
        """Вычисляет возраст пользователя"""
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Автоматически сохраняет профиль при сохранении User
    """
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

class LoginHistory(models.Model):
    """
    История входов пользователей в систему
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="login_history"
    )

    login_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время входа"
    )

    ip_address = models.GenericIPAddressField(
        verbose_name="IP адрес"
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Информация о браузере"
    )

    success = models.BooleanField(
        default=True,
        verbose_name="Успешный вход"
    )

    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Причина неудачи"
    )

    class Meta:
        verbose_name = "История входа"
        verbose_name_plural = "История входов"
        ordering = ['-login_time']

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.user.username} - {self.login_time.strftime('%d.%m.%Y %H:%M')}"

class UserSettings(models.Model):
    """
    Настройки пользователя для изучения английского
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )

    # Уровень английского
    ENGLISH_LEVELS = [
        ('beginner', 'Начинающий'),
        ('elementary', 'Элементарный'),
        ('intermediate', 'Средний'),
        ('upper_intermediate', 'Выше среднего'),
        ('advanced', 'Продвинутый'),
        ('proficiency', 'Профессиональный'),
    ]

    english_level = models.CharField(
        max_length=20,
        choices=ENGLISH_LEVELS,
        default='beginner',
        verbose_name="Уровень английского"
    )

    # Предпочтения обучения
    daily_goal = models.PositiveIntegerField(
        default=10,
        verbose_name="Ежедневная цель (минут)"
    )

    notification_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Время напоминаний"
    )

    # Статистика
    total_study_time = models.PositiveIntegerField(
        default=0,
        verbose_name="Общее время изучения (минут)"
    )

    words_learned = models.PositiveIntegerField(
        default=0,
        verbose_name="Изучено слов"
    )

    tests_completed = models.PositiveIntegerField(
        default=0,
        verbose_name="Пройдено тестов"
    )

    current_streak = models.PositiveIntegerField(
        default=0,
        verbose_name="Текущая серия дней"
    )

    best_streak = models.PositiveIntegerField(
        default=0,
        verbose_name="Лучшая серия дней"
    )

    class Meta:
        verbose_name = "Настройки пользователя"
        verbose_name_plural = "Настройки пользователей"

    def __str__(self):
        return f"Настройки {self.user.username}"

# Вспомогательные функции для работы с моделями
def get_client_ip(request):
    """Получает IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_login_attempt(user, request, success=True, failure_reason=""):
    """Логирует попытку входа в систему"""
    LoginHistory.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        success=success,
        failure_reason=failure_reason
    )

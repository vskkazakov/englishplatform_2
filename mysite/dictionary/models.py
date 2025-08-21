from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator


class Category(models.Model):
    """
    Модель для категорий слов
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Название категории"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание категории"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="Создатель"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )


    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        unique_together = ['name', 'created_by']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.created_by.username})"


class Word(models.Model):
    """
    Модель для хранения слов пользователей в словаре
    """
    # Связь с пользователем
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="words"
    )

    # Основные поля слова
    english_word = models.CharField(
        max_length=100,
        verbose_name="Английское слово",
        validators=[MinLengthValidator(1)],
        help_text="Введите английское слово"
    )

    russian_translation = models.CharField(
        max_length=200,
        verbose_name="Русский перевод",
        validators=[MinLengthValidator(1)],
        help_text="Введите перевод на русский язык"
    )

    transcription = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Транскрипция",
        help_text="Фонетическая транскрипция (например, [ˈwɜːrd])"
    )

    definition = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Определение",
        help_text="Определение на английском"
    )

    example_sentence = models.TextField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="Пример",
        help_text="Пример предложения"
    )

    # ИСПРАВЛЕНО: Категория теперь ForeignKey на Category модель
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        related_name="words",
        help_text="Категория слова"
    )

    # Уровни сложности
    DIFFICULTY_CHOICES = [
        ('beginner', 'Начинающий'),
        ('elementary', 'Элементарный'),
        ('intermediate', 'Средний'),
        ('upper_intermediate', 'Выше среднего'),
        ('advanced', 'Продвинутый'),
        ('proficiency', 'Профессиональный'),
    ]

    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        verbose_name="Уровень сложности"
    )

    # ИСПРАВЛЕНО: Убрал дублирование полей - оставил только одну версию каждого поля
    # Статистика изучения
    is_learned = models.BooleanField(
        default=False,
        verbose_name="Выучено"
    )

    times_practiced = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество повторений"
    )

    last_practiced = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последнее повторение"
    )

    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        ordering = ['-created_at']
        unique_together = ['user', 'english_word', 'category']
        indexes = [
            models.Index(fields=['user', 'is_learned']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'difficulty_level']),
            models.Index(fields=['last_practiced']),
        ]

    def __str__(self):
        return f"{self.english_word} - {self.russian_translation}"

    def mark_as_learned(self):
        self.is_learned = True
        self.save(update_fields=['is_learned'])

    def mark_as_not_learned(self):
        self.is_learned = False
        self.save(update_fields=['is_learned'])

    def increment_practice(self):
        self.times_practiced += 1
        self.last_practiced = timezone.now()
        self.save(update_fields=['times_practiced', 'last_practiced'])

    def get_progress_percentage(self):
        if self.is_learned:
            return 100
        # Предполагается, что учеба считается завершённой после 10 повторений
        return min(int((self.times_practiced / 10) * 100), 99)

    def needs_practice(self):
        if not self.last_practiced:
            return True
        days_since = (timezone.now() - self.last_practiced).days
        if days_since > 7:
            return True
        if not self.is_learned and days_since > 3:
            return True
        return False


class StudySession(models.Model):
    """
    Модель для отслеживания сессий изучения слов
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="study_sessions"
    )

    words_studied = models.ManyToManyField(
        'Word',
        verbose_name="Изученные слова",
        blank=True
    )

    start_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время начала"
    )

    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время окончания"
    )

    words_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество слов"
    )

    correct_answers = models.PositiveIntegerField(
        default=0,
        verbose_name="Правильных ответов"
    )

    class Meta:
        verbose_name = "Сессия изучения"
        verbose_name_plural = "Сессии изучения"
        ordering = ['-start_time']

    def __str__(self):
        return f"Сессия {self.user.username} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"

    def get_duration_minutes(self):
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0

    def get_success_rate(self):
        if self.words_count > 0:
            return int((self.correct_answers / self.words_count) * 100)
        return 0


class WordStatistics(models.Model):
    """
    Модель хранения статистики по пользователю
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="word_statistics"
    )

    total_words_added = models.PositiveIntegerField(
        default=0,
        verbose_name="Добавлено слов"
    )

    words_learned = models.PositiveIntegerField(
        default=0,
        verbose_name="Выучено слов"
    )

    total_practice_time = models.PositiveIntegerField(
        default=0,
        verbose_name="Общее время практики (мин)"
    )

    current_streak = models.PositiveIntegerField(
        default=0,
        verbose_name="Текущая серия дней"
    )

    best_streak = models.PositiveIntegerField(
        default=0,
        verbose_name="Максимальная серия дней"
    )

    last_study_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Последняя дата обучения"
    )

    class Meta:
        verbose_name = "Статистика слов"
        verbose_name_plural = "Статистика слов"

    def __str__(self):
        return f"Статистика пользователя {self.user.username}"

    def update_words_count(self):
        self.total_words_added = self.user.words.count()
        self.words_learned = self.user.words.filter(is_learned=True).count()
        self.save(update_fields=['total_words_added', 'words_learned'])

    def update_streak(self):
        today = timezone.now().date()
        if not self.last_study_date:
            self.current_streak = 1
            self.last_study_date = today
        elif self.last_study_date == today:
            pass
        elif self.last_study_date == today - timezone.timedelta(days=1):
            self.current_streak += 1
            self.last_study_date = today
        else:
            self.current_streak = 1
            self.last_study_date = today

        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        
        self.save(update_fields=['current_streak', 'best_streak', 'last_study_date'])

# test/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from dictionary.models import Word  # Импортируем Word из приложения dictionary


class TestSession(models.Model):
    """
    Модель для сессий тестирования
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="test_sessions"
    )
    
    categories = models.JSONField(
        default=list,
        verbose_name="Категории для тестирования"
    )
    
    total_words = models.PositiveIntegerField(
        default=0,
        verbose_name="Общее количество слов в тесте"
    )
    
    correct_answers = models.PositiveIntegerField(
        default=0,
        verbose_name="Правильные ответы"
    )
    
    incorrect_answers = models.PositiveIntegerField(
        default=0,
        verbose_name="Неправильные ответы"
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
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Тест завершен"
    )
    
    duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Длительность выполнения"
    )

    def get_duration_minutes(self):
        """Получить продолжительность теста в минутах"""
        if self.duration:
            return int(self.duration.total_seconds() // 60)
        return 0

    class Meta:
        verbose_name = "Сессия тестирования"
        verbose_name_plural = "Сессии тестирования"
        ordering = ['-start_time']

    def __str__(self):
        return f"Тест {self.user.username} - {self.start_time.strftime('%d.%m.%Y %H:%M')}"

    def get_success_rate(self):
        """Получить процент успешности"""
        if self.total_words > 0:
            return int((self.correct_answers / self.total_words) * 100)
        return 0

    def get_categories_display(self):
        """Получить строку с категориями"""
        return ", ".join(self.categories) if self.categories else "Нет категорий"

    duration = models.PositiveIntegerField(
        default=0,
        verbose_name="Длительность выполнения (сек)"
    )

    def get_duration_minutes(self):
        """Получить продолжительность теста в минутах"""
        return round(self.duration / 60, 1) if self.duration else 0

class TestAnswer(models.Model):
    """
    Модель для ответов в тестах
    """
    test_session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Сессия теста"
    )
    
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        verbose_name="Слово"
    )
    
    user_answer = models.CharField(
        max_length=200,
        verbose_name="Ответ пользователя"
    )
    
    is_correct = models.BooleanField(
        verbose_name="Правильный ответ"
    )
    
    answer_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время ответа"
    )

    class Meta:
        verbose_name = "Ответ в тесте"
        verbose_name_plural = "Ответы в тестах"

    def __str__(self):
        return f"{self.word.english_word} - {self.user_answer} ({'✓' if self.is_correct else '✗'})"

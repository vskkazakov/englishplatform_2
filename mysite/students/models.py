from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class StudentRequest(models.Model):
    """
    Запрос ученика к учителю на обучение
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонен'),
        ('cancelled', 'Отменен'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_requests',
        verbose_name="Ученик"
    )
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_requests',
        verbose_name="Учитель"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус запроса"
    )
    
    message = models.TextField(
        blank=True,
        verbose_name="Сообщение от ученика"
    )
    
    teacher_response = models.TextField(
        blank=True,
        verbose_name="Ответ учителя"
    )
    
    student_response = models.TextField(
        blank=True,
        verbose_name="Ответ ученика"
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
        verbose_name = "Запрос на обучение"
        verbose_name_plural = "Запросы на обучение"
        unique_together = ['student', 'teacher']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} → {self.teacher.get_full_name()} ({self.get_status_display()})"

class StudentTeacherRelationship(models.Model):
    """
    Связь между учеником и учителем
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_relationships',
        verbose_name="Ученик"
    )
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_teacher_relationships',
        verbose_name="Учитель"
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата начала обучения"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Заметки учителя"
    )
    
    class Meta:
        verbose_name = "Связь ученик-учитель"
        verbose_name_plural = "Связи ученик-учитель"
        unique_together = ['student', 'teacher']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} учится у {self.teacher.get_full_name()}"

class Homework(models.Model):
    """
    Домашнее задание от учителя ученику
    """
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='homework_given',
        verbose_name="Учитель"
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='homework_received',
        verbose_name="Ученик"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Название задания"
    )
    
    description = models.TextField(
        verbose_name="Описание задания"
    )
    
    due_date = models.DateTimeField(
        verbose_name="Срок выполнения"
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Выполнено"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата выполнения"
    )
    
    teacher_feedback = models.TextField(
        blank=True,
        verbose_name="Отзыв учителя"
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
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.student.get_full_name()}"
class CategorySharingRequest(models.Model):
    """
    Запрос учителя на передачу категории слов ученику
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
    ]

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='category_sharing_requests_sent',
        verbose_name="Учитель"
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='category_sharing_requests_received',
        verbose_name="Ученик"
    )

    # Предполагаем, что в dictionary есть модель Category
    category = models.ForeignKey(
        'dictionary.Category',  # Связь с моделью Category из приложения dictionary
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус запроса"
    )

    message = models.TextField(
        blank=True,
        verbose_name="Сообщение от учителя"
    )

    student_response = models.TextField(
        blank=True,
        verbose_name="Ответ ученика"
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
        verbose_name = "Запрос на передачу категории"
        verbose_name_plural = "Запросы на передачу категорий"
        unique_together = ['teacher', 'student', 'category']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher.get_full_name()} → {self.student.get_full_name()}: {self.category.name} ({self.get_status_display()})"

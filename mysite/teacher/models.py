from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TeacherRequest(models.Model):
    """
    Запрос учителя к ученику на обучение
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонен'),
        ('cancelled', 'Отменен'),
    ]
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_student_relationships',
        verbose_name="Учитель"
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_requests_received',
        verbose_name="Ученик"
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
    
    teacher_response = models.TextField(
        blank=True,
        verbose_name="Ответ учителя"
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
        verbose_name = "Запрос учителя"
        verbose_name_plural = "Запросы учителей"
        unique_together = ['teacher', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} → {self.student.get_full_name()} ({self.get_status_display()})"

class TeacherStudentRelationship(models.Model):
    """
    Связь между учителем и учеником
    """
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_relationships',
        verbose_name="Учитель"
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_relationships_received',
        verbose_name="Ученик"
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
        verbose_name="Заметки ученика"
    )
    
    class Meta:
        verbose_name = "Связь учитель-ученик"
        verbose_name_plural = "Связи учитель-ученик"
        unique_together = ['teacher', 'student']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} учится у {self.teacher.get_full_name()}"

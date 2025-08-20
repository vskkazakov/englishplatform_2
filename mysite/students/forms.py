from django import forms
from .models import StudentRequest, StudentTeacherRelationship, Homework
from authen.models import UserProfile

class StudentRequestForm(forms.ModelForm):
    """
    Форма для отправки запроса на обучение
    """
    class Meta:
        model = StudentRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Напишите, почему вы хотите учиться у этого учителя...'
            })
        }
        labels = {
            'message': 'Сообщение учителю'
        }

class StudentResponseForm(forms.ModelForm):
    """
    Форма для ответа ученика на приглашение учителя
    """
    class Meta:
        model = StudentRequest
        fields = ['student_response', 'status']
        widgets = {
            'student_response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш ответ учителю...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'student_response': 'Ваш ответ',
            'status': 'Решение'
        }

class StudentSearchForm(forms.Form):
    """
    Форма для поиска учеников
    """
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по имени или email...'
        }),
        label='Поиск'
    )
    
    role_filter = forms.ChoiceField(
        choices=[('', 'Все роли')] + UserProfile.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Роль'
    )

class HomeworkForm(forms.ModelForm):
    """
    Форма для создания домашнего задания
    """
    class Meta:
        model = Homework
        fields = ['title', 'description', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название задания'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание задания...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'due_date': 'Срок выполнения'
        }

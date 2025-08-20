from django import forms
from .models import TeacherRequest, TeacherStudentRelationship
from authen.models import UserProfile

class TeacherRequestForm(forms.ModelForm):
    """
    Форма для отправки запроса от ученика к учителю
    """
    class Meta:
        model = TeacherRequest
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

class TeacherResponseForm(forms.ModelForm):
    """
    Форма для ответа учителя на запрос ученика
    """
    class Meta:
        model = TeacherRequest
        fields = ['teacher_response', 'status']
        widgets = {
            'teacher_response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш ответ ученику...'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'teacher_response': 'Ваш ответ',
            'status': 'Решение'
        }

class TeacherSearchForm(forms.Form):
    """
    Форма для поиска учителей
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

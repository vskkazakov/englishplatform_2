from django.shortcuts import render
from authen.models import UserProfile

def index(request):
    is_teacher = False
    is_student = False
    
    if request.user.is_authenticated:
        try:
            # Получаем профиль пользователя
            profile = UserProfile.objects.get(user=request.user)
            is_teacher = profile.role == 'teacher'
            is_student = profile.role == 'student'
        except UserProfile.DoesNotExist:
            is_teacher = False
            is_student = False
    
    context = {
        'is_teacher': is_teacher,
        'is_student': is_student,
    }
    
    return render(request, 'mainApp/index.html', context)

def contact(request):
    return render(request, 'mainApp/contact.html', {'values' : ['Если вопросы', '1234567']})


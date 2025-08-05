from django.shortcuts import render
from authen.models import UserProfile

def index(request):
    is_teacher = False
    if request.user.is_authenticated:
        try:
            # Получаем профиль пользователя
            profile = UserProfile.objects.get(user=request.user)
            is_teacher = profile.role == 'teacher'
        except UserProfile.DoesNotExist:
            is_teacher = False
    return render(request, 'mainApp/index.html', {'is_teacher': is_teacher})

def contact(request):
    return render(request, 'mainApp/contact.html', {'values' : ['Если вопросы', '1234567']})


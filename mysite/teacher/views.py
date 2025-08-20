from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import TeacherRequest, TeacherStudentRelationship
from .forms import TeacherRequestForm, TeacherResponseForm, TeacherSearchForm
from authen.models import UserProfile
from students.models import Homework, StudentRequest
from students.models import StudentTeacherRelationship

@login_required
def index(request):
    """
    Показывает учителей ученика или сообщение о том, что нужно найти учителей
    """
    print(f"DEBUG: index called by user {request.user.email}")
    
    # Проверяем, что пользователь - ученик
    try:
        profile = UserProfile.objects.get(user=request.user)
        print(f"DEBUG: user profile role={profile.role}")
        if profile.role != 'student':
            return redirect('index')
    except UserProfile.DoesNotExist:
        return redirect('index')
    
    # Получаем текущих учителей (с которыми установлена связь)
    current_teachers = StudentTeacherRelationship.objects.filter(
        student=request.user
    ).select_related('teacher').order_by('-started_at')
    print(f"DEBUG: Found {current_teachers.count()} current teachers")
    
    # Получаем входящие приглашения от учителей
    incoming_requests = StudentRequest.objects.filter(
        student=request.user,
        status='pending'
    ).select_related('teacher').order_by('-created_at')
    print(f"DEBUG: Found {incoming_requests.count()} incoming requests")
    
    # Получаем домашние задания, назначенные ученику
    homework_list = Homework.objects.filter(
        student=request.user
    ).select_related('teacher').order_by('-created_at')
    print(f"DEBUG: Found {homework_list.count()} homework assignments")
    
    context = {
        'current_teachers': current_teachers,
        'incoming_requests': incoming_requests,
        'homework_list': homework_list,
    }
    
    return render(request, 'teacher/teacher.html', context)

@login_required
def send_request(request, teacher_id):
    """
    Отправка запроса на обучение от ученика к учителю
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'})
    
    # Проверяем, что пользователь - ученик
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'student':
            return JsonResponse({'success': False, 'error': 'Только ученики могут отправлять запросы'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})
    
    # Проверяем, что учитель существует и является учителем
    try:
        teacher_profile = UserProfile.objects.get(user_id=teacher_id, role='teacher')
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Учитель не найден'})
    
    # Проверяем, что запрос еще не отправлен
    if TeacherRequest.objects.filter(student=request.user, teacher_id=teacher_id).exists():
        return JsonResponse({'success': False, 'error': 'Запрос уже отправлен'})
    
    # Создаем запрос
    form = TeacherRequestForm(request.POST)
    if form.is_valid():
        request_obj = form.save(commit=False)
        request_obj.student = request.user
        request_obj.teacher_id = teacher_id
        request_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Запрос отправлен учителю {teacher_profile.user.get_full_name()}'
        })
    else:
        return JsonResponse({'success': False, 'error': 'Неверные данные формы'})

@login_required
def cancel_request(request, request_id):
    """
    Отмена запроса на обучение от ученика к учителю
    """
    try:
        teacher_request = TeacherRequest.objects.get(
            id=request_id,
            student=request.user,
            status='pending'
        )
        teacher_request.status = 'cancelled'
        teacher_request.save()
        messages.success(request, 'Запрос отменен')
    except TeacherRequest.DoesNotExist:
        messages.error(request, 'Запрос не найден')
    
    return redirect('teacher:index')

@login_required
def my_teachers(request):
    """
    Страница для ученика - показывает его учителей
    """
    # Проверяем, что пользователь - ученик
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'student':
            messages.error(request, 'Доступ только для учеников')
            return redirect('index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Профиль не найден')
        return redirect('index')
    
    # Получаем учителей ученика
    relationships = TeacherStudentRelationship.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('teacher', 'teacher__userprofile')

    # ИСПРАВЛЕНО: Получаем входящие запросы от учителей из приложения students
    incoming_requests = StudentRequest.objects.filter(
        student=request.user,
        status='pending'
    ).select_related('teacher', 'teacher__userprofile')
    
    # Получаем домашние задания
    homework_list = Homework.objects.filter(
        student=request.user
    ).select_related('teacher').order_by('-created_at')
    
    context = {
        'relationships': relationships,
        'incoming_requests': incoming_requests,
        'homework_list': homework_list,
    }
    
    return render(request, 'teacher/my_teachers.html', context)

@login_required
def respond_to_request(request, request_id):
    """
    Ответ ученика на запрос учителя
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'})
    
    # Проверяем, что пользователь - ученик
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'student':
            return JsonResponse({'success': False, 'error': 'Доступ только для учеников'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})
    
    # ИСПРАВЛЕНО: Получаем запрос из приложения students
    try:
        student_request = StudentRequest.objects.get(
            id=request_id,
            student=request.user,
            status='pending'
        )
    except StudentRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Запрос не найден'})
    
    # Обрабатываем ответ
    status = request.POST.get('status')
    if status in ['accepted', 'rejected']:
        student_request.status = status
        student_request.save()
        
        # Если запрос принят, создаем связь в приложении students
        if status == 'accepted':
            from students.models import StudentTeacherRelationship
            StudentTeacherRelationship.objects.get_or_create(
                student=request.user,
                teacher=student_request.teacher
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Запрос {student_request.get_status_display().lower()}',
            'status': status
        })
    else:
        return JsonResponse({'success': False, 'error': 'Неверный статус'})

@login_required
def view_homework(request, homework_id):
    """
    Просмотр домашнего задания учеником
    """
    homework = get_object_or_404(Homework, id=homework_id, student=request.user)
    
    context = {
        'homework': homework,
    }
    
    return render(request, 'teacher/view_homework.html', context)

@login_required
def complete_homework(request, homework_id):
    """
    Отметка домашнего задания как выполненного
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'})
    
    # Проверяем, что пользователь - ученик
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'student':
            return JsonResponse({'success': False, 'error': 'Только ученики могут отмечать задания как выполненные'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})
    
    # Получаем домашнее задание
    try:
        homework = Homework.objects.get(id=homework_id, student=request.user)
    except Homework.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Задание не найдено'})
    
    # Отмечаем как выполненное
    homework.is_completed = True
    homework.completed_at = timezone.now()
    homework.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Задание отмечено как выполненное'
    })

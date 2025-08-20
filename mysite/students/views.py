from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import StudentRequest, StudentTeacherRelationship, Homework
from .forms import StudentRequestForm, StudentResponseForm, StudentSearchForm, HomeworkForm
from authen.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def index(request):
    """
    Главная страница для учителей - показывает текущих учеников и домашние задания
    """
    print(f"DEBUG: index called by user {request.user.email}")
    
    # Проверяем, что пользователь - учитель
    try:
        profile = UserProfile.objects.get(user=request.user)
        print(f"DEBUG: user profile role={profile.role}")
        if profile.role != 'teacher':
            return redirect('index')
    except UserProfile.DoesNotExist:
        return redirect('index')
    
    # Получаем текущих учеников (с которыми установлена связь)
    current_students = StudentTeacherRelationship.objects.filter(
        teacher=request.user
    ).select_related('student').order_by('-started_at')
    print(f"DEBUG: Found {current_students.count()} current students")
    
    # Получаем домашние задания, назначенные учителем
    homework_list = Homework.objects.filter(
        teacher=request.user
    ).select_related('student').order_by('-created_at')
    print(f"DEBUG: Found {homework_list.count()} homework assignments")
    
    context = {
        'current_students': current_students,
        'homework_list': homework_list,
    }
    
    return render(request, 'students/students.html', context)

@login_required
def send_request(request, student_id):  # ИЗМЕНЕНО: student_email -> student_id
    """
    Отправка приглашения от учителя к ученику
    """
    print(f"DEBUG: send_request called with student_id={student_id}")
    print(f"DEBUG: request.user={request.user}")
    print(f"DEBUG: request.method={request.method}")

    if request.method != 'POST':
        print("DEBUG: Method not POST")
        return JsonResponse({'success': False, 'error': 'Неверный метод'})

    # Проверяем, что пользователь - учитель
    try:
        profile = UserProfile.objects.get(user=request.user)
        print(f"DEBUG: user profile role={profile.role}")
        if profile.role != 'teacher':
            print("DEBUG: User is not a teacher")
            return JsonResponse({'success': False, 'error': 'Только учителя могут отправлять приглашения'})
    except UserProfile.DoesNotExist:
        print("DEBUG: UserProfile not found")
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})

    # ИСПРАВЛЕНО: Поиск ученика по ID вместо email
    try:
        print(f"DEBUG: Looking for user with id: {student_id}")
        student_user = User.objects.get(id=student_id)  # ИЗМЕНЕНО
        print(f"DEBUG: Found user: {student_user.username}")
        student_profile = UserProfile.objects.get(user=student_user, role='student')
        print(f"DEBUG: student profile found: {student_profile.user.username}")
    except User.DoesNotExist:
        print(f"DEBUG: User with id {student_id} not found")
        return JsonResponse({'success': False, 'error': 'Ученик не найден'})
    except UserProfile.DoesNotExist:
        print(f"DEBUG: UserProfile for user {student_user.username} not found or not a student")
        return JsonResponse({'success': False, 'error': 'Ученик не найден'})

    # ИСПРАВЛЕНО: Проверяем, что приглашение еще не отправлено или было отклонено/отменено
    existing_request = StudentRequest.objects.filter(teacher=request.user, student=student_user).first()
    if existing_request and existing_request.status == 'pending':
        print("DEBUG: Request already exists and pending")
        return JsonResponse({'success': False, 'error': 'Приглашение уже отправлено'})
    
    # Если запрос был отклонен или отменен, обновляем его
    if existing_request and existing_request.status in ['rejected', 'cancelled']:
        print("DEBUG: Updating existing rejected/cancelled request")
        existing_request.status = 'pending'
        existing_request.message = request.POST.get('message', '')
        existing_request.save()
        return JsonResponse({
            'success': True,
            'message': f'Приглашение повторно отправлено ученику {student_profile.user.get_full_name()}'
        })

    # Создаем новый запрос
    form = StudentRequestForm(request.POST)
    if form.is_valid():
        request_obj = form.save(commit=False)
        request_obj.teacher = request.user
        request_obj.student = student_user
        request_obj.save()
        print(f"DEBUG: Request created successfully")
        return JsonResponse({
            'success': True,
            'message': f'Приглашение отправлено ученику {student_profile.user.get_full_name()}'
        })
    else:
        print(f"DEBUG: Form errors: {form.errors}")
        return JsonResponse({'success': False, 'error': 'Неверные данные формы'})

@login_required
def cancel_request(request, request_id):
    """
    Отмена приглашения от учителя к ученику
    """
    try:
        student_request = StudentRequest.objects.get(
            id=request_id,
            teacher=request.user,
            status='pending'
        )
        student_request.status = 'cancelled'
        student_request.save()
        messages.success(request, 'Приглашение отменено')
    except StudentRequest.DoesNotExist:
        messages.error(request, 'Приглашение не найдено')
    
    return redirect('students:index')

@login_required
def my_students(request):
    """
    Страница для учителя - показывает его учеников
    """
    # Проверяем, что пользователь - учитель
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'teacher':
            messages.error(request, 'Доступ только для учителей')
            return redirect('index')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Профиль не найден')
        return redirect('index')
    
    # Получаем учеников учителя
    relationships = StudentTeacherRelationship.objects.filter(
        teacher=request.user,
        is_active=True
    ).select_related('student', 'student__userprofile')
    
    # Получаем входящие запросы от учеников
    incoming_requests = StudentRequest.objects.filter(
        teacher=request.user,
        status='pending'
    ).select_related('student', 'student__userprofile')
    
    # Получаем домашние задания
    homework_list = Homework.objects.filter(
        teacher=request.user
    ).select_related('student').order_by('-created_at')
    
    context = {
        'relationships': relationships,
        'incoming_requests': incoming_requests,
        'homework_list': homework_list,
    }
    
    return render(request, 'students/my_students.html', context)

@login_required
def respond_to_request(request, request_id):
    """
    Ответ учителя на запрос ученика
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'})
    
    # Проверяем, что пользователь - учитель
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'teacher':
            return JsonResponse({'success': False, 'error': 'Доступ только для учителей'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})
    
    # Получаем запрос
    try:
        student_request = StudentRequest.objects.get(
            id=request_id,
            teacher=request.user,
            status='pending'
        )
    except StudentRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Запрос не найден'})
    
    # Обрабатываем ответ
    status = request.POST.get('status')
    if status in ['accepted', 'rejected']:
        student_request.status = status
        student_request.save()
        
        # Если запрос принят, создаем связь
        if status == 'accepted':
            StudentTeacherRelationship.objects.get_or_create(
                student=student_request.student,
                teacher=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Ученик {student_request.get_status_display().lower()}'
        })
    else:
        return JsonResponse({'success': False, 'error': 'Неверный статус'})

@login_required
def create_homework(request, student_id):  # ИЗМЕНЕНО: student_email -> student_id
    """
    Создание домашнего задания для ученика
    """
    # Проверяем, что пользователь - учитель
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'teacher':
            return JsonResponse({'success': False, 'error': 'Доступ только для учителей'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})

    # ИСПРАВЛЕНО: Получаем ученика по ID вместо email
    try:
        student_user = User.objects.get(id=student_id)  # ИЗМЕНЕНО
        student_profile = UserProfile.objects.get(user=student_user, role='student')
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Ученик не найден'})

    # Проверяем, что у учителя есть связь с этим учеником
    if not StudentTeacherRelationship.objects.filter(
        teacher=request.user,
        student=student_user,
        is_active=True
    ).exists():
        return JsonResponse({'success': False, 'error': 'У вас нет активной связи с этим учеником'})

    if request.method == 'POST':
        form = HomeworkForm(request.POST)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.teacher = request.user
            homework.student = student_user
            homework.save()
            return JsonResponse({
                'success': True,
                'message': f'Домашнее задание создано для {student_profile.user.get_full_name()}'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Неверные данные формы'})

    return JsonResponse({'success': False, 'error': 'Неверный метод'})


@login_required
def view_homework(request, homework_id):
    """
    Просмотр домашнего задания
    """
    homework = get_object_or_404(Homework, id=homework_id)
    
    # Проверяем права доступа
    if request.user != homework.teacher and request.user != homework.student:
        messages.error(request, 'Нет доступа к этому заданию')
        return redirect('students:my_students')
    
    context = {
        'homework': homework,
    }
    
    return render(request, 'students/view_homework.html', context)

def test_view(request):
    """
    Тестовое представление для проверки URL-ов
    """
    return JsonResponse({'success': True, 'message': 'Test view works!'})

@login_required
def get_students_list(request):
    """
    AJAX endpoint для получения списка учеников для добавления
    """
    # Проверяем, что пользователь - учитель
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'teacher':
            return JsonResponse({'success': False, 'error': 'Доступ только для учителей'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Профиль не найден'})
    
    # Получаем поисковый запрос
    search_query = request.GET.get('search', '')
    
    # Получаем учеников
    students = UserProfile.objects.filter(role='student').exclude(user=request.user)
    
    # Применяем поиск
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Получаем существующие запросы и связи
    existing_requests = StudentRequest.objects.filter(teacher=request.user)
    existing_relationships = StudentTeacherRelationship.objects.filter(teacher=request.user)
    
    # Формируем список учеников
    students_list = []
    for student_profile in students:
        student_user = student_profile.user
        
        # Проверяем статус запроса
        request_obj = existing_requests.filter(student=student_user).first()
        has_request = request_obj is not None
        request_status = request_obj.status if request_obj else None
        
        # Проверяем, является ли уже учеником
        is_current_student = existing_relationships.filter(student=student_user).exists()
        
        students_list.append({
            'id': student_user.id,
            'name': student_user.get_full_name() or student_user.username,
            'email': student_user.email,
            'has_request': has_request,
            'request_status': request_status,
            'is_current_student': is_current_student,
        })
    
    return JsonResponse({
        'success': True,
        'students': students_list
    })

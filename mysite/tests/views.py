# tests/views.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Avg
import random

from dictionary.models import Word
from .models import TestSession, TestAnswer
from .forms import TestCategorySelectForm, TestAnswerForm


def index(request):
    """Главная страница тестов"""
    context = {
        'title': 'Тесты по английскому языку'
    }
    return render(request, 'tests/index.html', context)  # ← ИСПРАВЛЕНО: tests/index.html


@login_required
def categories(request):
    """Выбор категорий для тестирования"""
    # Проверяем, есть ли у пользователя слова
    total_words = request.user.words.count()
    if total_words == 0:
        messages.warning(request, 'У вас пока нет слов в словаре. Добавьте слова для начала тестирования.')
        return redirect('/dictionary/')  # Перенаправляем в словарь
    
    if request.method == 'POST':
        form = TestCategorySelectForm(request.POST, user=request.user)
        if form.is_valid():
            # Сохраняем настройки теста в сессии
            test_config = {
                'categories': form.cleaned_data['categories'],
                'words_count': form.cleaned_data['words_count'],
                'test_mode': form.cleaned_data['test_mode'],
                'include_learned': form.cleaned_data['include_learned'],
                'word_selection': form.cleaned_data['word_selection'],
            }
            request.session['test_config'] = test_config
            return redirect('tests:start')  # ← ИСПРАВЛЕНО: tests:start
    else:
        form = TestCategorySelectForm(user=request.user)
    
    # Статистика для показа
    categories_count = request.user.words.values('category').distinct().count()
    
    context = {
        'form': form,
        'total_words': total_words,
        'categories_count': categories_count,
        'title': 'Выберите категории для тестирования'
    }
    
    return render(request, 'tests/categories.html', context)  # ← ИСПРАВЛЕНО


@login_required
def start(request):
    """Начало тестирования"""
    # Получаем конфигурацию из сессии
    test_config = request.session.get('test_config')
    if not test_config:
        messages.warning(request, 'Пожалуйста, выберите параметры тестирования.')
        return redirect('tests:categories')  # ← ИСПРАВЛЕНО
    
    # Создаем новую сессию тестирования
    test_session = TestSession.objects.create(
        user=request.user,
        categories=test_config['categories']
    )
    
    # Формируем queryset слов для тестирования
    words_queryset = request.user.words.filter(
        category__in=test_config['categories']
    )
    
    # Применяем фильтры
    if not test_config['include_learned']:
        words_queryset = words_queryset.filter(is_learned=False)
    
    # Метод выбора слов
    selection_method = test_config['word_selection']
    if selection_method == 'least_practiced':
        words_queryset = words_queryset.order_by('times_practiced')
    elif selection_method == 'newest':
        words_queryset = words_queryset.order_by('-created_at')
    elif selection_method == 'most_difficult':
        words_queryset = words_queryset.filter(
            difficulty_level__in=['advanced', 'proficiency']
        ).order_by('times_practiced')
    else:  # random
        words_queryset = words_queryset.order_by('?')
    
    # Ограничиваем количество слов
    words_count = min(test_config['words_count'], words_queryset.count())
    selected_words = list(words_queryset[:words_count])
    
    if not selected_words:
        messages.warning(request, 'Не найдено слов для тестирования с выбранными параметрами.')
        return redirect('tests:categories')  # ← ИСПРАВЛЕНО
    
    # Для смешанного режима перемешиваем типы вопросов
    if test_config['test_mode'] == 'mixed':
        # Создаем список режимов для каждого слова
        modes = ['en_to_ru', 'ru_to_en'] * (len(selected_words) // 2 + 1)
        random.shuffle(modes)
        word_modes = modes[:len(selected_words)]
    else:
        word_modes = [test_config['test_mode']] * len(selected_words)
    
    # Сохраняем слова и их режимы в сессии
    test_words_data = []
    for i, word in enumerate(selected_words):
        test_words_data.append({
            'word_id': word.id,
            'mode': word_modes[i]
        })
    
    request.session['test_session_id'] = test_session.id
    request.session['test_words_data'] = test_words_data
    request.session['current_word_index'] = 0
    
    # Обновляем статистику сессии
    test_session.total_words = len(selected_words)
    test_session.save()
    
    return redirect('tests:question')  # ← ИСПРАВЛЕНО


@login_required
def question(request):
    """Отображение вопроса теста"""
    # Получаем данные сессии
    test_session_id = request.session.get('test_session_id')
    test_words_data = request.session.get('test_words_data', [])
    current_index = request.session.get('current_word_index', 0)
    
    if not test_session_id or not test_words_data:
        messages.error(request, 'Сессия тестирования не найдена.')
        return redirect('tests:categories')  # ← ИСПРАВЛЕНО
    
    # Проверяем, не закончился ли тест
    if current_index >= len(test_words_data):
        return redirect('tests:results')  # ← ИСПРАВЛЕНО
    
    try:
        test_session = TestSession.objects.get(id=test_session_id, user=request.user)
    except TestSession.DoesNotExist:
        messages.error(request, 'Сессия тестирования не найдена.')
        return redirect('tests:categories')  # ← ИСПРАВЛЕНО
    
    # Получаем текущее слово
    current_word_data = test_words_data[current_index]
    current_word = get_object_or_404(
        Word, 
        id=current_word_data['word_id'], 
        user=request.user
    )
    current_mode = current_word_data['mode']
    
    # Обрабатываем ответ
    if request.method == 'POST':
        form = TestAnswerForm(request.POST, word=current_word, test_mode=current_mode)
        if form.is_valid():
            is_correct = form.is_correct()
            user_answer = form.cleaned_data['answer']
            
            # Сохраняем ответ
            TestAnswer.objects.create(
                test_session=test_session,
                word=current_word,
                user_answer=user_answer,
                is_correct=is_correct
            )
            
            # Обновляем статистику сессии
            if is_correct:
                test_session.correct_answers += 1
                messages.success(request, 'Правильно! 🎉')
            else:
                test_session.incorrect_answers += 1
                correct_answer = form.get_correct_answer()
                messages.error(request, f'Неправильно. Правильный ответ: {correct_answer}')
            
            test_session.save()
            
            # Переходим к следующему слову
            request.session['current_word_index'] = current_index + 1
            
            # Показываем результат на несколько секунд
            context = {
                'show_result': True,
                'is_correct': is_correct,
                'current_word': current_word,
                'user_answer': user_answer,
                'correct_answer': form.get_correct_answer(),
                'current_index': current_index + 1,
                'total_words': len(test_words_data),
                'test_mode': current_mode,
                'progress_percentage': int(((current_index + 1) / len(test_words_data)) * 100)
            }
            
            return render(request, 'tests/question.html', context)  # ← ИСПРАВЛЕНО
    else:
        form = TestAnswerForm(word=current_word, test_mode=current_mode)
    
    # Определяем, что показывать пользователю
    if current_mode == 'en_to_ru':
        question_word = current_word.english_word
        question_hint = f"Транскрипция: {current_word.transcription}" if current_word.transcription else ""
        question_type = "Переведите на русский:"
    else:  # ru_to_en
        question_word = current_word.russian_translation
        question_hint = f"Определение: {current_word.definition}" if current_word.definition else ""
        question_type = "Переведите на английский:"
    
    context = {
        'form': form,
        'current_word': current_word,
        'question_word': question_word,
        'question_hint': question_hint,
        'question_type': question_type,
        'current_index': current_index + 1,
        'total_words': len(test_words_data),
        'test_mode': current_mode,
        'progress_percentage': int(((current_index + 1) / len(test_words_data)) * 100),
        'show_result': False
    }
    
    return render(request, 'tests/question.html', context)  # ← ИСПРАВЛЕНО


@login_required
def results(request):
    """Результаты тестирования"""
    test_session_id = request.session.get('test_session_id')
    
    if not test_session_id:
        messages.error(request, 'Сессия тестирования не найдена.')
        return redirect('tests:categories')  # ← ИСПРАВЛЕНО
    
    try:
        test_session = TestSession.objects.get(id=test_session_id, user=request.user)
    except TestSession.DoesNotExist:
        messages.error(request, 'Сессия тестирования не найдена.')
        return redirect('tests:categories')  # ← ИСПРАВЛЕНО
    
    # Завершаем тест
    test_session.end_time = timezone.now()
    test_session.is_completed = True
    test_session.save()
    
    # Получаем детализированные результаты
    answers = test_session.answers.all().order_by('answer_time')
    
    # Статистика по категориям
    category_stats = {}
    for answer in answers:
        category = answer.word.category
        if category not in category_stats:
            category_stats[category] = {'correct': 0, 'total': 0}
        
        category_stats[category]['total'] += 1
        if answer.is_correct:
            category_stats[category]['correct'] += 1
    
    # Добавляем процент успешности по категориям
    for category in category_stats:
        total = category_stats[category]['total']
        correct = category_stats[category]['correct']
        category_stats[category]['percentage'] = int((correct / total) * 100) if total > 0 else 0
    
    # Очищаем сессионные данные
    session_keys = ['test_session_id', 'test_words_data', 'current_word_index', 'test_config']
    for key in session_keys:
        request.session.pop(key, None)
    
    context = {
        'test_session': test_session,
        'answers': answers,
        'category_stats': category_stats,
        'success_rate': test_session.get_success_rate(),
        'duration': test_session.get_duration_minutes(),
    }
    
    return render(request, 'tests/results.html', context)  # ← ИСПРАВЛЕНО


@login_required
def history(request):
    """История тестов"""
    test_sessions = request.user.test_sessions.filter(
        is_completed=True
    ).order_by('-start_time')[:20]
    
    # Общая статистика тестов
    total_tests = request.user.test_sessions.filter(is_completed=True).count()
    if total_tests > 0:
        # Вычисляем средний процент успешности
        completed_tests = request.user.test_sessions.filter(is_completed=True)
        total_success = sum([test.get_success_rate() for test in completed_tests])
        avg_success_rate = int(total_success / total_tests) if total_tests > 0 else 0
    else:
        avg_success_rate = 0
    
    context = {
        'test_sessions': test_sessions,
        'total_tests': total_tests,
        'avg_success_rate': avg_success_rate,
        'title': 'История тестов'
    }
    
    return render(request, 'tests/history.html', context)  # ← ИСПРАВЛЕНО

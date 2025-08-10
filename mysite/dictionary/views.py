# views.py - Представления для приложения словаря

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
import random

from .models import Word, StudySession, WordStatistics
from .forms import (
    WordForm, WordSearchForm, StudyConfigForm, 
    BulkWordImportForm, WordQuizForm
)


@login_required
def index(request):
    """Главная страница словаря с статистикой"""
    
    # Получаем или создаем статистику пользователя
    stats, created = WordStatistics.objects.get_or_create(user=request.user)
    if created or stats.total_words_added == 0:
        stats.update_words_count()
    
    # Статистика слов
    total_words = request.user.words.count()
    learned_words = request.user.words.filter(is_learned=True).count()
    words_need_practice = request.user.words.filter(
        Q(last_practiced__isnull=True) | 
        Q(last_practiced__lt=timezone.now() - timezone.timedelta(days=7))
    ).count()
    
    # Последние добавленные слова
    recent_words = request.user.words.order_by('-created_at')[:5]
    
    # Статистика по категориям
    category_stats = request.user.words.values('category').annotate(
        count=Count('id'),
        learned_count=Count('id', filter=Q(is_learned=True))
    ).order_by('-count')
    
    # Прогресс изучения
    progress_percentage = 0
    if total_words > 0:
        progress_percentage = int((learned_words / total_words) * 100)
    
    context = {
        'total_words': total_words,
        'learned_words': learned_words,
        'words_need_practice': words_need_practice,
        'progress_percentage': progress_percentage,
        'recent_words': recent_words,
        'category_stats': category_stats,
        'stats': stats,
    }
    
    return render(request, 'dictionary/index.html', context)


@login_required
def add_word(request):
    """Добавление нового слова"""
    
    if request.method == 'POST':
        form = WordForm(request.POST, user=request.user)
        if form.is_valid():
            word = form.save()
            
            # Обновляем статистику
            stats, created = WordStatistics.objects.get_or_create(user=request.user)
            stats.update_words_count()
            
            messages.success(request, f'Слово "{word.english_word}" успешно добавлено в словарь!')
            
            # Если запрос AJAX, возвращаем JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Слово "{word.english_word}" добавлено!',
                    'word_id': word.id
                })
            
            return redirect('dictionary:view_words')
        else:
            # Если есть ошибки формы
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = WordForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Добавить новое слово'
    }
    
    return render(request, 'dictionary/add_word.html', context)


@login_required
def view_words(request):
    """Просмотр всех слов пользователя с фильтрацией и поиском"""
    
    # Форма поиска и фильтров
    search_form = WordSearchForm(request.GET)
    
    # Базовый queryset
    words_queryset = request.user.words.all()
    
    # Применяем фильтры
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query')
        category = search_form.cleaned_data.get('category')
        difficulty_level = search_form.cleaned_data.get('difficulty_level')
        status = search_form.cleaned_data.get('status')
        sort_by = search_form.cleaned_data.get('sort_by')
        
        # Поиск по слову или переводу
        if search_query:
            words_queryset = words_queryset.filter(
                Q(english_word__icontains=search_query) |
                Q(russian_translation__icontains=search_query)
            )
        
        # Фильтр по категории
        if category:
            words_queryset = words_queryset.filter(category=category)
        
        # Фильтр по уровню сложности
        if difficulty_level:
            words_queryset = words_queryset.filter(difficulty_level=difficulty_level)
        
        # Фильтр по статусу изучения
        if status == 'learned':
            words_queryset = words_queryset.filter(is_learned=True)
        elif status == 'not_learned':
            words_queryset = words_queryset.filter(is_learned=False)
        elif status == 'needs_practice':
            week_ago = timezone.now() - timezone.timedelta(days=7)
            words_queryset = words_queryset.filter(
                Q(last_practiced__isnull=True) | 
                Q(last_practiced__lt=week_ago)
            )
        
        # Сортировка
        if sort_by:
            words_queryset = words_queryset.order_by(sort_by)
    
    # Пагинация
    paginator = Paginator(words_queryset, 20)  # 20 слов на страницу
    page_number = request.GET.get('page')
    words = paginator.get_page(page_number)
    
    # Статистика для текущей выборки
    total_filtered = words_queryset.count()
    learned_filtered = words_queryset.filter(is_learned=True).count()
    
    context = {
        'words': words,
        'search_form': search_form,
        'total_filtered': total_filtered,
        'learned_filtered': learned_filtered,
        'total_words': request.user.words.count(),
    }
    
    return render(request, 'dictionary/view_words.html', context)


@login_required
def edit_word(request, word_id):
    """Редактирование слова"""
    
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    if request.method == 'POST':
        form = WordForm(request.POST, instance=word, user=request.user)
        if form.is_valid():
            word = form.save()
            messages.success(request, f'Слово "{word.english_word}" успешно обновлено!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Слово "{word.english_word}" обновлено!'
                })
            
            return redirect('dictionary:view_words')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = WordForm(instance=word, user=request.user)
    
    context = {
        'form': form,
        'word': word,
        'title': f'Редактировать слово: {word.english_word}'
    }
    
    return render(request, 'dictionary/edit_word.html', context)


@login_required
@require_http_methods(["POST"])
def delete_word(request, word_id):
    """Удаление слова"""
    
    word = get_object_or_404(Word, id=word_id, user=request.user)
    word_name = word.english_word
    word.delete()
    
    # Обновляем статистику
    stats, created = WordStatistics.objects.get_or_create(user=request.user)
    stats.update_words_count()
    
    messages.success(request, f'Слово "{word_name}" удалено из словаря.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Слово "{word_name}" удалено!'
        })
    
    return redirect('dictionary:view_words')


@login_required
@require_http_methods(["POST"])
def toggle_learned(request, word_id):
    """Переключение статуса изученности слова"""
    
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    if word.is_learned:
        word.mark_as_not_learned()
        status = 'не изучено'
    else:
        word.mark_as_learned()
        status = 'изучено'
    
    # Обновляем статистику
    stats, created = WordStatistics.objects.get_or_create(user=request.user)
    stats.update_words_count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_learned': word.is_learned,
            'message': f'Слово "{word.english_word}" отмечено как {status}'
        })
    
    messages.success(request, f'Слово "{word.english_word}" отмечено как {status}')
    return redirect('dictionary:view_words')


@login_required
def study_setup(request):
    """Настройка сессии изучения слов"""
    
    if request.method == 'POST':
        form = StudyConfigForm(request.POST)
        if form.is_valid():
            # Сохраняем настройки в сессии
            config = form.cleaned_data
            request.session['study_config'] = config
            
            return redirect('dictionary:study_session')
    else:
        form = StudyConfigForm()
    
    # Статистика для выбора
    total_words = request.user.words.count()
    learned_words = request.user.words.filter(is_learned=True).count()
    unlearned_words = total_words - learned_words
    
    context = {
        'form': form,
        'total_words': total_words,
        'learned_words': learned_words,
        'unlearned_words': unlearned_words,
    }
    
    return render(request, 'dictionary/study_setup.html', context)


@login_required
def study_session(request):
    """Сессия изучения слов"""
    
    # Получаем конфигурацию из сессии
    config = request.session.get('study_config')
    if not config:
        messages.warning(request, 'Пожалуйста, настройте параметры изучения.')
        return redirect('dictionary:study_setup')
    
    # Получаем или создаем текущую сессию изучения
    session_id = request.session.get('current_study_session_id')
    
    if session_id:
        try:
            study_session = StudySession.objects.get(id=session_id, user=request.user)
        except StudySession.DoesNotExist:
            study_session = None
    else:
        study_session = None
    
    # Если сессии нет, создаем новую
    if not study_session:
        study_session = StudySession.objects.create(user=request.user)
        request.session['current_study_session_id'] = study_session.id
        
        # Выбираем слова для изучения
        words_queryset = request.user.words.all()
        
        # Применяем фильтры из конфигурации
        if config.get('categories'):
            words_queryset = words_queryset.filter(category__in=config['categories'])
        
        if config.get('difficulty_levels'):
            words_queryset = words_queryset.filter(difficulty_level__in=config['difficulty_levels'])
        
        if not config.get('include_learned', False):
            words_queryset = words_queryset.filter(is_learned=False)
        
        # Метод выбора слов
        selection_method = config.get('selection_method', 'random')
        
        if selection_method == 'least_practiced':
            words_queryset = words_queryset.order_by('times_practiced')
        elif selection_method == 'needs_practice':
            week_ago = timezone.now() - timezone.timedelta(days=7)
            words_queryset = words_queryset.filter(
                Q(last_practiced__isnull=True) | 
                Q(last_practiced__lt=week_ago)
            ).order_by('last_practiced')
        elif selection_method == 'newest':
            words_queryset = words_queryset.order_by('-created_at')
        elif selection_method == 'oldest':
            words_queryset = words_queryset.order_by('created_at')
        else:  # random
            words_queryset = words_queryset.order_by('?')
        
        # Ограничиваем количество слов
        words_count = min(config.get('words_count', 10), words_queryset.count())
        selected_words = list(words_queryset[:words_count])
        
        if not selected_words:
            messages.warning(request, 'Не найдено слов для изучения с выбранными параметрами.')
            return redirect('dictionary:study_setup')
        
        # Добавляем слова в сессию
        study_session.words_studied.set(selected_words)
        study_session.words_count = len(selected_words)
        study_session.save()
        
        # Сохраняем список слов и текущий индекс в сессии браузера
        request.session['study_words_ids'] = [word.id for word in selected_words]
        request.session['current_word_index'] = 0
        request.session['correct_answers'] = 0
    
    # Получаем текущее слово
    words_ids = request.session.get('study_words_ids', [])
    current_index = request.session.get('current_word_index', 0)
    
    if current_index >= len(words_ids):
        # Сессия завершена
        return redirect('dictionary:study_results')
    
    current_word = get_object_or_404(Word, id=words_ids[current_index], user=request.user)
    
    # Обработка ответа
    if request.method == 'POST':
        mode = config.get('mode', 'flashcards')
        
        if mode == 'flashcards':
            # В режиме карточек просто показываем следующее слово
            current_word.increment_practice()
            request.session['current_word_index'] = current_index + 1
            return redirect('dictionary:study_session')
        
        else:
            # В режиме квиза проверяем ответ
            form = WordQuizForm(request.POST, word=current_word, mode=mode)
            if form.is_valid():
                is_correct = form.is_correct()
                
                if is_correct:
                    request.session['correct_answers'] = request.session.get('correct_answers', 0) + 1
                    messages.success(request, 'Правильно!')
                else:
                    if mode == 'translation':
                        correct_answer = current_word.russian_translation
                    else:
                        correct_answer = current_word.english_word
                    messages.error(request, f'Неправильно. Правильный ответ: {correct_answer}')
                
                current_word.increment_practice()
                request.session['current_word_index'] = current_index + 1
                
                # Небольшая задержка для показа результата
                context = {
                    'show_result': True,
                    'is_correct': is_correct,
                    'current_word': current_word,
                    'current_index': current_index + 1,
                    'total_words': len(words_ids),
                    'config': config,
                }
                return render(request, 'dictionary/study_session.html', context)
    
    # Создаем форму для квиза (если нужно)
    mode = config.get('mode', 'flashcards')
    quiz_form = None
    
    if mode != 'flashcards':
        quiz_form = WordQuizForm(word=current_word, mode=mode)
    
    context = {
        'current_word': current_word,
        'current_index': current_index + 1,
        'total_words': len(words_ids),
        'config': config,
        'quiz_form': quiz_form,
        'mode': mode,
    }
    
    return render(request, 'dictionary/study_session.html', context)


@login_required
def study_results(request):
    """Результаты сессии изучения"""
    
    session_id = request.session.get('current_study_session_id')
    if not session_id:
        messages.warning(request, 'Сессия изучения не найдена.')
        return redirect('dictionary:index')
    
    try:
        study_session = StudySession.objects.get(id=session_id, user=request.user)
    except StudySession.DoesNotExist:
        messages.warning(request, 'Сессия изучения не найдена.')
        return redirect('dictionary:index')
    
    # Завершаем сессию
    study_session.end_time = timezone.now()
    study_session.correct_answers = request.session.get('correct_answers', 0)
    study_session.save()
    
    # Обновляем статистику пользователя
    stats, created = WordStatistics.objects.get_or_create(user=request.user)
    stats.update_words_count()
    stats.update_streak()
    stats.total_practice_time += study_session.get_duration_minutes()
    stats.save()
    
    # Очищаем сессионные данные
    session_keys = [
        'current_study_session_id', 'study_words_ids', 
        'current_word_index', 'correct_answers', 'study_config'
    ]
    for key in session_keys:
        request.session.pop(key, None)
    
    context = {
        'study_session': study_session,
        'stats': stats,
    }
    
    return render(request, 'dictionary/study_results.html', context)


@login_required
def bulk_import(request):
    """Массовый импорт слов"""
    
    if request.method == 'POST':
        form = BulkWordImportForm(request.POST)
        if form.is_valid():
            parsed_words = form.cleaned_data['words_text']
            default_category = form.cleaned_data['default_category']
            default_difficulty = form.cleaned_data['default_difficulty']
            skip_duplicates = form.cleaned_data['skip_duplicates']
            
            created_count = 0
            skipped_count = 0
            errors = []
            
            for word_data in parsed_words:
                english_word = word_data['english_word']
                russian_translation = word_data['russian_translation']
                
                # Проверяем на дубликаты
                if skip_duplicates:
                    existing = Word.objects.filter(
                        user=request.user,
                        english_word__iexact=english_word
                    ).exists()
                    
                    if existing:
                        skipped_count += 1
                        continue
                
                try:
                    Word.objects.create(
                        user=request.user,
                        english_word=english_word,
                        russian_translation=russian_translation,
                        category=default_category,
                        difficulty_level=default_difficulty
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Ошибка при создании '{english_word}': {str(e)}")
            
            # Обновляем статистику
            stats, created = WordStatistics.objects.get_or_create(user=request.user)
            stats.update_words_count()
            
            # Сообщения о результатах
            if created_count > 0:
                messages.success(request, f'Успешно добавлено {created_count} слов.')
            
            if skipped_count > 0:
                messages.info(request, f'Пропущено {skipped_count} дубликатов.')
            
            if errors:
                messages.warning(request, f'Ошибки: {"; ".join(errors)}')
            
            if created_count > 0:
                return redirect('dictionary:view_words')
    else:
        form = BulkWordImportForm()
    
    context = {
        'form': form,
        'title': 'Массовый импорт слов'
    }
    
    return render(request, 'dictionary/bulk_import.html', context)


@login_required
def statistics(request):
    """Статистика изучения слов"""
    
    stats, created = WordStatistics.objects.get_or_create(user=request.user)
    if created:
        stats.update_words_count()
    
    # Статистика по категориям
    category_stats = request.user.words.values('category').annotate(
        total=Count('id'),
        learned=Count('id', filter=Q(is_learned=True))
    ).order_by('-total')
    
    # Статистика по уровням сложности
    difficulty_stats = request.user.words.values('difficulty_level').annotate(
        total=Count('id'),
        learned=Count('id', filter=Q(is_learned=True))
    ).order_by('-total')
    
    # Последние сессии изучения
    recent_sessions = request.user.study_sessions.order_by('-start_time')[:10]
    
    # Активность за последние 30 дней
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_activity = request.user.study_sessions.filter(
        start_time__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(start_time)'}
    ).values('day').annotate(
        sessions=Count('id'),
        words_studied=Count('words_studied')
    ).order_by('day')
    
    context = {
        'stats': stats,
        'category_stats': category_stats,
        'difficulty_stats': difficulty_stats,
        'recent_sessions': recent_sessions,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'dictionary/statistics.html', context)


@login_required
def word_detail(request, word_id):
    """Детальная информация о слове"""
    
    word = get_object_or_404(Word, id=word_id, user=request.user)
    
    context = {
        'word': word,
    }
    
    return render(request, 'dictionary/word_detail.html', context)
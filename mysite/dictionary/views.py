# dictionary/views.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, Case, When, F, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
import random
from datetime import datetime, timedelta

from .models import Word, StudySession, WordStatistics, Category
from .forms import (
    WordForm, WordSearchForm, StudyConfigForm,
    BulkWordImportForm, WordQuizForm, QuickWordForm,
    CategorySelectForm, NewCategoryForm
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

    # Статистика по категориям - ИСПРАВЛЕНО
    category_stats = request.user.words.values('category__name').annotate(
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
    # Форма поиска и фильтров с передачей user
    search_form = WordSearchForm(request.GET, user=request.user)

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

        # Фильтр по категории - ИСПРАВЛЕНО
        if category:
            words_queryset = words_queryset.filter(category__name=category)

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
def select_category(request):
    """Выбор существующей категории для добавления слов"""
    # ИСПРАВЛЕНО: Получаем категории пользователя
    user_categories = Category.objects.filter(created_by=request.user).order_by('name')

    if not user_categories.exists():
        messages.info(request, 'У вас пока нет категорий. Создайте первую категорию!')
        return redirect('dictionary:create_category')

    if request.method == 'POST':
        form = CategorySelectForm(request.POST, user=request.user)
        if form.is_valid():
            selected_category_id = form.cleaned_data['category']
            selected_category = Category.objects.get(id=selected_category_id)
            return redirect('dictionary:add_to_category', category_name=selected_category.name)
    else:
        form = CategorySelectForm(user=request.user)

    context = {
        'form': form,
        'title': 'Выберите категорию',
        'user_categories': user_categories,
    }
    return render(request, 'dictionary/select_category.html', context)

@login_required
def create_category(request):
    """Создание новой категории"""
    if request.method == 'POST':
        form = NewCategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']

            # ИСПРАВЛЕНО: Проверяем, не существует ли уже такая категория у пользователя
            existing_category = Category.objects.filter(
                created_by=request.user,
                name__iexact=category_name
            ).first()

            if existing_category:
                messages.warning(request, f'Категория "{category_name}" уже существует!')
                return redirect('dictionary:add_to_category', category_name=existing_category.name)

            # Создаем новую категорию
            category = Category.objects.create(
                name=category_name,
                created_by=request.user
            )

            messages.success(request, f'Категория "{category_name}" создана! Теперь добавьте в неё слова.')
            return redirect('dictionary:add_to_category', category_name=category.name)
    else:
        form = NewCategoryForm()

    context = {
        'form': form,
        'title': 'Создать новую категорию'
    }
    return render(request, 'dictionary/create_category.html', context)

@login_required
def add_to_category(request, category_name):
    """Быстрое добавление слов в выбранную категорию"""
    # ИСПРАВЛЕНО: Получаем или создаем категорию
    category, created = Category.objects.get_or_create(
        name=category_name,
        created_by=request.user
    )

    # Статистика по категории
    words_in_category = request.user.words.filter(category=category).count()

    if request.method == 'POST':
        form = QuickWordForm(request.POST, user=request.user, category=category)
        if form.is_valid():
            word = form.save()

            # Обновляем статистику
            stats, created_stats = WordStatistics.objects.get_or_create(user=request.user)
            stats.update_words_count()

            messages.success(request, f'Слово "{word.english_word}" добавлено в категорию "{category_name}"!')

            # AJAX ответ для быстрого добавления
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Слово "{word.english_word}" добавлено!',
                    'word_id': word.id,
                    'words_count': request.user.words.filter(category=category).count()
                })

            # Перенаправляем обратно на эту же страницу для добавления следующего слова
            return redirect('dictionary:add_to_category', category_name=category_name)
        else:
            # AJAX ошибки
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = QuickWordForm(user=request.user, category=category)

    # Последние добавленные слова в эту категорию
    recent_words = request.user.words.filter(category=category).order_by('-created_at')[:5]

    context = {
        'form': form,
        'category_name': category_name,
        'words_in_category': words_in_category,
        'recent_words': recent_words,
        'title': f'Добавить слово в "{category_name.title()}"'
    }
    return render(request, 'dictionary/add_to_category.html', context)

# Остальные функции остаются без изменений, но добавим несколько ключевых
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
def word_detail(request, word_id):
    """Детальная информация о слове"""
    word = get_object_or_404(Word, id=word_id, user=request.user)
    context = {
        'word': word,
    }
    return render(request, 'dictionary/word_detail.html', context)

# Добавим базовые функции для изучения и статистики
@login_required
def statistics(request):
    """Статистика изучения слов"""
    stats, created = WordStatistics.objects.get_or_create(user=request.user)
    if created:
        stats.update_words_count()

    # ИСПРАВЛЕНО: Статистика по категориям
    category_stats = request.user.words.values('category__name').annotate(
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

    context = {
        'stats': stats,
        'category_stats': category_stats,
        'difficulty_stats': difficulty_stats,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'dictionary/statistics.html', context)

# Заглушки для остальных функций
@login_required
def study_setup(request):
    messages.info(request, 'Функция изучения в разработке')
    return redirect('dictionary:index')

@login_required  
def study_session(request):
    messages.info(request, 'Функция сессии изучения в разработке')
    return redirect('dictionary:index')

@login_required
def study_results(request):
    messages.info(request, 'Функция результатов в разработке')
    return redirect('dictionary:index')

@login_required
def bulk_import(request):
    messages.info(request, 'Функция импорта в разработке')
    return redirect('dictionary:index')

# act_static/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from dictionary.models import Word
from tests.models import TestSession, TestAnswer

@login_required
def index(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Статистика слов
    words = user.words.all()
    total_words = words.count()
    learned_words = words.filter(is_learned=True).count()
    words_need_practice = words.filter(is_learned=False, times_practiced__gt=0).count()
    
    # Прогресс в процентах
    progress_percentage = 0
    if total_words > 0:
        progress_percentage = int((learned_words / total_words) * 100)
    
    # Статистика по тестам
    test_sessions = user.test_sessions.filter(is_completed=True)
    total_tests = test_sessions.count()
    total_questions = 0
    total_correct = 0
    
    # Собираем статистику по категориям для тестов
    category_test_stats = {}
    for session in test_sessions:
        total_questions += session.total_words
        total_correct += session.correct_answers
        
        # Собираем статистику по категориям
        for category in session.categories:
            if category not in category_test_stats:
                category_test_stats[category] = {
                    'total_sessions': 0,
                    'total_questions': 0,
                    'total_correct': 0,
                    'total_time': 0
                }
            
            category_test_stats[category]['total_sessions'] += 1
            category_test_stats[category]['total_questions'] += session.total_words
            category_test_stats[category]['total_correct'] += session.correct_answers
            category_test_stats[category]['total_time'] += session.duration
    
    # Рассчитываем средние значения по категориям
    category_stats = []
    for category, stats in category_test_stats.items():
        avg_success = (stats['total_correct'] / stats['total_questions']) * 100 if stats['total_questions'] > 0 else 0
        avg_time = stats['total_time'] / stats['total_sessions'] if stats['total_sessions'] > 0 else 0
        
        category_stats.append({
            'category': category,
            'avg_success': round(avg_success, 1),
            'avg_time': round(avg_time / 60, 1),  # в минутах
            'total_tests': stats['total_sessions']
        })
    
    # Сортировка категорий по количеству тестов
    category_stats.sort(key=lambda x: x['total_tests'], reverse=True)
    
    # Общая статистика по тестам
    test_stats = {
        'total_tests': total_tests,
        'total_questions': total_questions,
        'total_correct': total_correct,
        'avg_success': round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0,
        'avg_time': 0
    }
    
    if total_tests > 0:
        total_time = sum(s.duration for s in test_sessions)
        test_stats['avg_time'] = round((total_time / total_tests) / 60, 1)  # в минутах
    
    # Последние 5 тестов
    recent_tests = test_sessions.order_by('-start_time')[:5]
    
    # Достижения
    achievements = {
        'current_streak': 7,  # Здесь должна быть логика расчета серии дней
        'best_streak': 15,
        'categories_count': len(category_stats),
        'practice_time': int(sum(s.duration for s in test_sessions) / 60)  # в минутах
    }
    
    # Последние изученные слова
    recent_learned_words = words.filter(is_learned=True).order_by('-last_practiced')[:6]
    
    # Активность по дням
    daily_learned_words = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        day_words = words.filter(
            last_practiced__date=day,
            times_practiced__gt=0
        )
        
        learned_count = day_words.filter(is_learned=True).count()
        
        daily_learned_words.append({
            'date': day,
            'date_formatted': day.strftime("%d.%m"),
            'day_name': day.strftime("%A"),
            'words_learned': learned_count,
            'words_practiced': day_words.count(),
            'words_list': day_words[:3]  # первые 3 слова для показа
        })
    
    context = {
        'total_words': total_words,
        'learned_words': learned_words,
        'words_need_practice': words_need_practice,
        'progress_percentage': progress_percentage,
        'test_stats': test_stats,
        'category_stats': category_stats,
        'recent_tests': recent_tests,
        'achievements': achievements,
        'daily_learned_words': daily_learned_words,
        'recent_learned_words': recent_learned_words,
    }
    
    return render(request, 'act_static/statistics.html', context)
from django.contrib import admin
from .models import TestSession, TestAnswer

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user_link', 
        'categories_display', 
        'total_words', 
        'success_rate_display',
        'duration_display',
        'start_time_display',
        'completion_status'
    ]
    
    list_filter = [
        'is_completed',
        'start_time',
        ('user', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'categories'
    ]
    
    readonly_fields = [
        'start_time',
        'end_time',
        'success_rate_display',
        'duration_display',
        'answers_summary'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'categories', 'is_completed')
        }),
        ('Статистика теста', {
            'fields': ('total_words', 'correct_answers', 'incorrect_answers', 'success_rate_display')
        }),
        ('Время', {
            'fields': ('start_time', 'end_time', 'duration_display')
        }),
        ('Детали ответов', {
            'fields': ('answers_summary',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-start_time']
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'
    
    def categories_display(self, obj):
        """Отображение категорий"""
        if obj.categories:
            categories = obj.get_categories_display()
            if len(categories) > 30:
                return f"{categories[:30]}..."
            return categories
        return "Нет категорий"
    categories_display.short_description = 'Категории'
    
    def success_rate_display(self, obj):
        """Отображение процента успешности с цветом"""
        rate = obj.get_success_rate()
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color, rate
        )
    success_rate_display.short_description = 'Успешность'
    success_rate_display.admin_order_field = 'correct_answers'
    
    def duration_display(self, obj):
        """Отображение длительности"""
        duration = obj.get_duration_minutes()
        if duration == 0:
            return "В процессе"
        elif duration < 5:
            return format_html('<span style="color: green;">{} мин</span>', duration)
        elif duration < 15:
            return format_html('<span style="color: orange;">{} мин</span>', duration)
        else:
            return format_html('<span style="color: red;">{} мин</span>', duration)
    duration_display.short_description = 'Длительность'
    
    def start_time_display(self, obj):
        """Форматированное время начала"""
        return obj.start_time.strftime('%d.%m.%Y %H:%M')
    start_time_display.short_description = 'Начало теста'
    start_time_display.admin_order_field = 'start_time'
    
    def completion_status(self, obj):
        """Статус завершения"""
        if obj.is_completed:
            return format_html('<span style="color: green;">✓ Завершен</span>')
        else:
            return format_html('<span style="color: red;">⏳ В процессе</span>')
    completion_status.short_description = 'Статус'
    completion_status.admin_order_field = 'is_completed'
    
    def answers_summary(self, obj):
        """Краткая сводка ответов"""
        answers = obj.answers.all()
        if not answers:
            return "Нет ответов"
        
        html_parts = ['<div style="max-height: 200px; overflow-y: scroll;">']
        for answer in answers:
            status_icon = '✓' if answer.is_correct else '✗'
            status_color = 'green' if answer.is_correct else 'red'
            
            html_parts.append(
                f'<p><span style="color: {status_color};">{status_icon}</span> '
                f'<strong>{answer.word.english_word}</strong> → '
                f'<em>{answer.user_answer}</em> '
                f'({answer.answer_time.strftime("%H:%M:%S")})</p>'
            )
        html_parts.append('</div>')
        
        return format_html(''.join(html_parts))
    answers_summary.short_description = 'Ответы в тесте'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('answers__word')

@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'test_session_link',
        'user_display',
        'word_display',
        'user_answer',
        'correct_status',
        'answer_time_display'
    ]
    
    list_filter = [
        'is_correct',
        'answer_time',
        ('test_session__user', admin.RelatedFieldListFilter),
        ('word__category', admin.AllValuesFieldListFilter),
    ]
    
    search_fields = [
        'word__english_word',
        'word__russian_translation',
        'user_answer',
        'test_session__user__username'
    ]
    
    readonly_fields = ['answer_time']
    
    ordering = ['-answer_time']
    
    def test_session_link(self, obj):
        """Ссылка на сессию теста"""
        url = reverse('admin:tests_testsession_change', args=[obj.test_session.pk])
        return format_html('<a href="{}">Тест #{}</a>', url, obj.test_session.id)
    test_session_link.short_description = 'Сессия теста'
    test_session_link.admin_order_field = 'test_session'
    
    def user_display(self, obj):
        """Отображение пользователя"""
        return obj.test_session.user.username
    user_display.short_description = 'Пользователь'
    user_display.admin_order_field = 'test_session__user__username'
    
    def word_display(self, obj):
        """Отображение слова"""
        return f"{obj.word.english_word} → {obj.word.russian_translation}"
    word_display.short_description = 'Слово'
    word_display.admin_order_field = 'word__english_word'
    
    def correct_status(self, obj):
        """Статус правильности ответа"""
        if obj.is_correct:
            return format_html('<span style="color: green; font-weight: bold;">✓ Правильно</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Неправильно</span>')
    correct_status.short_description = 'Результат'
    correct_status.admin_order_field = 'is_correct'
    
    def answer_time_display(self, obj):
        """Форматированное время ответа"""
        return obj.answer_time.strftime('%d.%m.%Y %H:%M:%S')
    answer_time_display.short_description = 'Время ответа'
    answer_time_display.admin_order_field = 'answer_time'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'test_session__user', 
            'word'
        )


# Кастомная админка с общей статистикой
class TestStatisticsAdmin(admin.ModelAdmin):
    """Дополнительная статистика по тестам"""
    
    def changelist_view(self, request, extra_context=None):
        # Общая статистика
        total_tests = TestSession.objects.filter(is_completed=True).count()
        total_answers = TestAnswer.objects.count()
        
        # Статистика по успешности
        avg_success = TestSession.objects.filter(
            is_completed=True
        ).aggregate(
            avg_rate=Avg('correct_answers') * 100 / Avg('total_words')
        )['avg_rate'] or 0
        
        # Статистика по пользователям
        user_stats = TestSession.objects.filter(
            is_completed=True
        ).values(
            'user__username'
        ).annotate(
            total_tests=Count('id'),
            avg_success=Avg('correct_answers') * 100 / Avg('total_words')
        ).order_by('-total_tests')[:10]
        
        # Статистика по категориям (топ-5)
        popular_categories = TestAnswer.objects.values(
            'word__category'
        ).annotate(
            total_questions=Count('id'),
            correct_answers=Count('id', filter=Q(is_correct=True))
        ).order_by('-total_questions')[:5]
        
        # Добавляем процент правильных ответов для категорий
        for cat in popular_categories:
            if cat['total_questions'] > 0:
                cat['success_rate'] = int((cat['correct_answers'] / cat['total_questions']) * 100)
            else:
                cat['success_rate'] = 0
        
        extra_context = extra_context or {}
        extra_context.update({
            'title': 'Статистика тестирования',
            'total_tests': total_tests,
            'total_answers': total_answers,
            'avg_success': int(avg_success),
            'user_stats': user_stats,
            'popular_categories': popular_categories,
        })
        
        return super().changelist_view(request, extra_context=extra_context)

# Добавляем кастомные действия
@admin.action(description='Пересчитать статистику выбранных тестов')
def recalculate_test_stats(modeladmin, request, queryset):
    """Пересчет статистики тестов"""
    updated = 0
    for test_session in queryset:
        answers = test_session.answers.all()
        test_session.total_words = answers.count()
        test_session.correct_answers = answers.filter(is_correct=True).count()
        test_session.incorrect_answers = answers.filter(is_correct=False).count()
        test_session.save()
        updated += 1
    
    modeladmin.message_user(request, f'Обновлена статистика для {updated} тестов.')

# Добавляем действие в админку TestSession
TestSessionAdmin.actions = [recalculate_test_stats]

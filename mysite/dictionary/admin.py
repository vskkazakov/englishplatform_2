from django.contrib import admin
from .models import Word

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = (
        'english_word',
        'russian_translation',
        'user',
        'category',
        'difficulty_level',
        'is_learned',
        'times_practiced',
        'created_at',
    )
    list_filter = ('user', 'category', 'difficulty_level', 'is_learned')
    search_fields = ('english_word', 'russian_translation', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

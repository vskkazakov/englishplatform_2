# tests/forms.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from django import forms
from django.core.exceptions import ValidationError
from dictionary.models import Word
import re


class TestCategorySelectForm(forms.Form):
    """Форма для выбора категорий для тестирования"""
    
    categories = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Выберите категории для тестирования",
        help_text="Можно выбрать несколько категорий"
    )
    
    words_count = forms.IntegerField(
        min_value=5,
        max_value=50,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '5',
            'max': '50'
        }),
        label="Количество слов в тесте"
    )
    
    test_mode = forms.ChoiceField(
        choices=[
            ('en_to_ru', 'Английский → Русский'),
            ('ru_to_en', 'Русский → Английский'),
            ('mixed', 'Смешанный режим'),
        ],
        initial='en_to_ru',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label="Режим тестирования"
    )
    
    include_learned = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Включить изученные слова"
    )
    
    word_selection = forms.ChoiceField(
        choices=[
            ('random', 'Случайные слова'),
            ('least_practiced', 'Наименее изучаемые'),
            ('newest', 'Новые слова'),
            ('most_difficult', 'Сложные слова'),
        ],
        initial='random',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Метод выбора слов"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # 🔧 ИСПРАВЛЕНИЕ: получаем категории только конкретного пользователя
            categories = user.words.values_list('category', flat=True).distinct().order_by('category')
            category_choices = []
            
            for cat in categories:
                if cat:
                    words_count = user.words.filter(category=cat).count()
                    category_choices.append((cat, f"{cat.title()} ({words_count} слов)"))
            
            self.fields['categories'].choices = category_choices
            
            if not category_choices:
                self.fields['categories'].choices = [('', 'У вас пока нет слов в словаре')]
        
    def clean_categories(self):
        categories = self.cleaned_data.get('categories')
        if not categories:
            raise ValidationError("Выберите хотя бы одну категорию для тестирования.")
        return categories

    def clean_words_count(self):
        words_count = self.cleaned_data.get('words_count')
        if words_count < 5:
            raise ValidationError("Минимальное количество слов для теста: 5")
        if words_count > 50:
            raise ValidationError("Максимальное количество слов для теста: 50")
        return words_count


class TestAnswerForm(forms.Form):
    """Форма для ответов в тесте"""
    
    answer = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Введите ваш ответ...',
            'autocomplete': 'off',
            'autofocus': True
        }),
        label="Ваш ответ"
    )

    def __init__(self, *args, word=None, test_mode='en_to_ru', **kwargs):
        super().__init__(*args, **kwargs)
        self.word = word
        self.test_mode = test_mode
        
        if test_mode == 'en_to_ru':
            self.fields['answer'].widget.attrs['placeholder'] = 'Введите перевод на русский...'
        elif test_mode == 'ru_to_en':
            self.fields['answer'].widget.attrs['placeholder'] = 'Введите перевод на английский...'

    def clean_answer(self):
        answer = self.cleaned_data.get('answer', '').strip()
        if not answer:
            raise ValidationError("Ответ не может быть пустым.")
        return answer

    def is_correct(self):
        """🔧 ИСПРАВЛЕНИЕ: Строгая проверка правильности ответа"""
        if not self.word or not self.is_valid():
            return False

        user_answer = self.cleaned_data['answer'].strip()
        
        if self.test_mode == 'en_to_ru':
            # Проверяем перевод на русский - строгое совпадение
            correct_answers = []
            
            # Основной перевод
            main_translation = self.word.russian_translation.strip()
            correct_answers.append(main_translation)
            
            # Варианты через запятую или точку с запятой
            if ',' in main_translation:
                variants = [ans.strip() for ans in main_translation.split(',') if ans.strip()]
                correct_answers.extend(variants)
            
            if ';' in main_translation:
                variants = [ans.strip() for ans in main_translation.split(';') if ans.strip()]
                correct_answers.extend(variants)
                
        elif self.test_mode == 'ru_to_en':
            # Проверяем перевод на английский - строгое совпадение
            correct_answers = [self.word.english_word.strip()]
        
        # 🔧 СТРОГАЯ ПРОВЕРКА: точное совпадение с учетом регистра
        for correct in correct_answers:
            if user_answer.lower() == correct.lower():
                return True
        
        return False

    def get_correct_answer(self):
        """Получить правильный ответ"""
        if not self.word:
            return ""
        
        if self.test_mode == 'en_to_ru':
            return self.word.russian_translation
        elif self.test_mode == 'ru_to_en':
            return self.word.english_word
        
        return ""

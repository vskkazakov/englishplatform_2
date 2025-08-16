# forms.py - Формы для приложения словаря

from django import forms
from django.core.exceptions import ValidationError
from .models import Word, StudySession
import re

class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = [
            'english_word',
            'russian_translation',
            'transcription',
            'definition',
            'example_sentence',
            'category',
            'difficulty_level',
        ]
        widgets = {
            'english_word': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите английское слово',
                'required': True,
            }),
            'russian_translation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите русский перевод',
                'required': True,
            }),
            'transcription': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '[ˈwɜːrd] - транскрипция (опционально)',
            }),
            'definition': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Определение на английском',
                'rows': 3,
            }),
            'example_sentence': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Пример предложения',
                'rows': 2,
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Категория (например, Бизнес, IT)',
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['english_word'].label = "Английское слово"
        self.fields['russian_translation'].label = "Русский перевод"
        self.fields['transcription'].label = "Транскрипция"
        self.fields['definition'].label = "Определение"
        self.fields['example_sentence'].label = "Пример"
        self.fields['category'].label = "Категория"
        self.fields['difficulty_level'].label = "Уровень сложности"

    def clean_english_word(self):
        english_word = self.cleaned_data.get('english_word', '').strip()
        if not english_word:
            raise ValidationError("Английское слово не может быть пустым.")
        if not re.match(r"^[a-zA-Z\s\-']+$", english_word):
            raise ValidationError("Английское слово должно содержать только английские буквы, пробелы, дефисы и апострофы.")
        if len(english_word) < 2:
            raise ValidationError("Английское слово должно быть минимум 2 символа.")
        # Проверка уникальности среди слов одного пользователя и категории
        if self.user:
            category = self.cleaned_data.get('category')
            qs = Word.objects.filter(
                user=self.user,
                english_word__iexact=english_word,
                category__iexact=category
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Такое слово уже есть в вашем словаре в данной категории.")
        return english_word.lower()

    def clean_russian_translation(self):
        translation = self.cleaned_data.get('russian_translation', '').strip()
        if not translation:
            raise ValidationError("Русский перевод не может быть пустым.")
        if len(translation) < 1:
            raise ValidationError("Русский перевод должен содержать минимум 1 символ.")
        return translation

    def clean_transcription(self):
        transcription = self.cleaned_data.get('transcription', '')
        if transcription:
            transcription = transcription.strip()
            # Опциональная проверка на формат скобок
            if not (transcription.startswith('[') and transcription.endswith(']')) and \
               not (transcription.startswith('/') and transcription.endswith('/')):
                transcription = f'[{transcription}]'
            return transcription
        return ''

    def save(self, commit=True):
        word = super().save(commit=False)
        if self.user and not word.pk:
            word.user = self.user
        if commit:
            word.save()
        return word


class WordSearchForm(forms.Form):
    """Форма для поиска и фильтрации слов"""

    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по английскому слову или переводу...',
        }),
        label="Поиск"
    )

    category = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Категория"
    )

    difficulty_level = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Уровень сложности"
    )

    STATUS_CHOICES = [
        ('', 'Все слова'),
        ('learned', 'Выученные'),
        ('not_learned', 'Не выученные'),
        ('needs_practice', 'Требуют практики'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Статус изучения"
    )

    SORT_CHOICES = [
        ('-created_at', 'Сначала новые'),
        ('created_at', 'Сначала старые'),
        ('english_word', 'По алфавиту (англ.)'),
        ('-times_practiced', 'По количеству повторений'),
        ('-last_practiced', 'По дате изучения'),
    ]

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Сортировка"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Динамические категории пользователя
        if user:
            categories = user.words.values_list('category', flat=True).distinct().order_by('category')
            category_choices = [('', 'Все категории')] + [(cat, cat.title()) for cat in categories if cat]
            self.fields['category'].choices = category_choices
        else:
            self.fields['category'].choices = [('', 'Все категории')]
        
        # Уровни сложности из модели
        self.fields['difficulty_level'].choices = [('', 'Все уровни')] + list(Word.DIFFICULTY_CHOICES)


class StudyConfigForm(forms.Form):
    """Форма настройки сессии изучения слов"""

    STUDY_MODES = [
        ('flashcards', 'Карточки (показать перевод)'),
        ('translation', 'Перевод с английского'),
        ('reverse_translation', 'Перевод на английский'),
        ('mixed', 'Смешанный режим'),
    ]

    mode = forms.ChoiceField(
        choices=STUDY_MODES,
        initial='flashcards',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label="Режим изучения"
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
        label="Количество слов"
    )

    categories = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Категории для изучения"
    )

    difficulty_levels = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Уровни сложности"
    )

    WORD_SELECTION_CHOICES = [
        ('random', 'Случайные слова'),
        ('least_practiced', 'Наименее изучаемые'),
        ('needs_practice', 'Требующие практики'),
        ('newest', 'Новые слова'),
        ('oldest', 'Старые слова'),
    ]

    selection_method = forms.ChoiceField(
        choices=WORD_SELECTION_CHOICES,
        initial='needs_practice',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Метод выбора слов"
    )

    include_learned = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Включить выученные слова"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if user:
            # Динамические категории пользователя
            categories = user.words.values_list('category', flat=True).distinct().order_by('category')
            category_choices = [(cat, cat.title()) for cat in categories if cat]
            self.fields['categories'].choices = category_choices
        else:
            self.fields['categories'].choices = []
        
        # Уровни сложности из модели
        self.fields['difficulty_levels'].choices = list(Word.DIFFICULTY_CHOICES)


class BulkWordImportForm(forms.Form):
    """Форма для массового импорта слов"""

    words_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Введите слова в формате:\nword1 - перевод1\nword2 - перевод2\n...'
        }),
        label="Список слов",
        help_text="Формат: 'английское_слово - русский_перевод' (каждое слово с новой строки)"
    )

    default_category = forms.CharField(
        max_length=50,
        initial='общие',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Бизнес, IT, Путешествия'
        }),
        label="Категория по умолчанию"
    )

    default_difficulty = forms.ChoiceField(
        choices=[],
        initial='beginner',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Уровень сложности по умолчанию"
    )

    skip_duplicates = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Пропускать дубликаты"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Уровни сложности из модели
        self.fields['default_difficulty'].choices = list(Word.DIFFICULTY_CHOICES)

    def clean_words_text(self):
        """Валидация текста со словами"""
        words_text = self.cleaned_data.get('words_text', '').strip()
        if not words_text:
            raise ValidationError("Список слов не может быть пустым.")

        lines = [line.strip() for line in words_text.split('\n') if line.strip()]
        if not lines:
            raise ValidationError("Не найдено ни одного слова для импорта.")

        parsed_words = []
        errors = []

        for i, line in enumerate(lines, 1):
            if ' - ' not in line:
                errors.append(f"Строка {i}: неверный формат. Используйте 'слово - перевод'")
                continue

            parts = line.split(' - ', 1)
            if len(parts) != 2:
                errors.append(f"Строка {i}: неверный формат")
                continue

            english_word = parts[0].strip()
            russian_translation = parts[1].strip()

            if not english_word or not russian_translation:
                errors.append(f"Строка {i}: пустое слово или перевод")
                continue

            if not re.match(r"^[a-zA-Z\s\-']+$", english_word):
                errors.append(f"Строка {i}: '{english_word}' содержит недопустимые символы")
                continue

            parsed_words.append({
                'english_word': english_word.lower(),
                'russian_translation': russian_translation
            })

        if errors:
            raise ValidationError("Ошибки в формате:\n" + "\n".join(errors))

        if not parsed_words:
            raise ValidationError("Не найдено корректных слов для импорта.")

        return parsed_words


class WordQuizForm(forms.Form):
    """Форма для квиза по словам"""

    answer = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ответ...',
            'autocomplete': 'off'
        }),
        label="Ваш ответ"
    )

    def __init__(self, *args, word=None, mode='translation', **kwargs):
        super().__init__(*args, **kwargs)
        self.word = word
        self.mode = mode

        if mode == 'translation':
            self.fields['answer'].widget.attrs['placeholder'] = 'Введите перевод на русский...'
        elif mode == 'reverse_translation':
            self.fields['answer'].widget.attrs['placeholder'] = 'Введите перевод на английский...'

    def clean_answer(self):
        """Валидация ответа"""
        answer = self.cleaned_data.get('answer', '').strip()
        if not answer:
            raise ValidationError("Ответ не может быть пустым.")
        return answer

    def is_correct(self):
        """Проверка правильности ответа"""
        if not self.word or not self.is_valid():
            return False

        user_answer = self.cleaned_data['answer'].lower().strip()

        if self.mode == 'translation':
            # Проверяем перевод на русский
            correct_answers = [
                self.word.russian_translation.lower().strip()
            ]

            # Добавляем варианты через запятую или точку с запятой
            if ',' in self.word.russian_translation:
                correct_answers.extend([
                    ans.strip().lower()
                    for ans in self.word.russian_translation.split(',')
                ])

            if ';' in self.word.russian_translation:
                correct_answers.extend([
                    ans.strip().lower()
                    for ans in self.word.russian_translation.split(';')
                ])

        elif self.mode == 'reverse_translation':
            # Проверяем перевод на английский
            correct_answers = [
                self.word.english_word.lower().strip()
            ]

        # Проверяем точное соответствие или частичное (для длинных фраз)
        for correct in correct_answers:
            if user_answer == correct or (len(user_answer) > 5 and user_answer in correct):
                return True

        return False


# Форма для быстрого добавления слова в существующую категорию
class QuickWordForm(forms.ModelForm):
    """Быстрая форма добавления слова"""

    class Meta:
        model = Word
        fields = ['english_word', 'russian_translation', 'transcription', 'definition', 'example_sentence']
        widgets = {
            'english_word': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите английское слово',
                'required': True,
                'autofocus': True
            }),
            'russian_translation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите русский перевод',
                'required': True
            }),
            'transcription': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '[ˈwɜːrd] - транскрипция (опционально)'
            }),
            'definition': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Определение (опционально)',
                'rows': 2
            }),
            'example_sentence': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Пример предложения (опционально)',
                'rows': 2
            }),
        }

    def __init__(self, *args, user=None, category=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.category = category
        
        # Устанавливаем подписи
        self.fields['english_word'].label = "Английское слово"
        self.fields['russian_translation'].label = "Русский перевод"
        self.fields['transcription'].label = "Транскрипция"
        self.fields['definition'].label = "Определение"
        self.fields['example_sentence'].label = "Пример предложения"

    def clean_english_word(self):
        """Валидация английского слова"""
        english_word = self.cleaned_data.get('english_word', '').strip().lower()
        
        if not english_word:
            raise ValidationError("Английское слово не может быть пустым.")
        
        if not re.match(r"^[a-zA-Z\s\-']+$", english_word):
            raise ValidationError("Английское слово должно содержать только английские буквы, пробелы, дефисы и апострофы.")
        
        if len(english_word) < 2:
            raise ValidationError("Английское слово должно содержать минимум 2 символа.")
        
        # Проверяем уникальность для данного пользователя
        if self.user:
            existing_word = Word.objects.filter(
                user=self.user,
                english_word__iexact=english_word
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_word.exists():
                raise ValidationError("Это слово уже есть в вашем словаре.")
        
        return english_word

    def clean_russian_translation(self):
        """Валидация русского перевода"""
        russian_translation = self.cleaned_data.get('russian_translation', '').strip()
        
        if not russian_translation:
            raise ValidationError("Русский перевод не может быть пустым.")
        
        if len(russian_translation) < 1:
            raise ValidationError("Русский перевод должен содержать минимум 1 символ.")
        
        return russian_translation

    def clean_transcription(self):
        """Валидация транскрипции"""
        transcription = self.cleaned_data.get('transcription', '')
        if transcription:
            transcription = transcription.strip()
            if transcription and not (transcription.startswith('[') and transcription.endswith(']')) and \
               not (transcription.startswith('/') and transcription.endswith('/')):
                transcription = f'[{transcription}]'
        return transcription if transcription else None

    def save(self, commit=True):
        """Переопределяем сохранение"""
        word = super().save(commit=False)
        if self.user:
            word.user = self.user
        if self.category:
            word.category = self.category
        word.difficulty_level = 'beginner'  # По умолчанию
        
        if commit:
            word.save()
        return word


# Форма выбора существующей категории
class CategorySelectForm(forms.Form):
    """Форма для выбора существующей категории"""
    
    category = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Выберите категорию"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Получаем уникальные категории пользователя
            categories = user.words.values_list('category', flat=True).distinct().order_by('category')
            category_choices = [(cat, cat.title()) for cat in categories if cat]
            
            if category_choices:
                self.fields['category'].choices = category_choices
            else:
                self.fields['category'].choices = [('', 'У вас пока нет категорий')]


# Форма создания новой категории
class NewCategoryForm(forms.Form):
    """Форма для создания новой категории"""
    
    category_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Бизнес, Путешествия, IT...',
            'autofocus': True
        }),
        label="Название новой категории"
    )

    def clean_category_name(self):
        """Валидация названия категории"""
        category_name = self.cleaned_data.get('category_name', '').strip().lower()
        
        if not category_name:
            raise ValidationError("Название категории не может быть пустым.")
        
        if len(category_name) < 2:
            raise ValidationError("Название категории должно содержать минимум 2 символа.")
        
        if len(category_name) > 50:
            raise ValidationError("Название категории не должно превышать 50 символов.")
        
        return category_name

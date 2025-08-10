# forms.py - Формы для приложения словаря

from django import forms
from django.core.exceptions import ValidationError
from .models import Word, StudySession
import re


class WordForm(forms.ModelForm):
    """
    Форма для добавления и редактирования слов
    """
    
    class Meta:
        model = Word
        fields = [
            'english_word', 
            'russian_translation', 
            'transcription', 
            'definition', 
            'example_sentence',
            'category', 
            'difficulty_level'
        ]
        widgets = {
            'english_word': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите английское слово',
                'required': True
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
                'placeholder': 'Определение слова на английском языке (опционально)',
                'rows': 3
            }),
            'example_sentence': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Пример предложения с этим словом (опционально)',
                'rows': 2
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Устанавливаем подписи для полей
        self.fields['english_word'].label = "Английское слово"
        self.fields['russian_translation'].label = "Русский перевод"
        self.fields['transcription'].label = "Транскрипция"
        self.fields['definition'].label = "Определение на английском"
        self.fields['example_sentence'].label = "Пример предложения"
        self.fields['category'].label = "Категория"
        self.fields['difficulty_level'].label = "Уровень сложности"

    def clean_english_word(self):
        """Валидация английского слова"""
        english_word = self.cleaned_data.get('english_word', '').strip().lower()
        
        if not english_word:
            raise ValidationError("Английское слово не может быть пустым.")
        
        # Проверяем, что слово содержит только английские буквы, дефисы и апострофы
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
        transcription = self.cleaned_data.get('transcription')
        if transcription is None:
            return ''  # либо, если поле обязательное, выбросить ошибку валидации
        transcription = transcription.strip()
        # дополнительные проверки или преобразования
        return transcription


    def save(self, commit=True):
        """Переопределяем сохранение для установки пользователя"""
        word = super().save(commit=False)
        if self.user:
            word.user = self.user
        if commit:
            word.save()
        return word


class WordSearchForm(forms.Form):
    """
    Форма для поиска и фильтрации слов
    """
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
        choices=[('', 'Все категории')] + Word.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Категория"
    )
    
    difficulty_level = forms.ChoiceField(
        choices=[('', 'Все уровни')] + Word.DIFFICULTY_CHOICES,
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


class StudyConfigForm(forms.Form):
    """
    Форма настройки сессии изучения слов
    """
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
        choices=Word.CATEGORY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Категории для изучения"
    )
    
    difficulty_levels = forms.MultipleChoiceField(
        choices=Word.DIFFICULTY_CHOICES,
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


class BulkWordImportForm(forms.Form):
    """
    Форма для массового импорта слов
    """
    words_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Введите слова в формате:\nword1 - перевод1\nword2 - перевод2\n...'
        }),
        label="Список слов",
        help_text="Формат: 'английское_слово - русский_перевод' (каждое слово с новой строки)"
    )
    
    default_category = forms.ChoiceField(
        choices=Word.CATEGORY_CHOICES,
        initial='general',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Категория по умолчанию"
    )
    
    default_difficulty = forms.ChoiceField(
        choices=Word.DIFFICULTY_CHOICES,
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
    """
    Форма для квиза по словам
    """
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
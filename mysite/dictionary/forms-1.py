# dictionary/forms.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from django import forms
from django.core.exceptions import ValidationError
from .models import Word, StudySession, Category
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
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # ИСПРАВЛЕНО: Получаем категории пользователя для выбора
        if self.user:
            categories = Category.objects.filter(created_by=self.user).order_by('name')
            self.fields['category'].queryset = categories
            if not categories.exists():
                # Если категорий нет, создаем выбор "создать категорию"
                self.fields['category'].widget = forms.HiddenInput()
        else:
            self.fields['category'].queryset = Category.objects.none()

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
            if not (transcription.startswith('[') and transcription.endswith(']')) and \
               not (transcription.startswith('/') and transcription.endswith('/')):
                transcription = f'[{transcription}]'
            return transcription
        return ''

    def clean(self):
        """ИСПРАВЛЕНО: Проверяем уникальность только в той же категории"""
        cleaned_data = super().clean()
        english_word = cleaned_data.get('english_word')
        category = cleaned_data.get('category')

        if self.user and english_word and category:
            # ИСПРАВЛЕНО: Проверяем через ForeignKey
            existing_query = Word.objects.filter(
                user=self.user,
                english_word__iexact=english_word,
                category=category  # Убрали __iexact, так как category теперь ForeignKey
            )

            # Исключаем текущий объект при редактировании
            if self.instance and self.instance.pk:
                existing_query = existing_query.exclude(pk=self.instance.pk)

            if existing_query.exists():
                raise ValidationError({
                    'english_word': f'Слово "{english_word}" уже существует в категории "{category.name}". '
                                  'Вы можете добавить это же слово в другую категорию.'
                })

        return cleaned_data

    def save(self, commit=True):
        word = super().save(commit=False)
        if self.user and not word.pk:
            word.user = self.user
        if commit:
            word.save()
        return word

class QuickWordForm(forms.ModelForm):
    """Быстрая форма добавления слова в определенную категорию"""

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
        self.category = category  # Теперь это объект Category, а не строка

        self.fields['english_word'].label = "Английское слово"
        self.fields['russian_translation'].label = "Русский перевод"
        self.fields['transcription'].label = "Транскрипция"
        self.fields['definition'].label = "Определение"
        self.fields['example_sentence'].label = "Пример предложения"

    def clean_english_word(self):
        english_word = self.cleaned_data.get('english_word', '').strip()
        if not english_word:
            raise ValidationError("Английское слово не может быть пустым.")
        if not re.match(r"^[a-zA-Z\s\-']+$", english_word):
            raise ValidationError("Английское слово должно содержать только английские буквы, пробелы, дефисы и апострофы.")
        if len(english_word) < 2:
            raise ValidationError("Английское слово должно содержать минимум 2 символа.")

        # ИСПРАВЛЕНО: Проверяем дубликат только в той же категории
        if self.user and self.category:
            existing_word = Word.objects.filter(
                user=self.user,
                english_word__iexact=english_word,
                category=self.category  # Убрали __iexact, так как category теперь ForeignKey объект
            )

            # Исключаем текущий объект при редактировании
            if self.instance and self.instance.pk:
                existing_word = existing_word.exclude(pk=self.instance.pk)

            if existing_word.exists():
                raise ValidationError(f'Слово "{english_word}" уже существует в категории "{self.category.name}". '
                                    'Это же слово можно добавить в другую категорию.')

        return english_word.lower()

    def clean_russian_translation(self):
        russian_translation = self.cleaned_data.get('russian_translation', '').strip()
        if not russian_translation:
            raise ValidationError("Русский перевод не может быть пустым.")
        if len(russian_translation) < 1:
            raise ValidationError("Русский перевод должен содержать минимум 1 символ.")
        return russian_translation

    def clean_transcription(self):
        transcription = self.cleaned_data.get('transcription', '')
        if transcription:
            transcription = transcription.strip()
            if transcription and not (transcription.startswith('[') and transcription.endswith(']')) and \
               not (transcription.startswith('/') and transcription.endswith('/')):
                transcription = f'[{transcription}]'
            return transcription if transcription else None

    def save(self, commit=True):
        word = super().save(commit=False)
        if self.user:
            word.user = self.user
        if self.category:
            word.category = self.category  # Теперь присваиваем объект Category
        word.difficulty_level = 'beginner'  # По умолчанию
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

        # ИСПРАВЛЕНО: Динамические категории пользователя
        if user:
            categories = Category.objects.filter(created_by=user).order_by('name')
            category_choices = [('', 'Все категории')] + [(cat.name, cat.name.title()) for cat in categories]
            self.fields['category'].choices = category_choices
        else:
            self.fields['category'].choices = [('', 'Все категории')]

        # Уровни сложности из модели
        self.fields['difficulty_level'].choices = [('', 'Все уровни')] + list(Word.DIFFICULTY_CHOICES)

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
            # ИСПРАВЛЕНО: Получаем категории через модель Category
            categories = Category.objects.filter(created_by=user).order_by('name')
            category_choices = [(cat.id, cat.name.title()) for cat in categories]

            if category_choices:
                self.fields['category'].choices = category_choices
            else:
                self.fields['category'].choices = [('', 'У вас пока нет категорий')]

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
        category_name = self.cleaned_data.get('category_name', '').strip()
        if not category_name:
            raise ValidationError("Название категории не может быть пустым.")
        if len(category_name) < 2:
            raise ValidationError("Название категории должно содержать минимум 2 символа.")
        if len(category_name) > 50:
            raise ValidationError("Название категории не должно превышать 50 символов.")
        return category_name

# Заглушки для остальных форм
class StudyConfigForm(forms.Form):
    """Заглушка для формы настройки изучения"""
    pass

class BulkWordImportForm(forms.Form):
    """Заглушка для формы импорта"""
    pass

class WordQuizForm(forms.Form):
    """Заглушка для формы квиза"""
    pass

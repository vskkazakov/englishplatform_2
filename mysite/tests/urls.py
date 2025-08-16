# tests/urls.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from django.urls import path
from . import views

app_name = 'tests'  # ← ИСПРАВЛЕНО: было 'test', стало 'tests'

urlpatterns = [
    # Главная страница тестов
    path('', views.index, name='index'),
    
    # Выбор категорий для тестирования
    path('categories/', views.categories, name='categories'),
    
    # Начало теста
    path('start/', views.start, name='start'),
    
    # Вопросы теста
    path('question/', views.question, name='question'),
    
    # Результаты теста
    path('results/', views.results, name='results'),
    
    # История тестов
    path('history/', views.history, name='history'),
]

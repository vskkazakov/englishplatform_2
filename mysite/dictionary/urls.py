from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    # Главная страница словаря
    path('', views.index, name='index'),
    
    # Работа со словами (старые маршруты)
    path('add/', views.add_word, name='add_word'),
    path('words/', views.view_words, name='view_words'),
    path('word/<int:word_id>/', views.word_detail, name='word_detail'),
    path('word/<int:word_id>/edit/', views.edit_word, name='edit_word'),
    path('word/<int:word_id>/delete/', views.delete_word, name='delete_word'),
    path('word/<int:word_id>/toggle-learned/', views.toggle_learned, name='toggle_learned'),
    
    # НОВЫЕ маршруты для работы с категориями
    path('categories/select/', views.select_category, name='select_category'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<str:category_name>/add/', views.add_to_category, name='add_to_category'),
    
    # Изучение слов
    path('study/setup/', views.study_setup, name='study_setup'),
    path('study/session/', views.study_session, name='study_session'),
    path('study/results/', views.study_results, name='study_results'),
    
    # Дополнительные функции
    path('import/', views.bulk_import, name='bulk_import'),
    path('statistics/', views.statistics, name='statistics'),
]

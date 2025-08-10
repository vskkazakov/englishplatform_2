from django.urls import path
from . import views

app_name = 'authen'

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('test-db/', views.test_db_connection, name='test_db'),
    path('resend-code/', views.resend_code, name='resend_code'),  # Добавляем эту строку
]
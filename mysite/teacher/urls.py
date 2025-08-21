from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.index, name='index'),
    path('my-teachers/', views.my_teachers, name='my_teachers'),
    path('send-request/<int:teacher_id>/', views.send_request, name='send_request'),
    path('cancel-request/<int:request_id>/', views.cancel_request, name='cancel_request'),
    path('respond-request/<int:request_id>/', views.respond_to_request, name='respond_to_request'),
    path('view-homework/<int:homework_id>/', views.view_homework, name='view_homework'),
    path('complete-homework/<int:homework_id>/', views.complete_homework, name='complete_homework'),
    path('respond-category-request/<int:request_id>/', views.respond_to_category_request, name='respond_to_category_request')
]

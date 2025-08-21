from django.urls import path
from . import views
from django.conf.urls import include

app_name = 'students'

urlpatterns = [
    path('', views.index, name='index'),
    path('my-students/', views.my_students, name='my_students'),
    path('send-request/<int:student_id>/', views.send_request, name='send_request'),  # ИСПРАВЛЕНО
    path('cancel-request/<int:request_id>/', views.cancel_request, name='cancel_request'),  # ИСПРАВЛЕНО
    path('respond-request/<int:request_id>/', views.respond_to_request, name='respond_to_request'),  # ИСПРАВЛЕНО
    path('create-homework/<int:student_id>/', views.create_homework, name='create_homework'),  # ИСПРАВЛЕНО
    path('view-homework/<int:homework_id>/', views.view_homework, name='view_homework'),  # ИСПРАВЛЕНО
    path('get-students-list/', views.get_students_list, name='get_students_list'),
    path('test/', views.test_view, name='test'),
    path('share-category/<int:student_id>/', views.share_category, name='share_category'),
    path('get-teacher-categories/', views.get_teacher_categories, name='get_teacher_categories'),
]

from django.urls import path
from . import views
from django.conf.urls import include

app_name = 'act_static'

urlpatterns = [
    path('', views.index, name='index'),
]
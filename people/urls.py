from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('', views.people_directory, name='directory'),
    path('<int:pk>/', views.person_detail, name='detail'),
]
from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/logout/', views.custom_logout, name='logout'),
]
from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.overall_search, name='overall'),
    path('people/', views.people_search, name='people'),
    path('locations/', views.locations_search, name='locations'),
    path('years/', views.years_search, name='years'),
    path('tags/', views.tags_search, name='tags'),
    
    # API endpoints
    path('api/people/', views.people_autocomplete, name='people_autocomplete'),
    path('api/locations/', views.locations_autocomplete, name='locations_autocomplete'),
]
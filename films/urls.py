from django.urls import path
from . import views

app_name = 'films'

urlpatterns = [
    path('', views.film_catalog, name='catalog'),
    path('<str:file_id>/', views.film_detail, name='detail'),
    path('<str:file_id>/chapters/<int:chapter_id>/metadata/', views.chapter_metadata_api, name='chapter_metadata_api'),
    path('<str:file_id>/thumbnail/', views.animated_thumbnail_data, name='thumbnail_data'),
    
    # API endpoints for metadata editing
    path('api/people-autocomplete/', views.people_autocomplete, name='people_autocomplete'),
    path('api/locations-autocomplete/', views.locations_autocomplete, name='locations_autocomplete'),
    path('api/tags-autocomplete/', views.tags_autocomplete, name='tags_autocomplete'),
    path('api/film/<str:file_id>/metadata/', views.update_film_metadata, name='update_film_metadata'),
    path('api/film/<str:file_id>/years/', views.update_film_years, name='update_film_years'),
    path('api/film/<str:file_id>/aggregated-metadata/', views.get_film_aggregated_metadata, name='get_film_aggregated_metadata'),
    path('api/chapter/<int:chapter_id>/metadata/', views.get_chapter_metadata, name='get_chapter_metadata'),
    path('api/chapter/<int:chapter_id>/update/', views.update_chapter_metadata, name='update_chapter_metadata'),
    path('api/chapter/<int:chapter_id>/notes/', views.update_chapter_notes, name='update_chapter_notes'),
]
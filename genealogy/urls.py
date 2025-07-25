from django.urls import path
from . import views

app_name = 'genealogy'

urlpatterns = [
    # Main genealogy pages
    path('', views.GenealogyHomeView.as_view(), name='home'),
    path('tree/', views.GenealogyHomeView.as_view(), name='tree_home'),
    path('tree/<int:pk>/', views.FamilyTreeView.as_view(), name='tree'),
    
    # Person relationship management
    path('person/<int:pk>/edit/', views.PersonRelationshipEditView.as_view(), name='person_edit'),
    path('person/<int:pk>/biography/', views.PersonBiographyView.as_view(), name='biography'),
    path('person/<int:pk>/biography/edit/', views.PersonBiographyEditView.as_view(), name='biography_edit'),
    
    # API endpoints
    path('api/tree/<int:pk>/', views.FamilyTreeAPIView.as_view(), name='api_tree'),
    path('api/search-people/', views.search_people_api, name='api_search_people'),
]
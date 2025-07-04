from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
from main.models import Location, Film


def locations_list(request):
    """Browse all locations in the database"""
    locations = Location.objects.annotate(
        film_count=Count('film')
    ).filter(film_count__gt=0).order_by('name')
    
    # Pagination
    paginator = Paginator(locations, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'locations': page_obj,
    }
    return render(request, 'locations/list.html', context)


def location_detail(request, pk):
    """Individual location page"""
    location = get_object_or_404(Location, pk=pk)
    films = Film.objects.filter(locations=location).exclude(youtube_id__startswith='placeholder_').prefetch_related('people', 'locations', 'tags')
    
    # Pagination
    paginator = Paginator(films, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'location': location,
        'films': page_obj,
        'page_obj': page_obj,
        'total_films': films.count(),
    }
    return render(request, 'locations/detail.html', context)

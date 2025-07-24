from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from main.models import Location, Film


def locations_list(request):
    """Browse all locations in the database"""
    # Get locations that have any film associations (direct or via chapters)
    locations = Location.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct().order_by('name')
    
    # Calculate accurate film counts for each location
    for location in locations:
        films = Film.objects.filter(
            Q(locations=location) | Q(chapters__locations=location)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        location.film_count = films.count()
    
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
    # Get films where location appears directly or in chapters
    from django.db.models import Q
    films = Film.objects.filter(
        Q(locations=location) | Q(chapters__locations=location)
    ).exclude(youtube_id__startswith='placeholder_').distinct().prefetch_related('people', 'locations', 'tags')
    
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

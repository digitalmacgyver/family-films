from django.shortcuts import render
from django.db.models import Q, Count
from django.core.paginator import Paginator
# from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.http import JsonResponse
from main.models import Film, Person, Location, Tag, Chapter
import json


def add_aggregated_metadata_to_films(films):
    """Add aggregated metadata (people, locations, tags, years) to each film"""
    for film in films:
        # Aggregate people
        film.all_people = Person.objects.filter(
            Q(filmpeople__film=film) | Q(chapterpeople__chapter__film=film)
        ).distinct().order_by('last_name', 'first_name')
        
        # Aggregate locations
        film.all_locations = Location.objects.filter(
            Q(filmlocations__film=film) | Q(chapterlocations__chapter__film=film)
        ).distinct().order_by('name')
        
        # Aggregate tags
        film.all_tags = Tag.objects.filter(
            Q(filmtags__film=film) | Q(chaptertags__chapter__film=film)
        ).distinct().order_by('tag')
        
        # Aggregate years
        all_years_set = set()
        if film.years:
            all_years_set.update(film.get_year_list())
        for chapter in film.chapters.all():
            if chapter.years:
                chapter_years = [int(year.strip()) for year in chapter.years.replace(',', ' ').split() if year.strip().isdigit()]
                all_years_set.update(chapter_years)
        film.all_years = sorted(all_years_set)
    return films


def overall_search(request):
    """Overall search across all content"""
    query = request.GET.get('q', '').strip()
    is_ajax = request.GET.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not query:
        template = 'search/overall_ajax.html' if is_ajax else 'search/overall.html'
        return render(request, template, {'query': query})
    
    # Search films - SQLite compatible
    films = Film.objects.exclude(youtube_id__startswith='placeholder_').filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(summary__icontains=query)
    ).distinct()
    
    # Search chapters - SQLite compatible
    chapters = Chapter.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    ).exclude(film__youtube_id__startswith='placeholder_').select_related('film').distinct()
    
    # Search people
    people = Person.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).annotate(film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True))
    
    # Search locations
    locations = Location.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ).annotate(film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True))
    
    # Search tags
    tags = Tag.objects.filter(tag__icontains=query).annotate(film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True))
    
    # Add aggregated metadata to films
    films_list = list(films[:10])
    add_aggregated_metadata_to_films(films_list)
    
    context = {
        'query': query,
        'films': films_list,
        'chapters': chapters[:10],
        'people': people[:10],
        'locations': locations[:10],
        'tags': tags[:10],
        'total_results': {
            'films': films.count(),
            'chapters': chapters.count(),
            'people': people.count(),
            'locations': locations.count(),
            'tags': tags.count(),
        }
    }
    
    template = 'search/overall_ajax.html' if is_ajax else 'search/overall.html'
    return render(request, template, context)


def people_search(request):
    """Top-level people search page"""
    selected_people = request.GET.getlist('people')
    search_query = request.GET.get('q', '').strip()
    
    # Get all people for autocomplete
    people_qs = Person.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0)
    
    if search_query:
        people_qs = people_qs.filter(
            Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query)
        )
    
    people = people_qs.order_by('last_name', 'first_name')
    
    # Get films featuring selected people (includes chapter metadata)
    films = None
    page_obj = None
    if selected_people:
        films = Film.objects.filter(
            Q(people__id__in=selected_people) |
            Q(chapters__people__id__in=selected_people)
        ).exclude(youtube_id__startswith='placeholder_').distinct().prefetch_related('people', 'locations', 'tags')
        
        # Pagination
        paginator = Paginator(films, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add aggregated metadata to films
        films = list(page_obj)
        add_aggregated_metadata_to_films(films)
    
    context = {
        'people': people,
        'selected_people': selected_people,
        'search_query': search_query,
        'films': films,
        'page_obj': page_obj,
    }
    return render(request, 'search/people.html', context)


def locations_search(request):
    """Top-level locations search page"""
    selected_locations = request.GET.getlist('locations')
    search_query = request.GET.get('q', '').strip()
    
    # Get all locations for search
    locations_qs = Location.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0)
    
    if search_query:
        locations_qs = locations_qs.filter(
            Q(name__icontains=search_query) | 
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query)
        )
    
    locations = locations_qs.order_by('name')
    
    # Get films at selected locations (includes chapter metadata)
    films = None
    page_obj = None
    if selected_locations:
        films = Film.objects.filter(
            Q(locations__id__in=selected_locations) |
            Q(chapters__locations__id__in=selected_locations)
        ).exclude(youtube_id__startswith='placeholder_').distinct().prefetch_related('people', 'locations', 'tags')
        
        # Pagination
        paginator = Paginator(films, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add aggregated metadata to films
        films = list(page_obj)
        add_aggregated_metadata_to_films(films)
    
    context = {
        'locations': locations,
        'selected_locations': selected_locations,
        'search_query': search_query,
        'films': films,
        'page_obj': page_obj,
    }
    return render(request, 'search/locations.html', context)


def years_search(request):
    """Top-level years/timeline search page"""
    selected_years = request.GET.getlist('years')
    decade = request.GET.get('decade')
    
    # Get all years from films
    all_years = set()
    year_counts = {}
    
    for film in Film.objects.exclude(youtube_id__startswith='placeholder_'):
        years = film.get_year_list()
        all_years.update(years)
        for year in years:
            year_counts[year] = year_counts.get(year, 0) + 1
    
    all_years = sorted(all_years)
    
    # Group by decades
    decades = {}
    for year in all_years:
        decade_start = (year // 10) * 10
        if decade_start not in decades:
            decades[decade_start] = []
        decades[decade_start].append({
            'year': year,
            'count': year_counts[year]
        })
    
    # Get films for selected years
    films = None
    if selected_years:
        # Filter films that contain any of the selected years in film or chapters
        film_filters = Q()
        chapter_filters = Q()
        for year in selected_years:
            film_filters |= Q(years__icontains=year)
            chapter_filters |= Q(chapters__years__icontains=year)
        
        films = Film.objects.filter(film_filters | chapter_filters).exclude(youtube_id__startswith='placeholder_').distinct().prefetch_related('people', 'locations', 'tags', 'chapters')
        
        # Pagination
        paginator = Paginator(films, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add aggregated metadata to films
        films = list(page_obj)
        add_aggregated_metadata_to_films(films)
    
    context = {
        'decades': decades,
        'selected_years': selected_years,
        'films': films,
        'page_obj': page_obj if films else None,
        'year_counts': year_counts,
    }
    return render(request, 'search/years.html', context)


def tags_search(request):
    """Top-level tags search page"""
    selected_tags = request.GET.getlist('tags')
    category_filter = request.GET.get('category')
    
    # Get all tags grouped by category
    tags_qs = Tag.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0)
    
    if category_filter:
        tags_qs = tags_qs.filter(category=category_filter)
    
    tags = tags_qs.order_by('category', 'tag')
    
    # Group tags by category
    tags_by_category = {}
    for tag in tags:
        if tag.category not in tags_by_category:
            tags_by_category[tag.category] = []
        tags_by_category[tag.category].append(tag)
    
    # Get films with selected tags (includes chapter metadata)
    films = None
    page_obj = None
    if selected_tags:
        films = Film.objects.filter(
            Q(tags__tag__in=selected_tags) |
            Q(chapters__tags__tag__in=selected_tags)
        ).exclude(youtube_id__startswith='placeholder_').distinct().prefetch_related('people', 'locations', 'tags')
        
        # Pagination
        paginator = Paginator(films, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Add aggregated metadata to films
        films = list(page_obj)
        add_aggregated_metadata_to_films(films)
    
    context = {
        'tags_by_category': tags_by_category,
        'selected_tags': selected_tags,
        'category_filter': category_filter,
        'films': films,
        'page_obj': page_obj,
        'tag_categories': Tag.CATEGORY_CHOICES,
    }
    return render(request, 'search/tags.html', context)


# API endpoints for autocomplete
def people_autocomplete(request):
    """API endpoint for people autocomplete"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    people = Person.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).annotate(film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)).filter(film_count__gt=0)[:10]
    
    results = [
        {
            'id': person.id,
            'name': person.full_name(),
            'film_count': person.film_count
        }
        for person in people
    ]
    
    return JsonResponse({'results': results})


def locations_autocomplete(request):
    """API endpoint for locations autocomplete"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    locations = Location.objects.filter(
        Q(name__icontains=query) | Q(city__icontains=query)
    ).annotate(film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)).filter(film_count__gt=0)[:10]
    
    results = [
        {
            'id': location.id,
            'name': location.name,
            'film_count': location.film_count
        }
        for location in locations
    ]
    
    return JsonResponse({'results': results})

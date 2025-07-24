from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from main.models import Person, Film


def people_directory(request):
    """Browse all people in the database"""
    # Get sort preference
    sort_by = request.GET.get('sort', 'last_name')  # Default to last name
    
    # Get people that have any film associations (direct or via chapters)
    people = Person.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct()
    
    # Calculate accurate film counts for each person to avoid double-counting
    for person in people:
        films = Film.objects.filter(
            Q(people=person) | Q(chapters__people=person)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        person.film_count = films.count()
    
    # Filter out people with no films after excluding placeholders
    people = [person for person in people if person.film_count > 0]
    
    if sort_by == 'first_name':
        # Sort by first name
        people.sort(key=lambda p: (p.first_name.lower(), p.last_name.lower()))
    else:
        # Default: Sort by last name (empty last names first), then first name
        # This puts people without last names at the beginning under "#"
        people.sort(key=lambda p: (
            1 if p.last_name.strip() else 0,  # Empty last names first
            p.last_name.lower(), 
            p.first_name.lower()
        ))
    
    # Pagination
    paginator = Paginator(people, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'people': page_obj,
        'current_sort': sort_by,
    }
    return render(request, 'people/directory.html', context)


def person_detail(request, pk):
    """Individual person page"""
    person = get_object_or_404(Person, pk=pk)
    # Get films where person appears directly or in chapters
    from django.db.models import Q
    films = Film.objects.filter(
        Q(people=person) | Q(chapters__people=person)
    ).exclude(youtube_id__startswith='placeholder_').distinct().prefetch_related('people', 'locations', 'tags')
    
    # Pagination
    paginator = Paginator(films, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'person': person,
        'films': page_obj,
        'page_obj': page_obj,
        'total_films': films.count(),
    }
    return render(request, 'people/detail.html', context)

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count
from main.models import Person, Film


def people_directory(request):
    """Browse all people in the database"""
    # Get sort preference
    sort_by = request.GET.get('sort', 'last_name')  # Default to last name
    
    people = Person.objects.annotate(
        film_count=Count('film')
    ).filter(film_count__gt=0)
    
    if sort_by == 'first_name':
        # Sort by first name
        people = people.order_by('first_name', 'last_name')
    else:
        # Default: Sort by last name (empty last names first), then first name
        # This puts people without last names at the beginning under "#"
        people = people.extra(
            select={
                'has_last_name': "CASE WHEN last_name = '' OR last_name IS NULL THEN 0 ELSE 1 END"
            }
        ).order_by('has_last_name', 'last_name', 'first_name')
    
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
    films = Film.objects.filter(people=person).exclude(youtube_id__startswith='placeholder_').prefetch_related('people', 'locations', 'tags')
    
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

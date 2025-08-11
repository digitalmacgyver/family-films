from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
# from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from main.models import Film, Chapter, Person, Location, Tag


def film_catalog(request):
    """Film catalog page with animated thumbnails and filtering"""
    # Show all films including placeholders (Batch D imports need manual YouTube mapping)
    films = Film.objects.select_related().prefetch_related(
        'people', 'locations', 'tags', 'chapters'
    )
    
    # Search functionality - SQLite compatible - includes chapter content
    search_query = request.GET.get('q', '').strip()
    if search_query:
        films = films.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(chapters__title__icontains=search_query) |
            Q(chapters__description__icontains=search_query)
        ).distinct()
    
    # Filtering
    year_filter = request.GET.get('year')
    if year_filter:
        films = films.filter(years__icontains=year_filter)
    
    person_filter = request.GET.get('person')
    if person_filter:
        # Filter films that have the person in film metadata OR chapter metadata
        films = films.filter(
            Q(people__id=person_filter) |
            Q(chapters__people__id=person_filter)
        ).distinct()
    
    location_filter = request.GET.get('location')
    if location_filter:
        # Filter films that have the location in film metadata OR chapter metadata
        films = films.filter(
            Q(locations__id=location_filter) |
            Q(chapters__locations__id=location_filter)
        ).distinct()
    
    tag_filter = request.GET.get('tag')
    if tag_filter:
        # Filter films that have the tag in film metadata OR chapter metadata
        films = films.filter(
            Q(tags__tag=tag_filter) |
            Q(chapters__tags__tag=tag_filter)
        ).distinct()
    
    # Sorting
    sort_by = request.GET.get('sort', 'playlist')  # Default to playlist order
    sort_dir = request.GET.get('sort_dir', 'asc')
    
    if sort_by == 'playlist':
        if sort_dir == 'desc':
            films = films.order_by('-playlist_order')
        else:
            films = films.order_by('playlist_order')
    elif sort_by == 'title':
        if sort_dir == 'desc':
            films = films.order_by('-title')
        else:
            films = films.order_by('title')
    elif sort_by == 'year':
        if sort_dir == 'desc':
            films = films.order_by('-years')
        else:
            films = films.order_by('years')
    elif sort_by == 'duration':
        if sort_dir == 'desc':
            films = films.order_by('-duration')
        else:
            films = films.order_by('duration')
    elif sort_by == 'date':
        if sort_dir == 'desc':
            films = films.order_by('-upload_date', 'title')
        else:
            films = films.order_by('upload_date', 'title')
    else:  # fallback to playlist order
        films = films.order_by('playlist_order')
    
    # Pagination
    paginator = Paginator(films, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add aggregated metadata to each film
    for film in page_obj:
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
    
    # Get filter options for sidebar
    all_years = set()
    for film in Film.objects.all():
        all_years.update(film.get_year_list())
    all_years = sorted(all_years, reverse=True)
    
    people = Person.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0).order_by('last_name', 'first_name')[:20]
    
    locations = Location.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0).order_by('name')[:20]
    
    tags = Tag.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0).order_by('tag')
    
    context = {
        'page_obj': page_obj,
        'films': page_obj,
        'search_query': search_query,
        'current_filters': {
            'year': year_filter,
            'person': person_filter,
            'location': location_filter,
            'tag': tag_filter,
            'sort': sort_by,
            'sort_dir': sort_dir,
        },
        'filter_options': {
            'years': all_years,
            'people': people,
            'locations': locations,
            'tags': tags,
        }
    }
    return render(request, 'films/catalog.html', context)


def film_detail(request, file_id):
    """Film detail page with YouTube player and chapter editor"""
    film = get_object_or_404(Film, file_id=file_id)
    chapters = film.chapters.all().prefetch_related(
        'people', 'locations', 'tags'
    )
    
    # Get aggregated metadata (union of film and chapter associations)
    from main.models import Person, Location, Tag
    
    # Aggregate people: union of film people and chapter people
    all_people = Person.objects.filter(
        Q(filmpeople__film=film) | Q(chapterpeople__chapter__film=film)
    ).distinct().order_by('last_name', 'first_name')
    
    # Aggregate locations: union of film locations and chapter locations  
    all_locations = Location.objects.filter(
        Q(filmlocations__film=film) | Q(chapterlocations__chapter__film=film)
    ).distinct().order_by('name')
    
    # Aggregate tags: union of film tags and chapter tags
    all_tags = Tag.objects.filter(
        Q(filmtags__film=film) | Q(chaptertags__chapter__film=film)
    ).distinct().order_by('tag')
    
    # Aggregate years: union of film years and chapter years
    all_years_set = set()
    if film.years:
        all_years_set.update(film.get_year_list())
    for chapter in chapters:
        if chapter.years:
            # Parse chapter years similar to how film years are parsed
            chapter_years = [int(year.strip()) for year in chapter.years.replace(',', ' ').split() if year.strip().isdigit()]
            all_years_set.update(chapter_years)
    all_years = sorted(all_years_set)
    
    # Related films using aggregated metadata
    related_films = Film.objects.filter(
        Q(people__in=all_people) |
        Q(locations__in=all_locations) |
        Q(tags__in=all_tags)
    ).exclude(id=film.id).distinct()[:6]
    
    context = {
        'film': film,
        'chapters': chapters,
        'all_people': all_people,
        'all_locations': all_locations,
        'all_tags': all_tags,
        'all_years': all_years,
        'related_films': related_films,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'films/detail.html', context)


def chapter_metadata_api(request, file_id, chapter_id):
    """API endpoint for chapter metadata editing"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    film = get_object_or_404(Film, file_id=file_id)
    chapter = get_object_or_404(Chapter, id=chapter_id, film=film)
    
    if request.method == 'GET':
        # Return current metadata including notes
        data = {
            'people': [{'id': p.id, 'full_name': p.full_name()} for p in chapter.people.all()],
            'locations': [{'id': l.id, 'name': l.name} for l in chapter.locations.all()],
            'tags': [{'id': t.tag, 'tag': t.tag} for t in chapter.tags.all()],
            'years': chapter.years or '',
            'notes': chapter.description or '',
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        # Update metadata
        import json
        data = json.loads(request.body)
        
        # Update people
        if 'people' in data:
            chapter.people.clear()
            for person_id in data['people']:
                person = Person.objects.get(id=person_id)
                chapter.people.add(person)
        
        # Update locations
        if 'locations' in data:
            chapter.locations.clear()
            for location_id in data['locations']:
                location = Location.objects.get(id=location_id)
                chapter.locations.add(location)
        
        # Update tags
        if 'tags' in data:
            chapter.tags.clear()
            for tag_name in data['tags']:
                tag, created = Tag.objects.get_or_create(tag=tag_name)
                chapter.tags.add(tag)
        
        # Update years
        if 'years' in data:
            chapter.years = data['years']
            chapter.save()
        
        # Update metadata flags
        chapter.update_metadata_flags()
        
        # Return updated metadata for UI refresh
        updated_metadata = {
            'people': [{'id': p.id, 'full_name': p.full_name()} for p in chapter.people.all()],
            'locations': [{'id': l.id, 'name': l.name} for l in chapter.locations.all()],
            'tags': [{'id': t.tag, 'tag': t.tag} for t in chapter.tags.all()],
            'years': chapter.years or '',
        }
        
        return JsonResponse({'success': True, 'updated_metadata': updated_metadata})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def animated_thumbnail_data(request, file_id):
    """API endpoint for animated thumbnail data"""
    film = get_object_or_404(Film, file_id=file_id)
    
    if not film.has_animated_thumbnail():
        return JsonResponse({'animated': False})
    
    data = {
        'animated': True,
        'sprite_url': film.preview_sprite_url,
        'frame_count': film.preview_frame_count,
        'frame_interval': film.preview_frame_interval,
        'sprite_width': film.preview_sprite_width,
        'sprite_height': film.preview_sprite_height,
    }
    return JsonResponse(data)


# New API endpoints for metadata editing

@require_http_methods(["GET"])
def people_autocomplete(request):
    """Autocomplete endpoint for people"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    people = Person.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    )[:10]
    
    results = [
        {
            'id': person.id,
            'text': person.full_name(),
            'name': person.full_name()
        }
        for person in people
    ]
    
    return JsonResponse({'results': results})


@require_http_methods(["GET"])
def locations_autocomplete(request):
    """Autocomplete endpoint for locations"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    locations = Location.objects.filter(
        Q(name__icontains=query) | Q(city__icontains=query)
    )[:10]
    
    results = [
        {
            'id': location.id,
            'text': location.name,
            'name': location.name
        }
        for location in locations
    ]
    
    return JsonResponse({'results': results})


@require_http_methods(["GET"])
def tags_autocomplete(request):
    """Autocomplete endpoint for tags"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    tags = Tag.objects.filter(tag__icontains=query)[:10]
    
    results = [
        {
            'id': tag.tag,
            'text': tag.tag,
            'name': tag.tag
        }
        for tag in tags
    ]
    
    return JsonResponse({'results': results})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_film_metadata(request, file_id):
    """Update film-level metadata"""
    film = get_object_or_404(Film, file_id=file_id)
    
    try:
        data = json.loads(request.body)
        metadata_type = data.get('type')
        action = data.get('action')  # 'add' or 'remove'
        
        if metadata_type == 'people':
            person_name = data.get('value')
            if action == 'add':
                # Get or create person
                parts = person_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                person, created = Person.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name
                )
                film.people.add(person)
            elif action == 'remove':
                person_id = data.get('id')
                film.people.remove(person_id)
                
        elif metadata_type == 'locations':
            if action == 'add':
                location_name = data.get('value')
                location, created = Location.objects.get_or_create(name=location_name)
                film.locations.add(location)
            elif action == 'remove':
                location_id = data.get('id')
                film.locations.remove(location_id)
                
        elif metadata_type == 'tags':
            if action == 'add':
                tag_name = data.get('value')
                tag, created = Tag.objects.get_or_create(tag=tag_name)
                film.tags.add(tag)
            elif action == 'remove':
                tag_name = data.get('id')
                film.tags.remove(tag_name)
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@csrf_exempt  
@require_http_methods(["POST"])
def update_chapter_metadata(request, chapter_id):
    """Update chapter-level metadata"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    try:
        data = json.loads(request.body)
        metadata_type = data.get('type')
        action = data.get('action')  # 'add' or 'remove'
        
        if metadata_type == 'people':
            if action == 'add':
                person_name = data.get('value')
                parts = person_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
                person, created = Person.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name
                )
                chapter.people.add(person)
            elif action == 'remove':
                person_id = data.get('id')
                chapter.people.remove(person_id)
                
        elif metadata_type == 'locations':
            if action == 'add':
                location_name = data.get('value')
                location, created = Location.objects.get_or_create(name=location_name)
                chapter.locations.add(location)
            elif action == 'remove':
                location_id = data.get('id')
                chapter.locations.remove(location_id)
                
        elif metadata_type == 'tags':
            if action == 'add':
                tag_name = data.get('value')
                tag, created = Tag.objects.get_or_create(tag=tag_name)
                chapter.tags.add(tag)
            elif action == 'remove':
                tag_name = data.get('id')
                chapter.tags.remove(tag_name)
        
        elif metadata_type == 'years':
            if action == 'set':
                years = data.get('value', '')
                chapter.years = years
                chapter.save()
        
        # Update metadata flags
        chapter.update_metadata_flags()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_chapter_metadata(request, chapter_id):
    """Get chapter metadata for editing"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    data = {
        'people': [{'id': p.id, 'full_name': p.full_name()} for p in chapter.people.all()],
        'locations': [{'id': l.id, 'name': l.name} for l in chapter.locations.all()],
        'tags': [{'id': t.tag, 'tag': t.tag} for t in chapter.tags.all()],
        'years': chapter.years or '',
        'notes': chapter.description or '',
    }
    return JsonResponse(data)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_film_years(request, file_id):
    """Update film years"""
    film = get_object_or_404(Film, file_id=file_id)
    
    try:
        data = json.loads(request.body)
        years = data.get('years', '')
        
        film.years = years
        film.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
def get_film_aggregated_metadata(request, file_id):
    """Get aggregated metadata for film (union of film and chapter metadata)"""
    film = get_object_or_404(Film, file_id=file_id)
    
    from main.models import Person, Location, Tag
    
    # Get aggregated metadata (same logic as in film_detail view)
    all_people = Person.objects.filter(
        Q(filmpeople__film=film) | Q(chapterpeople__chapter__film=film)
    ).distinct().order_by('last_name', 'first_name')
    
    all_locations = Location.objects.filter(
        Q(filmlocations__film=film) | Q(chapterlocations__chapter__film=film)
    ).distinct().order_by('name')
    
    all_tags = Tag.objects.filter(
        Q(filmtags__film=film) | Q(chaptertags__chapter__film=film)
    ).distinct().order_by('tag')
    
    # Aggregate years: union of film years and chapter years
    chapters = film.chapters.all()
    all_years_set = set()
    if film.years:
        all_years_set.update(film.get_year_list())
    for chapter in chapters:
        if chapter.years:
            # Parse chapter years similar to how film years are parsed
            chapter_years = [int(year.strip()) for year in chapter.years.replace(',', ' ').split() if year.strip().isdigit()]
            all_years_set.update(chapter_years)
    all_years = sorted(all_years_set)
    
    return JsonResponse({
        'success': True,
        'people': [{'id': p.id, 'full_name': p.full_name()} for p in all_people],
        'locations': [{'id': l.id, 'name': l.name} for l in all_locations],
        'tags': [{'id': t.tag, 'tag': t.tag} for t in all_tags],
        'years': all_years,
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_chapter_notes(request, chapter_id):
    """Update chapter notes"""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    try:
        data = json.loads(request.body)
        notes = data.get('notes', '')
        
        chapter.description = notes
        chapter.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

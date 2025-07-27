#!/usr/bin/env python
"""
Comprehensive Data Management Tool

This script consolidates all data import and management functionality:
- Import films from CSV files with validation
- Import chapter metadata from Excel files
- Audit data consistency across sources
- Map YouTube video IDs to films
- Generate import/export reports
- Validate data integrity
"""

import os
import sys
import django
import csv
import re
import json
import argparse
from datetime import datetime
from django.utils import timezone

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Person, Location, Tag, Chapter

def parse_chapters(chapters_text):
    """Parse chapter information from the chapters column"""
    if not chapters_text:
        return []
    
    chapters = []
    # Split by lines and look for timestamp patterns
    lines = chapters_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for timestamp at the beginning: HH:MM or MM:SS followed by description
        match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$', line)
        if match:
            timestamp, description = match.groups()
            chapters.append({
                'timestamp': timestamp,
                'description': description.strip()
            })
    
    return chapters

def extract_file_id_from_summary(summary_text):
    """Extract File ID from the summary column (YouTube description format)"""
    if not summary_text:
        return None
    
    # Look for File ID at the end of the summary
    file_id_match = re.search(r'File ID:\s*([^\s\n]+)', summary_text, re.IGNORECASE)
    if file_id_match:
        return file_id_match.group(1).strip()
    
    return None

def parse_people(people_text):
    """Parse people from the people column"""
    if not people_text:
        return []
    
    # Split by commas and clean up
    people = [p.strip() for p in people_text.split(',') if p.strip()]
    return people

def parse_locations(location_text):
    """Parse locations from the location column"""
    if not location_text:
        return []
    
    # Split by commas and periods, clean up
    locations = []
    if location_text:
        # Split by commas first
        for loc in location_text.split(','):
            loc = loc.strip()
            if loc:
                # Also split by periods for sub-locations
                for subloc in loc.split('.'):
                    subloc = subloc.strip()
                    if subloc and subloc not in locations:
                        locations.append(subloc)
    
    return locations

def parse_years(years_text):
    """Parse years from the years column"""
    if not years_text:
        return []
    
    years = []
    # Find all 4-digit years
    year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', years_text)
    for year in year_matches:
        if int(year) not in years:
            years.append(int(year))
    
    return sorted(years)

def import_csv_data(csv_file='famil_movies_updated.csv', clear_existing=False, dry_run=False):
    """Import film data from CSV file"""
    print(f"=== IMPORTING CSV DATA: {csv_file} ===\n")
    
    if not os.path.exists(csv_file):
        print(f"ERROR: {csv_file} not found")
        return
    
    if clear_existing and not dry_run:
        print("Clearing existing film data...")
        Film.objects.all().delete()
        Person.objects.all().delete()
        Location.objects.all().delete()
        Tag.objects.all().delete()
    elif clear_existing:
        print("[DRY RUN] Would clear existing film data")
    
    imported_count = 0
    updated_count = 0
    errors = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        print(f"CSV columns: {list(reader.fieldnames)}\n")
        
        for row_num, row in enumerate(reader, 1):
            try:
                # Get the filename (File ID)
                filename = row.get('Filenames', '').strip()
                if not filename:
                    print(f"Row {row_num}: Skipping - no filename")
                    continue
                
                # Verify File ID matches filename
                summary = row.get('Summary', '')
                extracted_file_id = extract_file_id_from_summary(summary)
                
                if extracted_file_id and extracted_file_id != filename:
                    print(f"Row {row_num}: WARNING - Filename '{filename}' doesn't match File ID '{extracted_file_id}' in summary")
                
                # Use filename as file_id
                file_id = filename
                
                # Get basic fields
                title = row.get('Title', '').strip()
                description = row.get('Description', '').strip()
                duration = row.get('Duration at 23.97 fps (most of this was shot at 16 or 18 FPS)', '').strip()
                tech_notes = row.get('Tech Notes', '').strip()
                
                # Parse chapters
                chapters_text = row.get('Chapters', '')
                chapters = parse_chapters(chapters_text)
                
                # Parse people, locations, years
                people_list = parse_people(row.get('People', ''))
                locations_list = parse_locations(row.get('Location', ''))
                years_list = parse_years(row.get('Years', ''))
                
                if dry_run:
                    print(f"[DRY RUN] Would import: {file_id} - {title[:50]}")
                    if chapters:
                        print(f"  Would create {len(chapters)} chapters")
                    if people_list:
                        print(f"  Would link people: {', '.join(people_list[:3])}")
                    if locations_list:
                        print(f"  Would link locations: {', '.join(locations_list[:3])}")
                    continue
                
                # Create or update the film
                film, created = Film.objects.get_or_create(
                    file_id=file_id,
                    defaults={
                        'title': title,
                        'description': description,
                        'summary': description,  # Use description as summary too
                        'technical_notes': tech_notes,
                        'years': ', '.join(map(str, years_list)) if years_list else '',
                        'youtube_id': f'placeholder_{file_id}',  # Will be updated later
                        'youtube_url': f'https://www.youtube.com/watch?v=placeholder_{file_id}',
                        'thumbnail_url': f'https://img.youtube.com/vi/placeholder_{file_id}/maxresdefault.jpg',
                    }
                )
                
                if not created:
                    # Update existing film
                    film.title = title
                    film.description = description
                    film.summary = description
                    film.technical_notes = tech_notes
                    film.years = ', '.join(map(str, years_list)) if years_list else ''
                    film.save()
                    updated_count += 1
                else:
                    imported_count += 1
                
                # Clear existing chapters for this film
                Chapter.objects.filter(film=film).delete()
                
                # Create chapters
                for i, chapter_data in enumerate(chapters):
                    Chapter.objects.create(
                        film=film,
                        start_time=chapter_data['timestamp'],
                        title=chapter_data['description'],
                        order=i + 1
                    )
                
                # Create/link people
                for person_name in people_list:
                    # Split name into first and last
                    name_parts = person_name.strip().split(' ', 1)
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    person, _ = Person.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name
                    )
                    film.people.add(person)
                
                # Create/link locations
                for location_name in locations_list:
                    location, _ = Location.objects.get_or_create(name=location_name)
                    film.locations.add(location)
                
                action = "Created" if created else "Updated"
                print(f"{action}: {file_id} - {title[:50]}{'...' if len(title) > 50 else ''}")
                
                if extracted_file_id and extracted_file_id != filename:
                    print(f"  ⚠️  File ID mismatch: CSV filename='{filename}', Summary File ID='{extracted_file_id}'")
                
                if chapters:
                    print(f"  📖 {len(chapters)} chapters")
                if people_list:
                    print(f"  👥 People: {', '.join(people_list[:3])}{'...' if len(people_list) > 3 else ''}")
                if locations_list:
                    print(f"  📍 Locations: {', '.join(locations_list[:3])}{'...' if len(locations_list) > 3 else ''}")
                if years_list:
                    print(f"  📅 Years: {', '.join(map(str, years_list))}")
                
                print()
                
            except Exception as e:
                error_msg = f"Row {row_num} ({row.get('Filenames', 'unknown')}): {str(e)}"
                errors.append(error_msg)
                print(f"ERROR: {error_msg}")
    
    print(f"\n=== IMPORT SUMMARY ===")
    print(f"New films imported: {imported_count}")
    print(f"Existing films updated: {updated_count}")
    print(f"Total people: {Person.objects.count()}")
    print(f"Total locations: {Location.objects.count()}")
    
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    
    if dry_run:
        print("\n[DRY RUN] No changes were made to the database")
    else:
        print(f"\n✓ Import complete!")

def map_youtube_ids(mappings, dry_run=False):
    """Map YouTube video IDs to specific films"""
    print("=== MAPPING YOUTUBE IDS ===\n")
    
    # Default mappings if none provided
    if not mappings:
        mappings = {
            'PB-14_FROS': 'YFIDOmMvxiY',
            'P-04_FROS': 'abc123def456',  # Example
        }
    
    mapped_count = 0
    errors = []
    
    for file_id, youtube_id in mappings.items():
        try:
            film = Film.objects.get(file_id=file_id)
            
            if dry_run:
                print(f"[DRY RUN] Would map {file_id} -> {youtube_id}")
                continue
            
            # Update YouTube information
            film.youtube_id = youtube_id
            film.youtube_url = f'https://www.youtube.com/watch?v={youtube_id}'
            film.thumbnail_url = f'https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg'
            film.thumbnail_high_url = f'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'
            film.thumbnail_medium_url = f'https://img.youtube.com/vi/{youtube_id}/mqdefault.jpg'
            film.save()
            
            mapped_count += 1
            print(f"✅ Mapped {file_id} -> {youtube_id}")
            
        except Film.DoesNotExist:
            error_msg = f"Film {file_id} not found in database"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
        except Exception as e:
            error_msg = f"Error mapping {file_id}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    print(f"\n=== MAPPING SUMMARY ===")
    print(f"Successfully mapped: {mapped_count}")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")

def audit_data():
    """Comprehensive data audit across sources"""
    print("=== DATA AUDIT ===\n")
    
    # Database statistics
    total_films = Film.objects.count()
    films_with_youtube = Film.objects.exclude(youtube_id__startswith='placeholder_').count()
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct().count()
    total_people = Person.objects.count()
    total_locations = Location.objects.count()
    total_chapters = Chapter.objects.count()
    
    print(f"Database Statistics:")
    print(f"  Total films: {total_films}")
    print(f"  Films with YouTube mappings: {films_with_youtube}")
    print(f"  Films with chapters: {films_with_chapters}")
    print(f"  Total people: {total_people}")
    print(f"  Total locations: {total_locations}")
    print(f"  Total chapters: {total_chapters}")
    
    # Check for common issues
    print(f"\n=== DATA QUALITY CHECKS ===")
    
    # Films without titles
    films_no_title = Film.objects.filter(title='').count()
    print(f"Films without titles: {films_no_title}")
    
    # Films without descriptions
    films_no_desc = Film.objects.filter(description='').count()
    print(f"Films without descriptions: {films_no_desc}")
    
    # People with incomplete names
    people_no_last = Person.objects.filter(last_name='').count()
    print(f"People without last names: {people_no_last}")
    
    # Chapters without start times
    chapters_no_time = Chapter.objects.filter(start_time='').count()
    print(f"Chapters without start times: {chapters_no_time}")
    
    # Check for duplicates
    print(f"\n=== DUPLICATE DETECTION ===")
    
    # Duplicate films by file_id
    from django.db.models import Count
    duplicate_files = Film.objects.values('file_id').annotate(
        count=Count('file_id')
    ).filter(count__gt=1)
    print(f"Duplicate film file_ids: {duplicate_files.count()}")
    
    # Duplicate people by name
    duplicate_people = Person.objects.values('first_name', 'last_name').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    print(f"Duplicate people names: {duplicate_people.count()}")
    
    # Show top used people and locations
    print(f"\n=== TOP USAGE ===")
    
    from django.db.models import Q
    
    # Top people by film count
    print("Top 5 people by film appearances:")
    top_people = Person.objects.annotate(
        film_count=Count('film', distinct=True)
    ).filter(film_count__gt=0).order_by('-film_count')[:5]
    
    for person in top_people:
        print(f"  {person.first_name} {person.last_name}: {person.film_count} films")
    
    # Top locations by film count
    print("\nTop 5 locations by film appearances:")
    top_locations = Location.objects.annotate(
        film_count=Count('film', distinct=True)
    ).filter(film_count__gt=0).order_by('-film_count')[:5]
    
    for location in top_locations:
        print(f"  {location.name}: {location.film_count} films")

def extract_film_data(file_id):
    """Extract and display complete data for a specific film"""
    print(f"=== EXTRACTING DATA FOR {file_id} ===\n")
    
    try:
        film = Film.objects.get(file_id=file_id)
        
        print(f"File ID: {film.file_id}")
        print(f"Title: {film.title}")
        print(f"Description: {film.description}")
        print(f"Years: {film.years}")
        print(f"Technical Notes: {film.technical_notes}")
        print(f"YouTube ID: {film.youtube_id}")
        print(f"YouTube URL: {film.youtube_url}")
        
        # Show chapters
        chapters = film.chapters.all().order_by('order')
        if chapters:
            print(f"\nChapters ({chapters.count()}):")
            for chapter in chapters:
                print(f"  {chapter.order}: {chapter.start_time} - {chapter.title}")
        else:
            print("\nNo chapters found")
        
        # Show people
        people = film.people.all()
        if people:
            print(f"\nPeople ({people.count()}):")
            for person in people:
                print(f"  - {person.first_name} {person.last_name}")
        else:
            print("\nNo people linked")
        
        # Show locations
        locations = film.locations.all()
        if locations:
            print(f"\nLocations ({locations.count()}):")
            for location in locations:
                print(f"  - {location.name}")
        else:
            print("\nNo locations linked")
            
    except Film.DoesNotExist:
        print(f"Film with file_id '{file_id}' not found")

def generate_report(output_file='data_report.json'):
    """Generate comprehensive data report"""
    print(f"=== GENERATING DATA REPORT: {output_file} ===\n")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_stats': {
            'total_films': Film.objects.count(),
            'films_with_youtube': Film.objects.exclude(youtube_id__startswith='placeholder_').count(),
            'films_with_chapters': Film.objects.filter(chapters__isnull=False).distinct().count(),
            'total_people': Person.objects.count(),
            'total_locations': Location.objects.count(),
            'total_chapters': Chapter.objects.count(),
        },
        'quality_issues': {
            'films_no_title': Film.objects.filter(title='').count(),
            'films_no_description': Film.objects.filter(description='').count(),
            'people_no_last_name': Person.objects.filter(last_name='').count(),
            'chapters_no_start_time': Chapter.objects.filter(start_time='').count(),
        },
        'top_people': [],
        'top_locations': [],
        'recent_films': []
    }
    
    # Top people by film count
    from django.db.models import Count
    top_people = Person.objects.annotate(
        film_count=Count('film', distinct=True)
    ).filter(film_count__gt=0).order_by('-film_count')[:10]
    
    for person in top_people:
        report['top_people'].append({
            'name': f"{person.first_name} {person.last_name}",
            'film_count': person.film_count
        })
    
    # Top locations by film count
    top_locations = Location.objects.annotate(
        film_count=Count('film', distinct=True)
    ).filter(film_count__gt=0).order_by('-film_count')[:10]
    
    for location in top_locations:
        report['top_locations'].append({
            'name': location.name,
            'film_count': location.film_count
        })
    
    # Recent films (by ID)
    recent_films = Film.objects.order_by('-id')[:10]
    for film in recent_films:
        report['recent_films'].append({
            'file_id': film.file_id,
            'title': film.title,
            'youtube_id': film.youtube_id,
            'chapter_count': film.chapters.count()
        })
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to {output_file}")
    print(f"Total films: {report['database_stats']['total_films']}")
    print(f"Films with YouTube: {report['database_stats']['films_with_youtube']}")
    print(f"Quality issues found: {sum(report['quality_issues'].values())}")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive data management tool')
    parser.add_argument('command', choices=['import-csv', 'map-youtube', 'audit', 
                                           'extract', 'report', 'all'],
                        help='Command to run')
    parser.add_argument('--csv-file', default='famil_movies_updated.csv',
                        help='CSV file to import')
    parser.add_argument('--film-id', help='Film ID for extract command')
    parser.add_argument('--output-file', default='data_report.json',
                        help='Output file for report command')
    parser.add_argument('--clear-existing', action='store_true',
                        help='Clear existing data before import')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.command == 'import-csv':
        import_csv_data(args.csv_file, args.clear_existing, args.dry_run)
    elif args.command == 'map-youtube':
        # For now, use empty mappings (could be extended to read from file)
        map_youtube_ids({}, args.dry_run)
    elif args.command == 'audit':
        audit_data()
    elif args.command == 'extract':
        if not args.film_id:
            print("ERROR: --film-id required for extract command")
            sys.exit(1)
        extract_film_data(args.film_id)
    elif args.command == 'report':
        generate_report(args.output_file)
    elif args.command == 'all':
        print("Running comprehensive data management...\n")
        
        # Import CSV data
        import_csv_data(args.csv_file, args.clear_existing, args.dry_run)
        
        print("\n" + "="*60 + "\n")
        
        # Generate audit
        audit_data()
        
        print("\n" + "="*60 + "\n")
        
        # Generate report
        generate_report(args.output_file)

if __name__ == '__main__':
    main()
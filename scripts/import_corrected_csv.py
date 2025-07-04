#!/usr/bin/env python
import os
import sys
import django
import csv
import re
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

def main():
    print("=== IMPORTING CORRECTED CSV DATA ===\n")
    
    csv_file = 'famil_movies_updated.csv'
    
    if not os.path.exists(csv_file):
        print(f"ERROR: {csv_file} not found")
        return
    
    # Clear existing data
    print("Clearing existing film data...")
    Film.objects.all().delete()
    Person.objects.all().delete()
    Location.objects.all().delete()
    Tag.objects.all().delete()
    
    imported_count = 0
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
                
                imported_count += 1
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
    print(f"Total films imported: {imported_count}")
    print(f"Total people created: {Person.objects.count()}")
    print(f"Total locations created: {Location.objects.count()}")
    
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    
    print(f"\n✓ Import complete!")

if __name__ == '__main__':
    main()
#!/usr/bin/env python
"""
Script to update person information for films and chapters based on name_cleanup3.csv.
This script parses the CSV and applies person updates according to the specified rules.
"""

import os
import sys
import csv
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, Film, Chapter, FilmPeople, ChapterPeople
from django.db import transaction

def get_or_create_person(name_str):
    """Get or create a person from 'first_name:last_name' format."""
    name_str = name_str.strip()
    if not name_str:
        return None
    
    # Special handling for "5:25" in names - this is part of the name, not a separator
    if "5:25" in name_str:
        # If it contains 5:25, treat the whole thing as the name
        # Look for the last colon that's not part of "5:25"
        if name_str.count(':') > 1:
            # Find position of "5:25"
            time_pos = name_str.find("5:25")
            if time_pos > 0:
                # Split at the colon before "5:25"
                parts = name_str[:time_pos-1], name_str[time_pos-1:]
                first_name = parts[0].strip()
                last_name = parts[1].strip()
            else:
                # "5:25" is at the beginning, unusual but handle it
                first_name = ""
                last_name = name_str
        else:
            # Only one colon and it's in "5:25", so no real separator
            first_name = ""
            last_name = name_str
    else:
        # Normal case: split on first colon
        if ':' in name_str:
            parts = name_str.split(':', 1)  # Split on first colon only
            first_name = parts[0].strip()
            last_name = parts[1].strip()
        else:
            # No colon, treat as first name only
            first_name = name_str
            last_name = ""
    
    # Try to find existing person (case-insensitive)
    person = Person.objects.filter(
        first_name__iexact=first_name, 
        last_name__iexact=last_name
    ).first()
    
    if person:
        return person
    
    # Create new person
    person = Person.objects.create(first_name=first_name, last_name=last_name)
    print(f"  - Created new person: {person.full_name()}")
    return person

def update_film_people(film, current_person, new_people, replace):
    """Update people for a film."""
    # Check if film has the current person
    if current_person and FilmPeople.objects.filter(film=film, person=current_person).exists():
        print(f"  - Film '{film.title}' has person '{current_person.full_name()}'")
        
        # Add new people
        for new_person in new_people:
            if new_person:
                film_person, created = FilmPeople.objects.get_or_create(
                    film=film, person=new_person
                )
                if created:
                    print(f"    + Added person: {new_person.full_name()}")
                else:
                    print(f"    = Already has person: {new_person.full_name()}")
        
        # Remove current person if replace=1
        if replace:
            FilmPeople.objects.filter(film=film, person=current_person).delete()
            print(f"    - Removed person: {current_person.full_name()}")

def update_chapter_people(chapter, current_person, new_people, replace):
    """Update people for a chapter."""
    # Check if chapter has the current person
    if current_person and ChapterPeople.objects.filter(chapter=chapter, person=current_person).exists():
        print(f"  - Chapter '{chapter.title}' has person '{current_person.full_name()}'")
        
        # Add new people
        for new_person in new_people:
            if new_person:
                chapter_person, created = ChapterPeople.objects.get_or_create(
                    chapter=chapter, person=new_person
                )
                if created:
                    print(f"    + Added person: {new_person.full_name()}")
                else:
                    print(f"    = Already has person: {new_person.full_name()}")
        
        # Remove current person if replace=1
        if replace:
            ChapterPeople.objects.filter(chapter=chapter, person=current_person).delete()
            print(f"    - Removed person: {current_person.full_name()}")

def process_person_cleanup(csv_filename='name_cleanup3.csv'):
    """Process the person cleanup CSV file."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'design_docs', csv_filename)
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    print(f"Processing person cleanup CSV: {csv_filename}...")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip header row
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 3 or not any(row):  # Skip empty rows
                continue
            
            current_person_name = row[0].strip()
            new_people_str = row[1].strip()
            replace_str = row[2].strip()
            
            if not current_person_name or not new_people_str:
                continue
            
            # Parse new people (separated by |)
            new_person_names = [name.strip() for name in new_people_str.split('|') if name.strip()]
            
            # Parse replace flag
            try:
                replace = int(replace_str) == 1
            except ValueError:
                print(f"Warning: Invalid replace value '{replace_str}' in row {row_num}, treating as 0")
                replace = False
            
            print(f"\\nProcessing row {row_num}: '{current_person_name}' -> {new_person_names} (replace={replace})")
            
            # Find current person
            current_person = get_or_create_person(current_person_name)
            if not current_person:
                print(f"  - Could not parse person name '{current_person_name}'")
                continue
            
            # Get new people
            new_people = []
            for new_person_name in new_person_names:
                new_person = get_or_create_person(new_person_name)
                if new_person:
                    new_people.append(new_person)
            
            if not new_people:
                print(f"  - No valid new people found")
                continue
            
            with transaction.atomic():
                # Update all films with this person
                films_updated = 0
                for film in Film.objects.all():
                    if FilmPeople.objects.filter(film=film, person=current_person).exists():
                        update_film_people(film, current_person, new_people, replace)
                        films_updated += 1
                
                # Update all chapters with this person
                chapters_updated = 0
                for chapter in Chapter.objects.all():
                    if ChapterPeople.objects.filter(chapter=chapter, person=current_person).exists():
                        update_chapter_people(chapter, current_person, new_people, replace)
                        chapters_updated += 1
                
                if films_updated == 0 and chapters_updated == 0:
                    print(f"  - No films or chapters found with person '{current_person.full_name()}'")
    
    print("\\nPerson cleanup complete!")

def print_person_summary():
    """Print a summary of people in the database."""
    print("\\n=== Person Summary ===")
    
    total_people = Person.objects.count()
    print(f"Total people in database: {total_people}")
    
    # Show top 10 most used people
    print("\\nTop 10 most used people:")
    from django.db.models import Count, Q
    
    # Get people with film counts (using our corrected logic)
    people = Person.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct()
    
    # Calculate counts and sort
    person_counts = []
    for person in people:
        from main.models import Film
        films = Film.objects.filter(
            Q(people=person) | Q(chapters__people=person)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        person_counts.append((person, films.count()))
    
    person_counts.sort(key=lambda x: x[1], reverse=True)
    
    for person, count in person_counts[:10]:
        print(f"  {person.full_name()}: {count} films")

if __name__ == "__main__":
    process_person_cleanup()
    print_person_summary()
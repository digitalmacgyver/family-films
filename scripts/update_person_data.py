#!/usr/bin/env python
"""
Script to update person information for films and chapters based on name_cleanup.csv.
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
    if not name_str or ':' not in name_str:
        print(f"    Warning: Invalid name format '{name_str}' - skipping")
        return None
    
    # Handle special case of "5:25" in name
    if "5:25" in name_str:
        # This is part of the name, not a separator
        # Look for the actual separator (should be the first colon not part of "5:25")
        parts = name_str.split(':')
        if len(parts) >= 2:
            # If we have "Don Sear around 5:25" as last name, we need to find the real separator
            # This is a special case - let's handle it manually
            if "Don Sear around 5:25" in name_str:
                first_name = "and"  # Based on the CSV pattern
                last_name = "Mark. Don Sear around 5:25"
            else:
                first_name = parts[0].strip()
                last_name = ':'.join(parts[1:]).strip()
        else:
            return None
    else:
        parts = name_str.split(':', 1)  # Split on first colon only
        if len(parts) != 2:
            print(f"    Warning: Invalid name format '{name_str}' - skipping")
            return None
        
        first_name = parts[0].strip()
        last_name = parts[1].strip()
    
    if not first_name or not last_name:
        print(f"    Warning: Empty first or last name in '{name_str}' - skipping")
        return None
    
    # Try to find existing person (case-insensitive)
    person = Person.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
    if person:
        return person
    
    # Create new person
    person = Person.objects.create(first_name=first_name, last_name=last_name)
    print(f"    - Created new person: {person.full_name()}")
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

def process_name_cleanup(csv_filename='name_cleanup.csv'):
    """Process the name cleanup CSV file."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'design_docs', csv_filename)
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    print(f"Processing name cleanup CSV: {csv_filename}...")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip header row
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 2 or not any(row):  # Skip empty rows
                continue
            
            # Handle missing replace column
            if len(row) < 3:
                replace_str = "0"  # Default to no replace
            else:
                replace_str = row[2].strip()
            
            current_name = row[0].strip()
            new_names_str = row[1].strip()
            
            if not current_name or not new_names_str:
                continue
            
            # Parse new names (separated by |)
            new_name_strings = [name.strip() for name in new_names_str.split('|') if name.strip()]
            
            # Parse replace flag
            try:
                replace = int(replace_str) == 1
            except ValueError:
                print(f"Warning: Invalid replace value '{replace_str}' in row {row_num}, treating as 0")
                replace = False
            
            print(f"\nProcessing row {row_num}: '{current_name}' -> {new_name_strings} (replace={replace})")
            
            # Get current person
            current_person = get_or_create_person(current_name)
            if not current_person:
                print(f"  - Could not parse current person name: '{current_name}'")
                continue
            
            # Get new people
            new_people = []
            for new_name_str in new_name_strings:
                new_person = get_or_create_person(new_name_str)
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
    
    print("\nName cleanup complete!")

def print_person_summary():
    """Print a summary of people in the database."""
    print("\n=== Person Summary ===")
    
    total_people = Person.objects.count()
    print(f"Total people in database: {total_people}")
    
    # Show top 10 most used people
    print("\nTop 10 most used people:")
    from django.db.models import Count
    
    top_people = Person.objects.annotate(
        film_count=Count('film', distinct=True),
        chapter_count=Count('chapter', distinct=True)
    ).order_by('-film_count', '-chapter_count')[:10]
    
    for person in top_people:
        print(f"  {person.full_name()}: {person.film_count} films, {person.chapter_count} chapters")

if __name__ == "__main__":
    import sys
    
    # Allow specifying CSV filename as command line argument
    csv_filename = sys.argv[1] if len(sys.argv) > 1 else 'name_cleanup.csv'
    
    process_name_cleanup(csv_filename)
    print_person_summary()
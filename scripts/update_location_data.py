#!/usr/bin/env python
"""
Script to update location information for films and chapters based on location_cleanup.csv.
This script parses the CSV and applies location updates according to the specified rules.
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

from main.models import Location, Film, Chapter, FilmLocations, ChapterLocations
from django.db import transaction

def get_or_create_location(name):
    """Get or create a location by name."""
    name = name.strip()
    if not name:
        return None
    
    # Try to find existing location (case-insensitive)
    location = Location.objects.filter(name__iexact=name).first()
    if location:
        return location
    
    # Create new location
    location = Location.objects.create(name=name)
    print(f"  - Created new location: {name}")
    return location

def update_film_locations(film, current_location_name, new_location_names, replace):
    """Update locations for a film."""
    current_location = Location.objects.filter(name__iexact=current_location_name.strip()).first()
    
    # Check if film has the current location
    if current_location and FilmLocations.objects.filter(film=film, location=current_location).exists():
        print(f"  - Film '{film.title}' has location '{current_location_name}'")
        
        # Add new locations
        for new_location_name in new_location_names:
            new_location = get_or_create_location(new_location_name)
            if new_location:
                film_location, created = FilmLocations.objects.get_or_create(
                    film=film, location=new_location
                )
                if created:
                    print(f"    + Added location: {new_location_name}")
                else:
                    print(f"    = Already has location: {new_location_name}")
        
        # Remove current location if replace=1
        if replace:
            FilmLocations.objects.filter(film=film, location=current_location).delete()
            print(f"    - Removed location: {current_location_name}")

def update_chapter_locations(chapter, current_location_name, new_location_names, replace):
    """Update locations for a chapter."""
    current_location = Location.objects.filter(name__iexact=current_location_name.strip()).first()
    
    # Check if chapter has the current location
    if current_location and ChapterLocations.objects.filter(chapter=chapter, location=current_location).exists():
        print(f"  - Chapter '{chapter.title}' has location '{current_location_name}'")
        
        # Add new locations
        for new_location_name in new_location_names:
            new_location = get_or_create_location(new_location_name)
            if new_location:
                chapter_location, created = ChapterLocations.objects.get_or_create(
                    chapter=chapter, location=new_location
                )
                if created:
                    print(f"    + Added location: {new_location_name}")
                else:
                    print(f"    = Already has location: {new_location_name}")
        
        # Remove current location if replace=1
        if replace:
            ChapterLocations.objects.filter(chapter=chapter, location=current_location).delete()
            print(f"    - Removed location: {current_location_name}")

def process_location_cleanup(csv_filename='location_cleanup.csv'):
    """Process the location cleanup CSV file."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'design_docs', csv_filename)
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    print(f"Processing location cleanup CSV: {csv_filename}...")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip header row
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 3 or not any(row):  # Skip empty rows
                continue
            
            current_location = row[0].strip()
            new_locations_str = row[1].strip()
            replace_str = row[2].strip()
            
            if not current_location or not new_locations_str:
                continue
            
            # Parse new locations (separated by |)
            new_location_names = [loc.strip() for loc in new_locations_str.split('|') if loc.strip()]
            
            # Parse replace flag
            try:
                replace = int(replace_str) == 1
            except ValueError:
                print(f"Warning: Invalid replace value '{replace_str}' in row {row_num}, treating as 0")
                replace = False
            
            print(f"\nProcessing row {row_num}: '{current_location}' -> {new_location_names} (replace={replace})")
            
            # Debug: check if we can find this location
            location_obj = Location.objects.filter(name__iexact=current_location.strip()).first()
            if location_obj:
                print(f"  - Found location in database: '{location_obj.name}' (ID: {location_obj.id})")
            else:
                print(f"  - Location not found in database, searching for similar names...")
                similar = Location.objects.filter(name__icontains=current_location[:10] if len(current_location) > 10 else current_location)
                for sim in similar:
                    print(f"    Similar: '{sim.name}'")
            
            with transaction.atomic():
                # Update all films with this location
                films_updated = 0
                for film in Film.objects.all():
                    old_count = films_updated
                    update_film_locations(film, current_location, new_location_names, replace)
                    if films_updated == old_count:  # Check if anything was updated
                        # Only count if we actually made changes
                        current_location_obj = Location.objects.filter(name__iexact=current_location).first()
                        if current_location_obj and FilmLocations.objects.filter(film=film, location=current_location_obj).exists():
                            films_updated += 1
                
                # Update all chapters with this location
                chapters_updated = 0
                for chapter in Chapter.objects.all():
                    old_count = chapters_updated
                    update_chapter_locations(chapter, current_location, new_location_names, replace)
                    if chapters_updated == old_count:  # Check if anything was updated
                        # Only count if we actually made changes
                        current_location_obj = Location.objects.filter(name__iexact=current_location).first()
                        if current_location_obj and ChapterLocations.objects.filter(chapter=chapter, location=current_location_obj).exists():
                            chapters_updated += 1
                
                if films_updated == 0 and chapters_updated == 0:
                    print(f"  - No films or chapters found with location '{current_location}'")
    
    print("\nLocation cleanup complete!")

def print_location_summary():
    """Print a summary of locations in the database."""
    print("\n=== Location Summary ===")
    
    total_locations = Location.objects.count()
    print(f"Total locations in database: {total_locations}")
    
    # Show top 10 most used locations
    print("\nTop 10 most used locations:")
    from django.db.models import Count
    
    top_locations = Location.objects.annotate(
        film_count=Count('film', distinct=True),
        chapter_count=Count('chapter', distinct=True)
    ).order_by('-film_count', '-chapter_count')[:10]
    
    for location in top_locations:
        print(f"  {location.name}: {location.film_count} films, {location.chapter_count} chapters")

if __name__ == "__main__":
    import sys
    
    # Allow specifying CSV filename as command line argument
    csv_filename = sys.argv[1] if len(sys.argv) > 1 else 'location_cleanup.csv'
    
    process_location_cleanup(csv_filename)
    print_location_summary()
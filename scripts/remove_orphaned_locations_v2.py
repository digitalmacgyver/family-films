#!/usr/bin/env python
"""
Script to find and remove locations that are not associated with any films or chapters.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Location, Film, Chapter, FilmLocations, ChapterLocations
from django.db import transaction
from django.db.models import Q

def find_orphaned_locations():
    """Find locations with no film or chapter associations."""
    # Get all locations
    all_locations = Location.objects.all()
    
    orphaned_locations = []
    
    for location in all_locations:
        # Check if location has any film associations
        has_films = FilmLocations.objects.filter(location=location).exists()
        
        # Check if location has any chapter associations
        has_chapters = ChapterLocations.objects.filter(location=location).exists()
        
        # If neither, it's orphaned
        if not has_films and not has_chapters:
            orphaned_locations.append(location)
    
    return orphaned_locations

def remove_orphaned_locations(dry_run=True):
    """Remove locations that have no associations."""
    print("Finding orphaned locations...")
    
    orphaned_locations = find_orphaned_locations()
    
    if not orphaned_locations:
        print("No orphaned locations found!")
        return
    
    print(f"\nFound {len(orphaned_locations)} orphaned locations:")
    for location in orphaned_locations:
        print(f"  - {location.name} (ID: {location.id})")
    
    if dry_run:
        print("\n[DRY RUN] No locations were deleted. Run with dry_run=False to actually delete.")
    else:
        print("\nDeleting orphaned locations...")
        with transaction.atomic():
            for location in orphaned_locations:
                location.delete()
                print(f"  ✓ Deleted: {location.name}")
        print(f"\nSuccessfully deleted {len(orphaned_locations)} orphaned locations.")

def print_location_stats():
    """Print statistics about locations."""
    total_locations = Location.objects.count()
    
    # Locations with film associations
    locations_with_films = Location.objects.filter(
        film__isnull=False
    ).distinct().count()
    
    # Locations with chapter associations
    locations_with_chapters = Location.objects.filter(
        chapter__isnull=False
    ).distinct().count()
    
    # Locations with any associations
    locations_with_any = Location.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct().count()
    
    print("\n=== Location Statistics ===")
    print(f"Total locations: {total_locations}")
    print(f"Locations with film associations: {locations_with_films}")
    print(f"Locations with chapter associations: {locations_with_chapters}")
    print(f"Locations with any associations: {locations_with_any}")
    print(f"Orphaned locations: {total_locations - locations_with_any}")

if __name__ == "__main__":
    import sys
    
    # Check for command line argument
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        dry_run = False
    
    print_location_stats()
    print("\n" + "="*50 + "\n")
    remove_orphaned_locations(dry_run=dry_run)
    
    if dry_run:
        print("\nTo actually delete orphaned locations, run:")
        print(f"  python {sys.argv[0]} --delete")
#!/usr/bin/env python
"""
Comprehensive Location Management Tool

This script consolidates all location-related functionality:
- Update locations from CSV files with add/replace operations
- Remove orphaned locations with no associations
- Fix specific location issues (like typos or incorrect formatting)
- Split compound locations into component parts
- Show location statistics and usage
"""

import os
import sys
import csv
import django
import argparse
from collections import defaultdict

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Location, Film, Chapter, FilmLocations, ChapterLocations
from django.db import transaction
from django.db.models import Count, Q

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

def update_film_locations(film, current_location, new_locations, replace):
    """Update locations for a film."""
    # Check if film has the current location
    if current_location and FilmLocations.objects.filter(film=film, location=current_location).exists():
        print(f"  - Film '{film.title}' has location '{current_location.name}'")
        
        # Add new locations
        for new_location in new_locations:
            if new_location:
                film_location, created = FilmLocations.objects.get_or_create(
                    film=film, location=new_location
                )
                if created:
                    print(f"    + Added location: {new_location.name}")
                else:
                    print(f"    = Already has location: {new_location.name}")
        
        # Remove current location if replace=1
        if replace:
            FilmLocations.objects.filter(film=film, location=current_location).delete()
            print(f"    - Removed location: {current_location.name}")

def update_chapter_locations(chapter, current_location, new_locations, replace):
    """Update locations for a chapter."""
    # Check if chapter has the current location
    if current_location and ChapterLocations.objects.filter(chapter=chapter, location=current_location).exists():
        print(f"  - Chapter '{chapter.title}' has location '{current_location.name}'")
        
        # Add new locations
        for new_location in new_locations:
            if new_location:
                chapter_location, created = ChapterLocations.objects.get_or_create(
                    chapter=chapter, location=new_location
                )
                if created:
                    print(f"    + Added location: {new_location.name}")
                else:
                    print(f"    = Already has location: {new_location.name}")
        
        # Remove current location if replace=1
        if replace:
            ChapterLocations.objects.filter(chapter=chapter, location=current_location).delete()
            print(f"    - Removed location: {current_location.name}")

def process_location_cleanup(csv_filename='location_cleanup.csv', dry_run=False):
    """Process the location cleanup CSV file."""
    # Try multiple locations for the CSV file
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                     'design_docs', csv_filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename),
        csv_filename
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print(f"Error: CSV file '{csv_filename}' not found")
        print("Tried locations:")
        for path in possible_paths:
            print(f"  - {path}")
        return
    
    print(f"Processing location cleanup CSV: {csv_path}...")
    if dry_run:
        print("[DRY RUN] No changes will be made\n")
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Skip header row
        
        updates_made = 0
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 3 or not any(row):  # Skip empty rows
                continue
            
            current_location_name = row[0].strip()
            new_locations_str = row[1].strip()
            replace_str = row[2].strip() if len(row) > 2 else '0'
            
            if not current_location_name or not new_locations_str:
                continue
            
            # Parse new locations (separated by |)
            new_location_names = [loc.strip() for loc in new_locations_str.split('|') if loc.strip()]
            
            # Parse replace flag
            try:
                replace = int(replace_str) == 1
            except ValueError:
                print(f"Warning: Invalid replace value '{replace_str}' in row {row_num}, treating as 0")
                replace = False
            
            print(f"\nProcessing row {row_num}: '{current_location_name}' -> {new_location_names} (replace={replace})")
            
            # Find current location
            current_location = Location.objects.filter(name__iexact=current_location_name).first()
            if not current_location:
                print(f"  - Location '{current_location_name}' not found in database")
                continue
            
            # Get new locations
            new_locations = []
            for new_location_name in new_location_names:
                if not dry_run:
                    new_location = get_or_create_location(new_location_name)
                    if new_location:
                        new_locations.append(new_location)
                else:
                    print(f"  - Would create/use location: {new_location_name}")
            
            if dry_run:
                # Count what would be updated
                film_count = FilmLocations.objects.filter(location=current_location).count()
                chapter_count = ChapterLocations.objects.filter(location=current_location).count()
                print(f"  - Would update {film_count} films and {chapter_count} chapters")
                continue
            
            if not new_locations:
                print(f"  - No valid new locations found")
                continue
            
            with transaction.atomic():
                # Update all films with this location
                films_updated = 0
                for film in Film.objects.all():
                    if FilmLocations.objects.filter(film=film, location=current_location).exists():
                        update_film_locations(film, current_location, new_locations, replace)
                        films_updated += 1
                
                # Update all chapters with this location
                chapters_updated = 0
                for chapter in Chapter.objects.all():
                    if ChapterLocations.objects.filter(chapter=chapter, location=current_location).exists():
                        update_chapter_locations(chapter, current_location, new_locations, replace)
                        chapters_updated += 1
                
                if films_updated == 0 and chapters_updated == 0:
                    print(f"  - No films or chapters found with location '{current_location_name}'")
                else:
                    updates_made += 1
    
    print(f"\nLocation cleanup complete! Processed {updates_made} location updates.")

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

def remove_orphaned_locations(dry_run=False):
    """Remove locations that have no associations."""
    print("=== Finding Orphaned Locations ===\n")
    
    orphaned_locations = find_orphaned_locations()
    
    if not orphaned_locations:
        print("No orphaned locations found!")
        return
    
    print(f"Found {len(orphaned_locations)} orphaned locations:")
    for location in orphaned_locations:
        print(f"  - {location.name} (ID: {location.id})")
    
    if dry_run:
        print("\n[DRY RUN] No locations were deleted.")
    else:
        print("\nDeleting orphaned locations...")
        with transaction.atomic():
            for location in orphaned_locations:
                location.delete()
                print(f"  ✓ Deleted: {location.name}")
        print(f"\nSuccessfully deleted {len(orphaned_locations)} orphaned locations.")

def fix_specific_locations(dry_run=False):
    """Fix specific known location issues."""
    print("=== Fixing Specific Location Issues ===\n")
    
    fixes_applied = 0
    
    # Fix Children's Fairyland
    original_location = Location.objects.filter(name="California locations: Children's Fairyland park in Oakland").first()
    
    if original_location:
        print(f"Found location to fix: {original_location.name}")
        print(f"Films: {original_location.film_set.count()}, Chapters: {original_location.chapter_set.count()}")
        
        # Create or get the new locations
        new_locations = [
            "Children's Fairyland Park",
            "Oakland", 
            "California"
        ]
        
        if dry_run:
            print(f"[DRY RUN] Would split into: {new_locations}")
        else:
            with transaction.atomic():
                location_objects = []
                for loc_name in new_locations:
                    loc_obj = get_or_create_location(loc_name)
                    if loc_obj:
                        location_objects.append(loc_obj)
                
                # Update films
                for film in original_location.film_set.all():
                    print(f"Updating film: {film.title}")
                    for new_loc in location_objects:
                        FilmLocations.objects.get_or_create(film=film, location=new_loc)
                
                # Update chapters  
                for chapter in original_location.chapter_set.all():
                    print(f"Updating chapter: {chapter.title}")
                    for new_loc in location_objects:
                        ChapterLocations.objects.get_or_create(chapter=chapter, location=new_loc)
                
                # Remove the original location
                FilmLocations.objects.filter(location=original_location).delete()
                ChapterLocations.objects.filter(location=original_location).delete()
                original_location.delete()
                print(f"✓ Fixed and removed: {original_location.name}")
                fixes_applied += 1
    
    print(f"\nApplied {fixes_applied} location fixes.")

def show_location_statistics():
    """Print comprehensive location statistics."""
    print("=== Location Statistics ===\n")
    
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
    
    print(f"Total locations: {total_locations}")
    print(f"Locations with film associations: {locations_with_films}")
    print(f"Locations with chapter associations: {locations_with_chapters}")
    print(f"Locations with any associations: {locations_with_any}")
    print(f"Orphaned locations: {total_locations - locations_with_any}")
    
    # Show top locations by usage
    print("\n=== Top 15 Most Used Locations ===")
    
    # Get locations with counts
    locations = Location.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct()
    
    # Calculate counts and sort
    location_counts = []
    for location in locations:
        films = Film.objects.filter(
            Q(locations=location) | Q(chapters__locations=location)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        location_counts.append((location, films.count()))
    
    location_counts.sort(key=lambda x: x[1], reverse=True)
    
    for location, count in location_counts[:15]:
        print(f"  {location.name}: {count} films")
    
    # Show locations that might need cleanup
    print("\n=== Locations That Might Need Cleanup ===")
    
    # Look for locations with colons (might be compound)
    compound_locations = Location.objects.filter(name__contains=':')
    if compound_locations:
        print(f"\nLocations with colons (possibly compound): {compound_locations.count()}")
        for loc in compound_locations[:10]:
            film_count = FilmLocations.objects.filter(location=loc).count()
            chapter_count = ChapterLocations.objects.filter(location=loc).count()
            print(f"  - {loc.name} (Films: {film_count}, Chapters: {chapter_count})")
    
    # Look for very similar locations
    print("\n=== Similar Location Names ===")
    location_names = list(Location.objects.values_list('name', flat=True))
    similar_found = False
    
    for i, name1 in enumerate(location_names):
        for name2 in location_names[i+1:]:
            # Simple similarity check
            if (name1.lower() in name2.lower() or name2.lower() in name1.lower()) and name1 != name2:
                if not similar_found:
                    print("Found similar location names:")
                    similar_found = True
                print(f"  - '{name1}' <-> '{name2}'")
    
    if not similar_found:
        print("No obviously similar location names found.")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive location management tool')
    parser.add_argument('command', choices=['update-csv', 'remove-orphans', 'fix-specific', 
                                           'statistics', 'all'],
                        help='Command to run')
    parser.add_argument('--csv-file', default='location_cleanup.csv', 
                        help='CSV file for update-csv command')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.command == 'update-csv':
        process_location_cleanup(args.csv_file, dry_run=args.dry_run)
    elif args.command == 'remove-orphans':
        remove_orphaned_locations(dry_run=args.dry_run)
    elif args.command == 'fix-specific':
        fix_specific_locations(dry_run=args.dry_run)
    elif args.command == 'statistics':
        show_location_statistics()
    elif args.command == 'all':
        # Run all cleanup operations in order
        print("Running all location cleanup operations...\n")
        process_location_cleanup(args.csv_file, dry_run=args.dry_run)
        print("\n" + "="*60 + "\n")
        fix_specific_locations(dry_run=args.dry_run)
        print("\n" + "="*60 + "\n")
        remove_orphaned_locations(dry_run=args.dry_run)
        print("\n" + "="*60 + "\n")
        show_location_statistics()

if __name__ == "__main__":
    main()
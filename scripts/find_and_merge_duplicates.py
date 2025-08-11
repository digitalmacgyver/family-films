#!/usr/bin/env python3
"""
Find and Merge Duplicate Persons

This script finds people who have the same first name but one has a last name
and the other doesn't (e.g., "Doug Thompson" vs "Doug").

Usage:
    python find_and_merge_duplicates.py [--auto-merge]

Options:
    --auto-merge    Automatically merge all found duplicates without confirmation
"""

import os
import sys
import django
import argparse
import subprocess

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, FilmPeople, ChapterPeople
from collections import defaultdict

def find_potential_duplicates():
    """Find people who might be duplicates based on first name matching"""
    # Group people by first name
    first_name_groups = defaultdict(list)
    
    for person in Person.objects.all():
        if person.first_name:
            first_name_groups[person.first_name.strip()].append(person)
    
    # Find groups where one has a last name and one doesn't
    duplicates = []
    
    for first_name, people in first_name_groups.items():
        if len(people) > 1:
            # Check if we have people with and without last names
            with_last_name = [p for p in people if p.last_name and p.last_name.strip()]
            without_last_name = [p for p in people if not p.last_name or not p.last_name.strip()]
            
            if with_last_name and without_last_name:
                # We found potential duplicates
                for person_with in with_last_name:
                    for person_without in without_last_name:
                        duplicates.append((person_with, person_without))
    
    return duplicates

def show_person_details(person):
    """Show details about a person"""
    film_count = FilmPeople.objects.filter(person=person).count()
    chapter_count = ChapterPeople.objects.filter(person=person).count()
    return f"ID {person.id}: '{person.first_name} {person.last_name}' - {film_count} films, {chapter_count} chapters"

def main():
    parser = argparse.ArgumentParser(description='Find and merge duplicate persons')
    parser.add_argument('--auto-merge', action='store_true', 
                        help='Automatically merge all found duplicates without confirmation')
    
    args = parser.parse_args()
    
    print("=== FINDING POTENTIAL DUPLICATE PERSONS ===\n")
    
    duplicates = find_potential_duplicates()
    
    if not duplicates:
        print("No potential duplicates found!")
        return 0
    
    print(f"Found {len(duplicates)} potential duplicate pairs:\n")
    
    for i, (person_with, person_without) in enumerate(duplicates, 1):
        print(f"{i}. Potential duplicate:")
        print(f"   Keep:   {show_person_details(person_with)}")
        print(f"   Remove: {show_person_details(person_without)}")
        print()
    
    if args.auto_merge:
        print("=== AUTO-MERGING ALL DUPLICATES ===\n")
        
        for person_with, person_without in duplicates:
            print(f"\nMerging {person_without.id} into {person_with.id}...")
            
            # Call the merge script
            cmd = ['python', 'scripts/merge_specific_persons.py', 
                   str(person_with.id), str(person_without.id)]
            
            # Create a process with 'y' as input to confirm
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            # Send 'y' to confirm the merge
            stdout, stderr = process.communicate(input='y\n')
            
            if process.returncode == 0:
                print("✓ Merge successful")
            else:
                print(f"✗ Merge failed: {stderr}")
    
    else:
        print("\nTo merge these duplicates, you can:")
        print("1. Run this script with --auto-merge to merge all at once")
        print("2. Manually merge specific pairs using:")
        print("   python scripts/merge_specific_persons.py <keep_id> <remove_id>")
        
        print("\nExample commands:")
        for person_with, person_without in duplicates[:3]:  # Show first 3 examples
            print(f"   python scripts/merge_specific_persons.py {person_with.id} {person_without.id}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
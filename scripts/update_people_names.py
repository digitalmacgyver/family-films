#!/usr/bin/env python
"""
Script to update people names in the database - adding last names to first-name-only entries.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person
from django.db import transaction

def update_person_names():
    """Update specific people to add last names."""
    
    # Define the updates
    updates = [
        ("Bob", "Bob", "Lindner"),
        ("David", "David", "Myer"),
        ("Irwin", "Irwin", "Wren"),
        ("Oscar", "Oscar", "Myre"),
        ("Stan", "Stan", "Wren"),
        ("Victor", "Victor", "Beattie"),
    ]
    
    print("Updating people names in the database...\n")
    
    with transaction.atomic():
        for current_first, new_first, new_last in updates:
            # Find people with just the first name and empty last name
            people = Person.objects.filter(
                first_name=current_first,
                last_name=""
            )
            
            if people.exists():
                count = people.count()
                print(f"Found {count} person(s) named '{current_first}' with no last name")
                
                for person in people:
                    old_name = person.full_name()
                    person.first_name = new_first
                    person.last_name = new_last
                    person.save()
                    new_name = person.full_name()
                    print(f"  ✓ Updated: '{old_name}' → '{new_name}' (ID: {person.id})")
            else:
                print(f"No person found with first_name='{current_first}' and empty last name")
    
    print("\nName updates complete!")

def show_people_summary():
    """Show a summary of people with just first names."""
    print("\n=== People with only first names ===")
    people_with_no_last_name = Person.objects.filter(last_name="").order_by('first_name')
    
    if people_with_no_last_name.exists():
        print(f"Found {people_with_no_last_name.count()} people with no last name:")
        for person in people_with_no_last_name[:20]:  # Show first 20
            print(f"  - {person.first_name} (ID: {person.id})")
        if people_with_no_last_name.count() > 20:
            print(f"  ... and {people_with_no_last_name.count() - 20} more")
    else:
        print("No people found with empty last names")

if __name__ == "__main__":
    show_people_summary()
    print("\n" + "="*50 + "\n")
    update_person_names()
    print("\n" + "="*50 + "\n")
    show_people_summary()
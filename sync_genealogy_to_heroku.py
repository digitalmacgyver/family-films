#!/usr/bin/env python
"""
Script to sync genealogy data to Heroku production.
This script reads the genealogy_sync_data.json and updates production.
"""
import json
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person

def sync_genealogy_data():
    # Load genealogy data from JSON
    data_file = 'genealogy_sync_data.json'
    if not os.path.exists(data_file):
        print(f'ERROR: {data_file} not found')
        return
        
    with open(data_file, 'r') as f:
        genealogy_data = json.load(f)
    
    print('=== SYNCING GENEALOGY DATA TO PRODUCTION ==='
    print(f'Processing {len(genealogy_data)} people...')
    
    stats = {
        'found': 0,
        'updated': 0,
        'relationships_added': 0,
        'notes_added': 0,
        'not_found': 0
    }
    
    for person_data in genealogy_data:
        pk = person_data['pk']
        
        try:
            # Find matching person in production
            person = Person.objects.get(pk=pk)
            stats['found'] += 1
            
            updated = False
            
            # Update father relationship
            father_pk = person_data['father_pk']
            if father_pk and not person.father:
                try:
                    father = Person.objects.get(pk=father_pk)
                    person.father = father
                    updated = True
                    stats['relationships_added'] += 1
                    print(f'  ✓ Added father {father.full_name()} to {person.full_name()}')
                except Person.DoesNotExist:
                    print(f'  ⚠ Father pk:{father_pk} not found for {person.full_name()}')
            
            # Update mother relationship  
            mother_pk = person_data['mother_pk']
            if mother_pk and not person.mother:
                try:
                    mother = Person.objects.get(pk=mother_pk)
                    person.mother = mother
                    updated = True
                    stats['relationships_added'] += 1
                    print(f'  ✓ Added mother {mother.full_name()} to {person.full_name()}')
                except Person.DoesNotExist:
                    print(f'  ⚠ Mother pk:{mother_pk} not found for {person.full_name()}')
            
            # Update spouse relationship
            spouse_pk = person_data['spouse_pk']
            if spouse_pk and not person.spouse:
                try:
                    spouse = Person.objects.get(pk=spouse_pk)
                    person.spouse = spouse
                    updated = True
                    stats['relationships_added'] += 1
                    print(f'  ✓ Added spouse {spouse.full_name()} to {person.full_name()}')
                except Person.DoesNotExist:
                    print(f'  ⚠ Spouse pk:{spouse_pk} not found for {person.full_name()}')
            
            # Update notes/biography
            notes = person_data.get('notes', '')
            if notes and not person.notes:
                person.notes = notes
                updated = True
                stats['notes_added'] += 1
                print(f'  ✓ Added biography notes to {person.full_name()}')
            
            # Save if updated
            if updated:
                person.save()
                stats['updated'] += 1
                
        except Person.DoesNotExist:
            stats['not_found'] += 1
            print(f'  ⚠ Person pk:{pk} not found in production')
    
    print()
    print('=== SYNC COMPLETE ===')
    print(f'People found in production: {stats["found"]}')
    print(f'People updated: {stats["updated"]}')
    print(f'Relationships added: {stats["relationships_added"]}')
    print(f'Biographies added: {stats["notes_added"]}')
    print(f'People not found: {stats["not_found"]}')
    
    # Final verification
    print()
    print('=== FINAL VERIFICATION ===')
    people_with_father = Person.objects.filter(father__isnull=False).count()
    people_with_mother = Person.objects.filter(mother__isnull=False).count()
    people_with_spouse = Person.objects.filter(spouse__isnull=False).count()
    people_with_notes = Person.objects.filter(notes__isnull=False).exclude(notes='').count()
    
    print(f'People with father: {people_with_father}')
    print(f'People with mother: {people_with_mother}')
    print(f'People with spouse: {people_with_spouse}')
    print(f'People with biography notes: {people_with_notes}')

if __name__ == "__main__":
    sync_genealogy_data()
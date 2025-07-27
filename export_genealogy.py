#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person

print('=== EXPORTING LOCAL GENEALOGY DATA ===')

# Get all local people with their genealogy data
local_people = []
for person in Person.objects.all().order_by('pk'):
    local_people.append({
        'pk': person.pk,
        'first_name': person.first_name,
        'last_name': person.last_name,
        'father_pk': person.father.pk if person.father else None,
        'mother_pk': person.mother.pk if person.mother else None,
        'spouse_pk': person.spouse.pk if person.spouse else None,
        'notes': person.notes,
        'birth_date': person.birth_date.isoformat() if person.birth_date else None,
        'death_date': person.death_date.isoformat() if person.death_date else None,
        'hayward_index': person.hayward_index
    })

# Save to file
with open('backups/local_genealogy_data.json', 'w') as f:
    json.dump(local_people, f, indent=2)

print(f'Exported {len(local_people)} people with genealogy data')
print('Sample relationships:')
count = 0
for person_data in local_people:
    if person_data['father_pk'] or person_data['mother_pk'] or person_data['spouse_pk']:
        if count >= 5:
            break
        rels = []
        if person_data['father_pk']: 
            rels.append(f'F:{person_data["father_pk"]}')
        if person_data['mother_pk']: 
            rels.append(f'M:{person_data["mother_pk"]}')  
        if person_data['spouse_pk']: 
            rels.append(f'S:{person_data["spouse_pk"]}')
        print(f'  {person_data["first_name"]} {person_data["last_name"]} - {", ".join(rels)}')
        count += 1

print('Export complete!')
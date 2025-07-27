#!/usr/bin/env python3
"""
Comprehensive Genealogy Management Tool

This script consolidates all genealogy-related functionality:
- Export genealogy data from local development database
- Sync genealogy data to Heroku production
- Sync genealogy data to production environments
- Validate genealogy relationships and data integrity
- Generate genealogy reports and statistics

This tool handles family tree relationships (father, mother, spouse, children)
and biographical data (notes, birth/death dates, indexes) separately from
the main film metadata to allow independent genealogy data management.
"""

import os
import sys
import django
import json
import argparse
from datetime import datetime
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Person
from django.db import transaction
from django.db.models import Q

def export_genealogy_data(output_file=None, include_stats=True):
    """Export all genealogy data from local development database."""
    print('=== EXPORTING LOCAL GENEALOGY DATA ===\n')
    
    if output_file is None:
        output_file = 'backups/local_genealogy_data.json'
    
    # Ensure backups directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Get all local people with their genealogy data
    local_people = []
    for person in Person.objects.all().order_by('pk'):
        person_data = {
            'pk': person.pk,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'father_pk': person.father.pk if person.father else None,
            'mother_pk': person.mother.pk if person.mother else None,
            'spouse_pk': person.spouse.pk if person.spouse else None,
            'notes': person.notes if hasattr(person, 'notes') else None,
            'birth_date': person.birth_date.isoformat() if hasattr(person, 'birth_date') and person.birth_date else None,
            'death_date': person.death_date.isoformat() if hasattr(person, 'death_date') and person.death_date else None,
            'hayward_index': person.hayward_index if hasattr(person, 'hayward_index') else None
        }
        local_people.append(person_data)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(local_people, f, indent=2)
    
    print(f'✓ Exported {len(local_people)} people with genealogy data to {output_file}')
    
    if include_stats:
        print_genealogy_statistics(local_people)
    
    return output_file

def print_genealogy_statistics(people_data):
    """Print statistics about genealogy data."""
    print('\n=== GENEALOGY DATA STATISTICS ===')
    
    total_people = len(people_data)
    with_father = sum(1 for p in people_data if p['father_pk'])
    with_mother = sum(1 for p in people_data if p['mother_pk']) 
    with_spouse = sum(1 for p in people_data if p['spouse_pk'])
    with_notes = sum(1 for p in people_data if p['notes'])
    with_birth_date = sum(1 for p in people_data if p['birth_date'])
    with_death_date = sum(1 for p in people_data if p['death_date'])
    with_hayward_index = sum(1 for p in people_data if p['hayward_index'])
    
    print(f'Total people: {total_people}')
    print(f'People with father: {with_father} ({with_father/total_people*100:.1f}%)')
    print(f'People with mother: {with_mother} ({with_mother/total_people*100:.1f}%)')
    print(f'People with spouse: {with_spouse} ({with_spouse/total_people*100:.1f}%)')
    print(f'People with biography notes: {with_notes} ({with_notes/total_people*100:.1f}%)')
    print(f'People with birth date: {with_birth_date} ({with_birth_date/total_people*100:.1f}%)')
    print(f'People with death date: {with_death_date} ({with_death_date/total_people*100:.1f}%)')
    print(f'People with Hayward index: {with_hayward_index} ({with_hayward_index/total_people*100:.1f}%)')
    
    # Sample relationships
    print('\n=== SAMPLE RELATIONSHIPS ===')
    count = 0
    for person_data in people_data:
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

def sync_genealogy_to_production(data_file=None, dry_run=False):
    """Sync genealogy data to production environment."""
    print('=== SYNCING GENEALOGY DATA TO PRODUCTION ===\n')
    
    # Determine data file to use
    if data_file is None:
        # Try multiple locations
        possible_files = [
            'genealogy_sync_data.json',
            'backups/local_genealogy_data.json',
            'backups/genealogy_sync_data.json'
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                data_file = file_path
                break
        
        if data_file is None:
            print('ERROR: No genealogy data file found')
            print('Tried locations:')
            for path in possible_files:
                print(f'  - {path}')
            return False
    
    if not os.path.exists(data_file):
        print(f'ERROR: Data file not found: {data_file}')
        return False
    
    # Load genealogy data
    with open(data_file, 'r') as f:
        genealogy_data = json.load(f)
    
    print(f'Loaded genealogy data from: {data_file}')
    print(f'Processing {len(genealogy_data)} people...')
    
    if dry_run:
        print('[DRY RUN] No changes will be made\n')
    
    stats = {
        'found': 0,
        'updated': 0,
        'relationships_added': 0,
        'notes_added': 0,
        'dates_added': 0,
        'not_found': 0
    }
    
    with transaction.atomic():
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
                        if not dry_run:
                            person.father = father
                            updated = True
                        stats['relationships_added'] += 1
                        print(f'  ✓ Added father {father.first_name} {father.last_name} to {person.first_name} {person.last_name}')
                    except Person.DoesNotExist:
                        print(f'  ⚠ Father pk:{father_pk} not found for {person.first_name} {person.last_name}')
                
                # Update mother relationship  
                mother_pk = person_data['mother_pk']
                if mother_pk and not person.mother:
                    try:
                        mother = Person.objects.get(pk=mother_pk)
                        if not dry_run:
                            person.mother = mother
                            updated = True
                        stats['relationships_added'] += 1
                        print(f'  ✓ Added mother {mother.first_name} {mother.last_name} to {person.first_name} {person.last_name}')
                    except Person.DoesNotExist:
                        print(f'  ⚠ Mother pk:{mother_pk} not found for {person.first_name} {person.last_name}')
                
                # Update spouse relationship
                spouse_pk = person_data['spouse_pk']
                if spouse_pk and not person.spouse:
                    try:
                        spouse = Person.objects.get(pk=spouse_pk)
                        if not dry_run:
                            person.spouse = spouse
                            updated = True
                        stats['relationships_added'] += 1
                        print(f'  ✓ Added spouse {spouse.first_name} {spouse.last_name} to {person.first_name} {person.last_name}')
                    except Person.DoesNotExist:
                        print(f'  ⚠ Spouse pk:{spouse_pk} not found for {person.first_name} {person.last_name}')
                
                # Update notes/biography
                notes = person_data.get('notes', '')
                if notes and (not hasattr(person, 'notes') or not person.notes):
                    if not dry_run:
                        person.notes = notes
                        updated = True
                    stats['notes_added'] += 1
                    print(f'  ✓ Added biography notes to {person.first_name} {person.last_name}')
                
                # Update birth/death dates if available
                birth_date = person_data.get('birth_date')
                death_date = person_data.get('death_date')
                if birth_date or death_date:
                    if birth_date and hasattr(person, 'birth_date') and not person.birth_date:
                        if not dry_run:
                            from datetime import datetime
                            person.birth_date = datetime.fromisoformat(birth_date).date()
                            updated = True
                        stats['dates_added'] += 1
                        print(f'  ✓ Added birth date to {person.first_name} {person.last_name}')
                    
                    if death_date and hasattr(person, 'death_date') and not person.death_date:
                        if not dry_run:
                            from datetime import datetime
                            person.death_date = datetime.fromisoformat(death_date).date()
                            updated = True
                        stats['dates_added'] += 1
                        print(f'  ✓ Added death date to {person.first_name} {person.last_name}')
                
                # Save if updated
                if updated and not dry_run:
                    person.save()
                    stats['updated'] += 1
                    
            except Person.DoesNotExist:
                stats['not_found'] += 1
                print(f'  ⚠ Person pk:{pk} ({person_data["first_name"]} {person_data["last_name"]}) not found in production')
    
    print()
    print('=== SYNC COMPLETE ===')
    print(f'People found in production: {stats["found"]}')
    print(f'People updated: {stats["updated"]}')
    print(f'Relationships added: {stats["relationships_added"]}')
    print(f'Biographies added: {stats["notes_added"]}')
    print(f'Dates added: {stats["dates_added"]}')
    print(f'People not found: {stats["not_found"]}')
    
    if not dry_run:
        # Final verification
        print()
        print('=== FINAL VERIFICATION ===')
        people_with_father = Person.objects.filter(father__isnull=False).count()
        people_with_mother = Person.objects.filter(mother__isnull=False).count()
        people_with_spouse = Person.objects.filter(spouse__isnull=False).count()
        people_with_notes = Person.objects.filter(notes__isnull=False).exclude(notes='').count() if hasattr(Person.objects.first(), 'notes') else 0
        
        print(f'People with father: {people_with_father}')
        print(f'People with mother: {people_with_mother}')
        print(f'People with spouse: {people_with_spouse}')
        print(f'People with biography notes: {people_with_notes}')
    
    return True

def validate_genealogy_integrity():
    """Validate genealogy data integrity and report issues."""
    print('=== GENEALOGY DATA INTEGRITY VALIDATION ===\n')
    
    all_people = Person.objects.all()
    issues = []
    
    print(f'Validating {all_people.count()} people...')
    
    for person in all_people:
        person_issues = []
        
        # Check for circular relationships
        if person.father and person.father == person:
            person_issues.append('Self-referential father relationship')
        
        if person.mother and person.mother == person:
            person_issues.append('Self-referential mother relationship')
        
        if person.spouse and person.spouse == person:
            person_issues.append('Self-referential spouse relationship')
        
        # Check for impossible relationships
        if person.father and person.mother and person.father == person.mother:
            person_issues.append('Father and mother are the same person')
        
        # Check for mutual spouse relationships
        if person.spouse and person.spouse.spouse != person:
            person_issues.append(f'Spouse relationship not mutual with {person.spouse.first_name} {person.spouse.last_name}')
        
        # Check for generational loops (simplified check)
        if person.father and person.father.father == person:
            person_issues.append('Generational loop detected (grandfather is self)')
        
        if person.mother and person.mother.mother == person:
            person_issues.append('Generational loop detected (grandmother is self)')
        
        if person_issues:
            issues.append((person, person_issues))
    
    if issues:
        print(f'Found {len(issues)} people with integrity issues:\n')
        for person, person_issues in issues:
            print(f'{person.first_name} {person.last_name} (ID: {person.pk}):')
            for issue in person_issues:
                print(f'  - {issue}')
            print()
    else:
        print('✓ No integrity issues found')
    
    # Generate statistics
    print('=== GENEALOGY STATISTICS ===')
    total_people = all_people.count()
    people_with_father = Person.objects.filter(father__isnull=False).count()
    people_with_mother = Person.objects.filter(mother__isnull=False).count()
    people_with_spouse = Person.objects.filter(spouse__isnull=False).count()
    people_with_both_parents = Person.objects.filter(father__isnull=False, mother__isnull=False).count()
    people_with_notes = Person.objects.filter(notes__isnull=False).exclude(notes='').count() if hasattr(Person.objects.first(), 'notes') else 0
    
    print(f'Total people: {total_people}')
    print(f'People with father: {people_with_father} ({people_with_father/total_people*100:.1f}%)')
    print(f'People with mother: {people_with_mother} ({people_with_mother/total_people*100:.1f}%)')
    print(f'People with both parents: {people_with_both_parents} ({people_with_both_parents/total_people*100:.1f}%)')
    print(f'People with spouse: {people_with_spouse} ({people_with_spouse/total_people*100:.1f}%)')
    print(f'People with biography: {people_with_notes} ({people_with_notes/total_people*100:.1f}%)')
    
    return len(issues) == 0

def generate_genealogy_report(output_file=None):
    """Generate comprehensive genealogy report."""
    print('=== GENERATING GENEALOGY REPORT ===\n')
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'backups/genealogy_report_{timestamp}.json'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    all_people = Person.objects.all()
    
    report = {
        'generation_date': datetime.now().isoformat(),
        'total_people': all_people.count(),
        'people': [],
        'families': [],
        'statistics': {}
    }
    
    # Export people data
    for person in all_people.order_by('pk'):
        person_data = {
            'pk': person.pk,
            'name': f'{person.first_name} {person.last_name}',
            'first_name': person.first_name,
            'last_name': person.last_name,
            'father': {
                'pk': person.father.pk,
                'name': f'{person.father.first_name} {person.father.last_name}'
            } if person.father else None,
            'mother': {
                'pk': person.mother.pk,
                'name': f'{person.mother.first_name} {person.mother.last_name}'
            } if person.mother else None,
            'spouse': {
                'pk': person.spouse.pk,
                'name': f'{person.spouse.first_name} {person.spouse.last_name}'
            } if person.spouse else None,
            'children': [],
            'has_biography': bool(getattr(person, 'notes', None)),
            'film_associations': person.film_set.count() if hasattr(person, 'film_set') else 0,
            'chapter_associations': person.chapter_set.count() if hasattr(person, 'chapter_set') else 0
        }
        
        # Find children
        children = Person.objects.filter(Q(father=person) | Q(mother=person))
        for child in children:
            person_data['children'].append({
                'pk': child.pk,
                'name': f'{child.first_name} {child.last_name}'
            })
        
        report['people'].append(person_data)
    
    # Generate statistics
    report['statistics'] = {
        'people_with_father': Person.objects.filter(father__isnull=False).count(),
        'people_with_mother': Person.objects.filter(mother__isnull=False).count(),
        'people_with_spouse': Person.objects.filter(spouse__isnull=False).count(),
        'people_with_both_parents': Person.objects.filter(father__isnull=False, mother__isnull=False).count(),
        'people_with_biography': Person.objects.filter(notes__isnull=False).exclude(notes='').count() if hasattr(Person.objects.first(), 'notes') else 0,
        'people_with_children': len([p for p in report['people'] if p['children']]),
        'largest_family_size': max(len(p['children']) for p in report['people']) if report['people'] else 0
    }
    
    # Save report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f'✓ Generated genealogy report: {output_file}')
    print(f'  Total people: {report["total_people"]}')
    print(f'  People with children: {report["statistics"]["people_with_children"]}')
    print(f'  Largest family: {report["statistics"]["largest_family_size"]} children')
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Comprehensive genealogy management tool')
    parser.add_argument('command', choices=['export', 'sync', 'validate', 'report', 'all'],
                        help='Command to run')
    parser.add_argument('--data-file', help='Genealogy data file for sync command')
    parser.add_argument('--output-file', help='Output file for export/report commands')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes (sync only)')
    
    args = parser.parse_args()
    
    if args.command == 'export':
        export_genealogy_data(args.output_file)
    
    elif args.command == 'sync':
        sync_genealogy_to_production(args.data_file, args.dry_run)
    
    elif args.command == 'validate':
        validate_genealogy_integrity()
    
    elif args.command == 'report':
        generate_genealogy_report(args.output_file)
    
    elif args.command == 'all':
        print("Running comprehensive genealogy operations...\n")
        
        # Export current data
        print("=" * 60)
        export_file = export_genealogy_data()
        
        print("\n" + "=" * 60)
        validate_genealogy_integrity()
        
        print("\n" + "=" * 60)
        generate_genealogy_report()
        
        print("\n" + "=" * 60)
        print("All genealogy operations completed!")

if __name__ == "__main__":
    main()
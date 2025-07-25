from django.core.management.base import BaseCommand
from main.models import Person
import json

class Command(BaseCommand):
    help = 'Sync genealogy data to production database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data',
            type=str,
            help='JSON string containing genealogy data',
            required=True
        )

    def handle(self, *args, **options):
        try:
            genealogy_data = json.loads(options['data'])
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON data: {e}'))
            return

        self.stdout.write('=== SYNCING GENEALOGY DATA TO PRODUCTION ===')
        self.stdout.write(f'Processing {len(genealogy_data)} people...')
        
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
                        self.stdout.write(f'  ✓ Added father {father.full_name()} to {person.full_name()}')
                    except Person.DoesNotExist:
                        self.stdout.write(f'  ⚠ Father pk:{father_pk} not found for {person.full_name()}')
                
                # Update mother relationship  
                mother_pk = person_data['mother_pk']
                if mother_pk and not person.mother:
                    try:
                        mother = Person.objects.get(pk=mother_pk)
                        person.mother = mother
                        updated = True
                        stats['relationships_added'] += 1
                        self.stdout.write(f'  ✓ Added mother {mother.full_name()} to {person.full_name()}')
                    except Person.DoesNotExist:
                        self.stdout.write(f'  ⚠ Mother pk:{mother_pk} not found for {person.full_name()}')
                
                # Update spouse relationship
                spouse_pk = person_data['spouse_pk']
                if spouse_pk and not person.spouse:
                    try:
                        spouse = Person.objects.get(pk=spouse_pk)
                        person.spouse = spouse
                        updated = True
                        stats['relationships_added'] += 1
                        self.stdout.write(f'  ✓ Added spouse {spouse.full_name()} to {person.full_name()}')
                    except Person.DoesNotExist:
                        self.stdout.write(f'  ⚠ Spouse pk:{spouse_pk} not found for {person.full_name()}')
                
                # Update notes/biography
                notes = person_data.get('notes', '')
                if notes and not person.notes:
                    person.notes = notes
                    updated = True
                    stats['notes_added'] += 1
                    self.stdout.write(f'  ✓ Added biography notes to {person.full_name()}')
                
                # Save if updated
                if updated:
                    person.save()
                    stats['updated'] += 1
                    
            except Person.DoesNotExist:
                stats['not_found'] += 1
                self.stdout.write(f'  ⚠ Person pk:{pk} not found in production')
        
        self.stdout.write('')
        self.stdout.write('=== SYNC COMPLETE ===')
        self.stdout.write(f'People found in production: {stats["found"]}')
        self.stdout.write(f'People updated: {stats["updated"]}')
        self.stdout.write(f'Relationships added: {stats["relationships_added"]}')
        self.stdout.write(f'Biographies added: {stats["notes_added"]}')
        self.stdout.write(f'People not found: {stats["not_found"]}')
        
        # Final verification
        self.stdout.write('')
        self.stdout.write('=== FINAL VERIFICATION ===')
        people_with_father = Person.objects.filter(father__isnull=False).count()
        people_with_mother = Person.objects.filter(mother__isnull=False).count()
        people_with_spouse = Person.objects.filter(spouse__isnull=False).count()
        people_with_notes = Person.objects.filter(notes__isnull=False).exclude(notes='').count()
        
        self.stdout.write(f'People with father: {people_with_father}')
        self.stdout.write(f'People with mother: {people_with_mother}')
        self.stdout.write(f'People with spouse: {people_with_spouse}')
        self.stdout.write(f'People with biography notes: {people_with_notes}')
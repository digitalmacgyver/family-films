import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.serializers import deserialize
from main.models import (
    Film, Chapter, Person, Location, Tag, DigitalReel,
    FilmPeople, FilmLocations, FilmTags,
    ChapterPeople, ChapterLocations, ChapterTags
)


class Command(BaseCommand):
    help = 'Import all film data from JSON export file'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='JSON file to import from'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing data before import (DANGEROUS!)'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        dry_run = options['dry_run']
        clear_existing = options['clear_existing']
        
        if not os.path.exists(json_file):
            raise CommandError(f'JSON file not found: {json_file}')
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {json_file}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        if clear_existing and not dry_run:
            self.stdout.write(self.style.WARNING('WARNING: This will clear ALL existing data!'))
            confirm = input('Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write('Import cancelled.')
                return
        
        # Load data
        with open(json_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # Verify data structure
        self.verify_export_data(export_data)
        
        # Import in transaction
        with transaction.atomic():
            stats = self.import_all_data(export_data, dry_run, clear_existing)
            
            if dry_run:
                # Rollback transaction for dry run
                transaction.set_rollback(True)
        
        # Print statistics
        self.print_import_stats(stats)
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run completed - no data was actually imported'))
        else:
            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

    def verify_export_data(self, export_data):
        """Verify the export data has expected structure"""
        expected_keys = [
            'people', 'locations', 'tags', 'digital_reels', 'films', 'chapters',
            'film_people', 'film_locations', 'film_tags',
            'chapter_people', 'chapter_locations', 'chapter_tags', 'metadata'
        ]
        
        missing_keys = set(expected_keys) - set(export_data.keys())
        if missing_keys:
            self.stdout.write(
                self.style.WARNING(f'Missing keys in export data: {missing_keys}')
            )
        
        if 'metadata' in export_data:
            metadata = export_data['metadata']
            self.stdout.write(f'Export version: {metadata.get("export_version", "unknown")}')
            self.stdout.write(f'Total records: {metadata.get("total_records", "unknown")}')

    def import_all_data(self, export_data, dry_run, clear_existing):
        """Import all data in correct dependency order"""
        stats = {}
        
        if clear_existing and not dry_run:
            self.clear_all_data()
            self.stdout.write(self.style.WARNING('Existing data cleared'))
        
        # Import in dependency order
        import_order = [
            ('people', Person),
            ('locations', Location),
            ('tags', Tag),
            ('digital_reels', DigitalReel),
            ('films', Film),
            ('chapters', Chapter),
            ('film_people', FilmPeople),
            ('film_locations', FilmLocations),
            ('film_tags', FilmTags),
            ('chapter_people', ChapterPeople),
            ('chapter_locations', ChapterLocations),
            ('chapter_tags', ChapterTags),
        ]
        
        for key, model_class in import_order:
            if key in export_data:
                count = self.import_model_data(
                    key, export_data[key], model_class, dry_run
                )
                stats[key] = count
            else:
                stats[key] = 0
                self.stdout.write(f'No data found for {key}')
        
        return stats

    def import_model_data(self, model_name, data, model_class, dry_run):
        """Import data for a single model"""
        if not data:
            self.stdout.write(f'Importing {model_name}: 0 records')
            return 0
        
        self.stdout.write(f'Importing {model_name}: {len(data)} records...')
        
        if dry_run:
            return len(data)
        
        try:
            # Convert back to Django serializer format
            django_format = json.dumps(data)
            
            # Use Django's deserializer
            objects = list(deserialize('json', django_format))
            
            imported_count = 0
            for obj in objects:
                try:
                    # Check if object already exists (by primary key)
                    existing = None
                    if hasattr(obj.object, 'pk') and obj.object.pk:
                        try:
                            existing = model_class.objects.get(pk=obj.object.pk)
                        except model_class.DoesNotExist:
                            pass
                    
                    if existing:
                        # Update existing object
                        for field in obj.object._meta.fields:
                            setattr(existing, field.name, getattr(obj.object, field.name))
                        existing.save()
                    else:
                        # Save new object
                        obj.save()
                    
                    imported_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing {model_name} record: {str(e)}')
                    )
            
            self.stdout.write(f'  ✓ Successfully imported {imported_count} {model_name} records')
            return imported_count
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing {model_name}: {str(e)}')
            )
            return 0

    def clear_all_data(self):
        """Clear all existing data (in reverse dependency order)"""
        self.stdout.write('Clearing existing data...')
        
        # Delete in reverse dependency order
        ChapterTags.objects.all().delete()
        ChapterLocations.objects.all().delete()
        ChapterPeople.objects.all().delete()
        FilmTags.objects.all().delete()
        FilmLocations.objects.all().delete()
        FilmPeople.objects.all().delete()
        Chapter.objects.all().delete()
        Film.objects.all().delete()
        DigitalReel.objects.all().delete()
        Tag.objects.all().delete()
        Location.objects.all().delete()
        Person.objects.all().delete()

    def print_import_stats(self, stats):
        """Print import statistics"""
        self.stdout.write(self.style.SUCCESS('\n=== Import Statistics ==='))
        
        total_imported = 0
        for key, count in stats.items():
            self.stdout.write(f'{key}: {count} records')
            total_imported += count
        
        self.stdout.write(f'\nTotal records imported: {total_imported}')
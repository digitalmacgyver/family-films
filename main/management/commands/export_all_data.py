import json
import os
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from main.models import (
    Film, Chapter, Person, Location, Tag, DigitalReel,
    FilmPeople, FilmLocations, FilmTags,
    ChapterPeople, ChapterLocations, ChapterTags
)


class Command(BaseCommand):
    help = 'Export all film data to JSON file for transfer to production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='family_films_export.json',
            help='Output JSON file name'
        )
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Pretty print JSON output'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        pretty_print = options['pretty']
        
        self.stdout.write(self.style.SUCCESS('Starting data export...'))
        
        # Export all models in dependency order
        export_data = {}
        
        # Core entities first
        self.stdout.write('Exporting core entities...')
        export_data['people'] = self.export_model(Person, 'people')
        export_data['locations'] = self.export_model(Location, 'locations')
        export_data['tags'] = self.export_model(Tag, 'tags')
        export_data['digital_reels'] = self.export_model(DigitalReel, 'digital_reels')
        
        # Films and chapters
        self.stdout.write('Exporting films...')
        export_data['films'] = self.export_model(Film, 'films')
        
        self.stdout.write('Exporting chapters...')
        export_data['chapters'] = self.export_model(Chapter, 'chapters')
        
        # Relationship tables
        self.stdout.write('Exporting relationships...')
        export_data['film_people'] = self.export_model(FilmPeople, 'film_people')
        export_data['film_locations'] = self.export_model(FilmLocations, 'film_locations')
        export_data['film_tags'] = self.export_model(FilmTags, 'film_tags')
        export_data['chapter_people'] = self.export_model(ChapterPeople, 'chapter_people')
        export_data['chapter_locations'] = self.export_model(ChapterLocations, 'chapter_locations')
        export_data['chapter_tags'] = self.export_model(ChapterTags, 'chapter_tags')
        
        # Add metadata
        export_data['metadata'] = {
            'export_version': '1.0',
            'total_records': sum(len(data) for data in export_data.values() if isinstance(data, list)),
            'models_exported': list(export_data.keys())
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty_print:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(export_data, f, ensure_ascii=False, default=str)
        
        # Print statistics
        self.print_export_stats(export_data, output_file)
        
        self.stdout.write(
            self.style.SUCCESS(f'Export completed successfully! File: {output_file}')
        )

    def export_model(self, model_class, model_name):
        """Export a single model to JSON-serializable format"""
        try:
            queryset = model_class.objects.all()
            count = queryset.count()
            
            if count == 0:
                self.stdout.write(f'  - {model_name}: 0 records')
                return []
            
            # Use Django's serializer but convert to dict for easier handling
            serialized = serialize('json', queryset)
            data = json.loads(serialized)
            
            self.stdout.write(f'  - {model_name}: {count} records')
            return data
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error exporting {model_name}: {str(e)}')
            )
            return []

    def print_export_stats(self, export_data, output_file):
        """Print detailed export statistics"""
        self.stdout.write(self.style.SUCCESS('\n=== Export Statistics ==='))
        
        total_records = 0
        for key, data in export_data.items():
            if key == 'metadata':
                continue
            if isinstance(data, list):
                count = len(data)
                total_records += count
                self.stdout.write(f'{key}: {count} records')
        
        self.stdout.write(f'\nTotal records exported: {total_records}')
        
        # File size
        file_size = os.path.getsize(output_file)
        if file_size > 1024 * 1024:
            size_str = f'{file_size / (1024 * 1024):.1f} MB'
        elif file_size > 1024:
            size_str = f'{file_size / 1024:.1f} KB'
        else:
            size_str = f'{file_size} bytes'
        
        self.stdout.write(f'Export file size: {size_str}')
        self.stdout.write(f'Export file location: {os.path.abspath(output_file)}')
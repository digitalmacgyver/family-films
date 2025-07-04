import csv
from django.core.management.base import BaseCommand
from main.models import Film


class Command(BaseCommand):
    help = 'Create a CSV file for manually mapping file IDs to YouTube video IDs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-file',
            type=str,
            default='youtube_mapping.csv',
            help='Output CSV file for manual mapping'
        )

    def handle(self, *args, **options):
        output_file = options['output_file']
        
        films = Film.objects.all().order_by('file_id')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'file_id',
                'title',
                'current_youtube_id',
                'current_youtube_url',
                'new_youtube_id',
                'new_youtube_url',
                'notes'
            ])
            
            # Write film data
            for film in films:
                writer.writerow([
                    film.file_id,
                    film.title,
                    film.youtube_id,
                    film.youtube_url,
                    '',  # new_youtube_id - to be filled manually
                    '',  # new_youtube_url - to be filled manually  
                    ''   # notes
                ])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {output_file} with {films.count()} films.\n'
                f'Fill in the new_youtube_id column with actual YouTube video IDs,\n'
                f'then run: python manage.py apply_youtube_mapping {output_file}'
            )
        )
import csv
from django.core.management.base import BaseCommand, CommandError
from main.models import Film


class Command(BaseCommand):
    help = 'Apply YouTube video ID mappings from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='CSV file with YouTube mappings'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be updated'))

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                updated_count = 0
                error_count = 0
                
                for row in reader:
                    file_id = row['file_id'].strip()
                    new_youtube_id = row.get('new_youtube_id', '').strip()
                    new_youtube_url = row.get('new_youtube_url', '').strip()
                    
                    if not new_youtube_id:
                        continue  # Skip rows without new YouTube ID
                    
                    try:
                        film = Film.objects.get(file_id=file_id)
                        
                        if dry_run:
                            self.stdout.write(
                                f'Would update {file_id}: {film.youtube_id} -> {new_youtube_id}'
                            )
                        else:
                            # Update the film
                            old_youtube_id = film.youtube_id
                            film.youtube_id = new_youtube_id
                            
                            # Update URLs
                            if new_youtube_url:
                                film.youtube_url = new_youtube_url
                            else:
                                film.youtube_url = f'https://www.youtube.com/watch?v={new_youtube_id}'
                            
                            # Update thumbnail URLs
                            film.thumbnail_url = f'https://img.youtube.com/vi/{new_youtube_id}/maxresdefault.jpg'
                            film.thumbnail_high_url = f'https://img.youtube.com/vi/{new_youtube_id}/hqdefault.jpg'
                            film.thumbnail_medium_url = f'https://img.youtube.com/vi/{new_youtube_id}/mqdefault.jpg'
                            
                            film.save()
                            
                            self.stdout.write(
                                f'Updated {file_id}: {old_youtube_id} -> {new_youtube_id}'
                            )
                        
                        updated_count += 1
                        
                    except Film.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'Film not found for file_id: {file_id}')
                        )
                        error_count += 1
                        continue
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'Would update {updated_count} films')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully updated {updated_count} films')
                    )
                
                if error_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Encountered {error_count} errors')
                    )
                        
        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {e}')
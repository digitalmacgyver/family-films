import csv
from django.core.management.base import BaseCommand, CommandError
from main.models import Film


class Command(BaseCommand):
    help = 'Apply YouTube video ID mappings from matched mapping CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='CSV file with matched YouTube mappings'
        )
        parser.add_argument(
            '--confidence-filter',
            type=str,
            choices=['HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'LOW_CONFIDENCE', 'ALL'],
            default='HIGH_CONFIDENCE',
            help='Apply only mappings with specified confidence level'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        confidence_filter = options['confidence_filter']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be updated'))

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                updated_count = 0
                skipped_count = 0
                error_count = 0
                
                for row in reader:
                    confidence_level = row.get('confidence_level', '').upper().replace(' ', '_')
                    
                    # Filter by confidence level
                    if confidence_filter != 'ALL' and confidence_level != confidence_filter:
                        skipped_count += 1
                        continue
                    
                    file_id = row['file_id'].strip()
                    new_youtube_id = row.get('new_youtube_id', '').strip()
                    new_youtube_url = row.get('new_youtube_url', '').strip()
                    confidence_score = float(row.get('confidence_score', 0))
                    
                    if not new_youtube_id:
                        skipped_count += 1
                        continue
                    
                    try:
                        film = Film.objects.get(file_id=file_id)
                        
                        # Check if this YouTube ID is already used by another film
                        existing_film = Film.objects.filter(youtube_id=new_youtube_id).exclude(file_id=file_id).first()
                        if existing_film:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Skipping {file_id}: YouTube ID {new_youtube_id} already used by {existing_film.file_id}'
                                )
                            )
                            skipped_count += 1
                            continue
                        
                        if dry_run:
                            self.stdout.write(
                                f'Would update {file_id}: {film.youtube_id} -> {new_youtube_id} '
                                f'(confidence: {confidence_score:.3f})'
                            )
                        else:
                            # Update the film
                            old_youtube_id = film.youtube_id
                            film.youtube_id = new_youtube_id
                            
                            # Update URLs
                            film.youtube_url = new_youtube_url
                            
                            # Update thumbnail URLs with different qualities
                            film.thumbnail_url = f'https://img.youtube.com/vi/{new_youtube_id}/maxresdefault.jpg'
                            film.thumbnail_high_url = f'https://img.youtube.com/vi/{new_youtube_id}/hqdefault.jpg'
                            film.thumbnail_medium_url = f'https://img.youtube.com/vi/{new_youtube_id}/mqdefault.jpg'
                            
                            film.save()
                            
                            self.stdout.write(
                                f'Updated {file_id}: {old_youtube_id} -> {new_youtube_id} '
                                f'(confidence: {confidence_score:.3f})'
                            )
                        
                        updated_count += 1
                        
                    except Film.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'Film not found for file_id: {file_id}')
                        )
                        error_count += 1
                        continue
                
                # Print summary
                self.stdout.write('\n=== SUMMARY ===')
                if dry_run:
                    self.stdout.write(f'Would update: {updated_count} films')
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully updated: {updated_count} films')
                    )
                
                if skipped_count > 0:
                    self.stdout.write(f'Skipped: {skipped_count} films')
                
                if error_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Errors: {error_count} films')
                    )
                        
        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {e}')
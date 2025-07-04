import csv
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from main.models import (
    Film, Chapter, Person, Location, Tag, DigitalReel,
    FilmPeople, FilmLocations, FilmTags,
    ChapterPeople, ChapterLocations, ChapterTags
)


class Command(BaseCommand):
    help = 'Import family films data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the family_reunion_movies.csv file'
        )
        parser.add_argument(
            '--youtube-playlist',
            type=str,
            default='https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm',
            help='YouTube playlist URL'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        youtube_playlist = options['youtube_playlist']
        dry_run = options['dry_run']

        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        # Parse YouTube playlist ID
        playlist_id = self.extract_playlist_id(youtube_playlist)
        self.stdout.write(f'YouTube Playlist ID: {playlist_id}')

        # Import data
        with transaction.atomic():
            stats = self.import_csv_data(csv_file, playlist_id, dry_run)
            
            if dry_run:
                # Rollback the transaction for dry run
                transaction.set_rollback(True)

        # Print statistics
        self.print_import_stats(stats)

    def extract_playlist_id(self, url):
        """Extract playlist ID from YouTube URL"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        return query_params.get('list', [''])[0]

    def import_csv_data(self, csv_file, playlist_id, dry_run):
        """Import data from CSV file"""
        stats = {
            'films': 0,
            'chapters': 0,
            'people': 0,
            'locations': 0,
            'tags': 0,
            'errors': []
        }

        with open(csv_file, 'r', encoding='utf-8') as file:
            # Skip front matter and find the header row
            header_row_index = self.find_header_row(file)
            file.seek(0)  # Reset file pointer
            
            # Skip to header row
            for i in range(header_row_index):
                next(file)
            
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=header_row_index + 2):
                try:
                    if self.is_valid_film_row(row):
                        film_stats = self.process_film_row(row, playlist_id, dry_run)
                        self.merge_stats(stats, film_stats)
                        stats['films'] += 1
                        
                        if stats['films'] % 10 == 0:
                            self.stdout.write(f'Processed {stats["films"]} films...')
                            
                except Exception as e:
                    error_msg = f'Error processing row {row_num}: {str(e)}'
                    stats['errors'].append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

        return stats

    def find_header_row(self, file):
        """Find the row index that contains the column headers"""
        file.seek(0)
        for i, line in enumerate(file):
            if 'Filenames' in line and 'Years' in line and 'People' in line:
                return i
        return 1  # Default to row 2 (index 1) if not found

    def is_valid_film_row(self, row):
        """Check if the row contains valid film data"""
        return (row.get('Filenames', '').strip() and 
                row.get('Title', '').strip())

    def process_film_row(self, row, playlist_id, dry_run):
        """Process a single film row from CSV"""
        stats = {'chapters': 0, 'people': 0, 'locations': 0, 'tags': 0}
        
        file_id = row['Filenames'].strip()
        title = row['Title'].strip()
        
        self.stdout.write(f'Processing: {file_id} - {title}')
        
        if not dry_run:
            # Create or get film
            film, created = Film.objects.get_or_create(
                file_id=file_id,
                defaults=self.get_film_defaults(row, playlist_id)
            )
            
            if not created:
                # Update existing film
                for key, value in self.get_film_defaults(row, playlist_id).items():
                    setattr(film, key, value)
                film.save()
            
            # Process related data
            stats['people'] += self.process_people(film, row['People'])
            stats['locations'] += self.process_locations(film, row['Location'])
            stats['tags'] += self.process_tags(film, row)
            stats['chapters'] += self.process_chapters(film, row['Chapters'])
            
        else:
            # Dry run - just count what would be processed
            stats['people'] += len(self.parse_people_list(row['People']))
            stats['locations'] += len(self.parse_locations_list(row['Location']))
            stats['tags'] += len(self.extract_tags(row))
            stats['chapters'] += len(self.parse_chapters(row['Chapters']))

        return stats

    def get_film_defaults(self, row, playlist_id):
        """Get default values for Film creation"""
        file_id = row['Filenames'].strip()
        
        # Generate YouTube URL (this would need to be mapped to actual video IDs)
        # For now, using a placeholder - you'll need to map file_id to actual YouTube video IDs
        youtube_id = f"placeholder_{file_id}"  # This needs to be replaced with actual mapping
        youtube_url = f"https://www.youtube.com/watch?v={youtube_id}&list={playlist_id}"
        
        # Parse duration
        duration = self.parse_duration(row.get('Duration at 23.97 fps', ''))
        
        return {
            'title': row['Title'].strip(),
            'description': row.get('Description', '').strip(),
            'summary': row.get('Summary', '').strip(),
            'years': row.get('Years', '').strip(),
            'technical_notes': row.get('Tech Notes', '').strip(),
            'workflow_state': row.get('Workflow State', '').strip(),
            'youtube_url': youtube_url,
            'youtube_id': youtube_id,
            'thumbnail_url': f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg",
            'duration': duration,
        }

    def parse_duration(self, duration_str):
        """Parse duration string like '0:09:26' to timedelta"""
        if not duration_str.strip():
            return None
        
        try:
            parts = duration_str.strip().split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, TypeError):
            pass
        
        return None

    def process_people(self, film, people_str):
        """Process people mentioned in the film"""
        people_list = self.parse_people_list(people_str)
        count = 0
        
        for person_name in people_list:
            person = self.get_or_create_person(person_name)
            if person:
                FilmPeople.objects.get_or_create(film=film, person=person)
                count += 1
        
        return count

    def parse_people_list(self, people_str):
        """Parse people string into list of names"""
        if not people_str.strip():
            return []
        
        # Split by common delimiters and clean up
        people = re.split(r',|and|&|\n', people_str)
        people = [p.strip() for p in people if p.strip()]
        
        # Remove common descriptive text
        people = [p for p in people if not re.match(r'^(and their|with|including)', p.lower())]
        
        return people

    def get_or_create_person(self, full_name):
        """Create or get a Person object from full name"""
        if not full_name.strip():
            return None
        
        # Parse name parts
        name_parts = full_name.strip().split()
        if len(name_parts) < 2:
            first_name = name_parts[0] if name_parts else ''
            last_name = ''
        else:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
        
        # Handle special cases like "(nee Myre)"
        last_name = re.sub(r'\(nee [^)]+\)', '', last_name).strip()
        
        person, created = Person.objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            defaults={'notes': f'Imported from CSV: {full_name}'}
        )
        
        return person

    def process_locations(self, film, locations_str):
        """Process locations mentioned in the film"""
        locations_list = self.parse_locations_list(locations_str)
        count = 0
        
        for location_name in locations_list:
            location = self.get_or_create_location(location_name)
            if location:
                FilmLocations.objects.get_or_create(film=film, location=location)
                count += 1
        
        return count

    def parse_locations_list(self, locations_str):
        """Parse locations string into list of locations"""
        if not locations_str.strip():
            return []
        
        # Split by common delimiters
        locations = re.split(r',|;|\n', locations_str)
        locations = [loc.strip() for loc in locations if loc.strip()]
        
        # Clean up common prefixes
        cleaned = []
        for loc in locations:
            loc = re.sub(r'^(Locations?:?\s*)', '', loc, flags=re.IGNORECASE)
            if loc and loc not in cleaned:
                cleaned.append(loc)
        
        return cleaned

    def get_or_create_location(self, location_name):
        """Create or get a Location object"""
        if not location_name.strip():
            return None
        
        # Parse state/country info
        name = location_name.strip()
        city = ''
        state = ''
        
        # Simple parsing for "City, State" format
        if ',' in name:
            parts = [p.strip() for p in name.split(',')]
            if len(parts) == 2:
                city, state = parts
                name = f"{city}, {state}"
        
        location, created = Location.objects.get_or_create(
            name=name,
            defaults={
                'city': city,
                'state': state,
                'description': f'Imported from CSV'
            }
        )
        
        return location

    def process_tags(self, film, row):
        """Process tags from the row"""
        tags = self.extract_tags(row)
        count = 0
        
        for tag_name, category in tags:
            tag = self.get_or_create_tag(tag_name, category)
            if tag:
                FilmTags.objects.get_or_create(film=film, tag=tag)
                count += 1
        
        return count

    def extract_tags(self, row):
        """Extract tags from row columns"""
        tags = []
        
        # Process tag columns
        tag_columns = {
            'Tag: Ruth': 'people',
            'Tag: Disney': 'themes',
            'Tag: SF': 'places',
            'Tag: Needs Edit': 'other',
            'Tag: Theme Park': 'activities'
        }
        
        for col, category in tag_columns.items():
            if row.get(col, '').strip():
                tag_name = col.replace('Tag: ', '').strip()
                tags.append((tag_name, category))
        
        # Extract tags from format
        format_val = row.get('Format', '').strip()
        if format_val:
            tags.append((format_val, 'other'))
        
        return tags

    def get_or_create_tag(self, tag_name, category):
        """Create or get a Tag object"""
        if not tag_name.strip():
            return None
        
        tag, created = Tag.objects.get_or_create(
            tag=tag_name.lower(),
            defaults={
                'category': category,
                'description': f'Imported from CSV'
            }
        )
        
        return tag

    def process_chapters(self, film, chapters_str):
        """Process chapters from the chapters string"""
        chapters = self.parse_chapters(chapters_str)
        count = 0
        
        for order, (start_time, title) in enumerate(chapters):
            Chapter.objects.get_or_create(
                film=film,
                order=order + 1,
                defaults={
                    'start_time': start_time,
                    'title': title[:500],  # Truncate if too long
                    'start_time_seconds': self.parse_time_to_seconds(start_time)
                }
            )
            count += 1
        
        return count

    def parse_chapters(self, chapters_str):
        """Parse chapters string into list of (time, title) tuples"""
        if not chapters_str.strip():
            return []
        
        chapters = []
        lines = chapters_str.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match time pattern at start of line
            time_match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$', line)
            if time_match:
                time_str, title = time_match.groups()
                chapters.append((time_str, title.strip()))
        
        return chapters

    def parse_time_to_seconds(self, time_str):
        """Convert time string to seconds"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except (ValueError, IndexError):
            pass
        return 0

    def merge_stats(self, main_stats, sub_stats):
        """Merge sub-statistics into main statistics"""
        for key in ['chapters', 'people', 'locations', 'tags']:
            main_stats[key] += sub_stats.get(key, 0)

    def print_import_stats(self, stats):
        """Print import statistics"""
        self.stdout.write(self.style.SUCCESS('\n=== Import Statistics ==='))
        self.stdout.write(f'Films imported: {stats["films"]}')
        self.stdout.write(f'Chapters created: {stats["chapters"]}')
        self.stdout.write(f'People processed: {stats["people"]}')
        self.stdout.write(f'Locations processed: {stats["locations"]}')
        self.stdout.write(f'Tags processed: {stats["tags"]}')
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f'\nErrors encountered: {len(stats["errors"])}'))
            for error in stats['errors'][:10]:  # Show first 10 errors
                self.stdout.write(self.style.ERROR(f'  - {error}'))
            if len(stats['errors']) > 10:
                self.stdout.write(self.style.ERROR(f'  ... and {len(stats["errors"]) - 10} more'))
        
        self.stdout.write(self.style.SUCCESS('\nImport completed!'))
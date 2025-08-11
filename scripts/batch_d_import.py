#!/usr/bin/env python3
"""
Batch D Film Import Tool

This script imports new films from the family_movies_batchd.csv file for entries marked as "Batch D".
It cross-references with the YouTube playlist to extract metadata from video descriptions and creates
the necessary database entries for films, chapters, people, locations, and relationships.
"""

import os
import sys
import django
import csv
import re
import json
import argparse
import requests
from datetime import datetime
from urllib.parse import parse_qs, urlparse

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Person, Location, Tag, Chapter, FilmPeople, FilmLocations, ChapterPeople, ChapterLocations
from django.db import transaction

class BatchDImporter:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.youtube_playlist_url = 'https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm'
        self.added_videos_log = []
        self.stats = {
            'processed': 0,
            'found_youtube': 0,
            'created_films': 0,
            'created_chapters': 0,
            'created_people': 0,
            'created_locations': 0,
            'errors': 0
        }
        
    def log_video_status(self, filename, youtube_url=None, local_url=None, status='ERROR'):
        """Log video processing status for QA"""
        self.added_videos_log.append({
            'filename': filename,
            'youtube_url': youtube_url or '',
            'local_url': local_url or '',
            'status': status
        })

    def fetch_youtube_playlist_videos(self):
        """Fetch YouTube playlist videos - use cached data or create placeholder approach"""
        print("    🔍 Looking for YouTube video data...")
        
        # Check if we have cached data with descriptions
        cache_file = '/home/viblio/family_films/scripts/youtube_videos_with_descriptions.json'
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    if cached_data and len(cached_data) > 0:
                        print(f"    ✅ Using cached YouTube data with {len(cached_data)} videos")
                        return cached_data
            except Exception as e:
                print(f"    ⚠️ Could not load cached data: {e}")
        
        # For now, return existing data and create placeholders for missing videos
        # This allows the import to proceed without waiting for slow YouTube API calls
        print("    ⚠️ No cached YouTube descriptions available")
        print("    📋 Will create placeholder entries for manual YouTube mapping")
        
        return self._fallback_to_existing_data()
    
    def _fallback_to_existing_data(self):
        """Fallback to existing YouTube data if fresh fetch fails"""
        youtube_json_file = '/home/viblio/family_films/scripts/youtube_videos.json'
        
        try:
            if os.path.exists(youtube_json_file):
                with open(youtube_json_file, 'r') as f:
                    existing_data = json.load(f)
                    # Add empty descriptions to existing data
                    for video in existing_data:
                        if 'description' not in video:
                            video['description'] = ''
                    print(f"    ⚠️ Using existing data without descriptions ({len(existing_data)} videos)")
                    return existing_data
        except Exception as e:
            print(f"    ⚠️ Could not load existing YouTube data: {e}")
        
        return []

    def get_youtube_video_info(self, file_id):
        """
        Get YouTube video information by searching for File ID in video descriptions.
        """
        print(f"    🔍 Searching for YouTube video with File ID: {file_id}")
        
        # Try to get real YouTube data first
        if not hasattr(self, '_youtube_videos'):
            self._youtube_videos = self.fetch_youtube_playlist_videos()
        
        # Search through the YouTube videos for matching File ID
        for video in self._youtube_videos:
            description = video.get('description', '')
            if f"File ID: {file_id}" in description:
                print(f"    ✅ Found YouTube video: {video.get('title', 'Unknown')}")
                return {
                    'youtube_id': video.get('id', ''),
                    'youtube_url': f"https://www.youtube.com/watch?v={video.get('id', '')}",
                    'title': video.get('title', f"Family Film {file_id}"),
                    'description': description,
                    'thumbnail_url': video.get('thumbnail', f"https://img.youtube.com/vi/{video.get('id', '')}/hqdefault.jpg")
                }
        
        print(f"    ⚠️ No YouTube video found with File ID: {file_id}")
        
        # If real data not found, create a placeholder entry
        # This maintains the import process but marks videos as needing manual review
        placeholder_youtube_id = f"placeholder_{file_id.replace('-', '_')}"
        
        return {
            'youtube_id': placeholder_youtube_id,
            'youtube_url': f"https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm",
            'title': f"[NEEDS MANUAL MAPPING] {file_id}",
            'description': f"Manual mapping required for File ID: {file_id}",
            'thumbnail_url': None,
            'needs_manual_mapping': True
        }

    def parse_youtube_description(self, description):
        """Parse YouTube video description to extract structured metadata"""
        metadata = {
            'description': '',
            'chapters': [],
            'people': [],
            'years': [],
            'locations': [],
            'technical_notes': '',
            'file_id': ''
        }
        
        lines = description.split('\n')
        current_section = 'description'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            if line.lower().startswith('chapters:'):
                current_section = 'chapters'
                continue
            elif line.lower().startswith('people:'):
                current_section = 'people'
                continue
            elif line.lower().startswith('years:'):
                current_section = 'years'
                continue
            elif line.lower().startswith('locations:'):
                current_section = 'locations'
                continue
            elif line.lower().startswith('technical notes:'):
                current_section = 'technical_notes'
                continue
            elif line.startswith('File ID:'):
                metadata['file_id'] = line.replace('File ID:', '').strip()
                continue
            
            # Process content based on current section
            if current_section == 'description':
                if not any(line.lower().startswith(header) for header in ['chapters:', 'people:', 'years:', 'locations:', 'technical notes:']):
                    metadata['description'] += line + ' '
            elif current_section == 'chapters':
                # Parse chapter format: MM:SS Title
                match = re.match(r'^(\d{1,2}:\d{2})\s+(.+)$', line)
                if match:
                    timestamp, title = match.groups()
                    metadata['chapters'].append({
                        'start_time': timestamp,
                        'title': title.strip()
                    })
            elif current_section == 'people':
                # Parse comma-separated people
                people = [p.strip() for p in line.split(',') if p.strip()]
                metadata['people'].extend(people)
            elif current_section == 'years':
                # Parse comma-separated years
                years = [y.strip() for y in line.split(',') if y.strip()]
                metadata['years'].extend(years)
            elif current_section == 'locations':
                # Parse comma-separated locations
                locations = [l.strip() for l in line.split(',') if l.strip()]
                metadata['locations'].extend(locations)
            elif current_section == 'technical_notes':
                metadata['technical_notes'] += line + ' '
        
        # Clean up accumulated text
        metadata['description'] = metadata['description'].strip()
        metadata['technical_notes'] = metadata['technical_notes'].strip()
        
        return metadata

    def get_or_create_person(self, name):
        """Get or create a person by name"""
        if not name:
            return None
            
        # Split name into first and last
        parts = name.strip().split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        
        person, created = Person.objects.get_or_create(
            first_name=first_name,
            last_name=last_name
        )
        
        if created:
            self.stats['created_people'] += 1
            print(f"      ✓ Created person: {name}")
        
        return person

    def get_or_create_location(self, name):
        """Get or create a location by name"""
        if not name:
            return None
            
        location, created = Location.objects.get_or_create(
            name=name.strip()
        )
        
        if created:
            self.stats['created_locations'] += 1
            print(f"      ✓ Created location: {name}")
        
        return location

    def create_film_from_csv_and_youtube(self, csv_row, youtube_info):
        """Create a film from CSV data and YouTube information"""
        filename = csv_row['Filenames']
        
        # Parse YouTube description
        youtube_metadata = self.parse_youtube_description(youtube_info['description'])
        
        print(f"    📝 Creating film: {filename}")
        
        if not self.dry_run:
            with transaction.atomic():
                # Parse duration if available  
                duration_str = csv_row.get('Duration at 23.97 fps (most of this was shot at 16 or 18 FPS)', '')
                duration = None
                if duration_str and ':' in duration_str:
                    try:
                        # Try to parse duration like "0:09:26" 
                        parts = duration_str.split(':')
                        if len(parts) == 3:
                            hours, minutes, seconds = map(int, parts)
                            from datetime import timedelta
                            duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                    except (ValueError, IndexError):
                        duration = None
                
                # Create the film
                film = Film.objects.create(
                    file_id=filename,
                    title=csv_row.get('Title', '') or youtube_info['title'],
                    description=youtube_metadata['description'] or csv_row.get('Description', ''),
                    youtube_id=youtube_info['youtube_id'],
                    youtube_url=youtube_info['youtube_url'],
                    years=csv_row.get('Years', '') or (youtube_metadata['years'][0] if youtube_metadata['years'] else ''),
                    duration=duration,
                    workflow_state=csv_row.get('Workflow State', ''),
                    technical_notes=youtube_metadata['technical_notes'] or csv_row.get('Tech Notes', ''),
                    summary=csv_row.get('Summary', '')
                )
                
                # Create chapters
                for i, chapter_data in enumerate(youtube_metadata['chapters'], 1):
                    Chapter.objects.create(
                        film=film,
                        order=i,
                        title=chapter_data['title'],
                        start_time=chapter_data['start_time']
                    )
                    self.stats['created_chapters'] += 1
                
                # Create people relationships
                people_sources = []
                if csv_row.get('People'):
                    people_sources.extend([p.strip() for p in csv_row['People'].split(',') if p.strip()])
                people_sources.extend(youtube_metadata['people'])
                
                for person_name in set(people_sources):  # Remove duplicates
                    person = self.get_or_create_person(person_name)
                    if person:
                        FilmPeople.objects.get_or_create(film=film, person=person)
                
                # Create location relationships
                location_sources = []
                if csv_row.get('Location'):
                    location_sources.extend([l.strip() for l in csv_row['Location'].split(',') if l.strip()])
                location_sources.extend(youtube_metadata['locations'])
                
                for location_name in set(location_sources):  # Remove duplicates
                    location = self.get_or_create_location(location_name)
                    if location:
                        FilmLocations.objects.get_or_create(film=film, location=location)
                
                self.stats['created_films'] += 1
                print(f"      ✅ Created film with {len(youtube_metadata['chapters'])} chapters")
                
                # Generate local URL
                local_url = f"http://localhost:8000/films/{film.file_id}/"
                self.log_video_status(filename, youtube_info['youtube_url'], local_url, 'FOUND')
                
                return film
        else:
            print(f"      [DRY RUN] Would create film: {filename}")
            print(f"        - Title: {csv_row.get('Title', '') or youtube_info['title']}")
            print(f"        - Chapters: {len(youtube_metadata['chapters'])}")
            print(f"        - People: {len(set([p.strip() for p in csv_row.get('People', '').split(',') if p.strip()] + youtube_metadata['people']))}")
            print(f"        - Locations: {len(set([l.strip() for l in csv_row.get('Location', '').split(',') if l.strip()] + youtube_metadata['locations']))}")
            
            self.log_video_status(filename, youtube_info['youtube_url'], '', 'FOUND')
            return None

    def process_batch_d_films(self, csv_file):
        """Process all Batch D films from the CSV file"""
        print("=== BATCH D FILM IMPORT ===\n")
        
        if self.dry_run:
            print("🏃 DRY RUN MODE - No database changes will be made\n")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Only process Batch D entries
                    if row.get('Scan Batch (A, B, or C)') != 'Batch D':
                        continue
                    
                    filename = row.get('Filenames', '').strip()
                    if not filename:
                        continue
                    
                    self.stats['processed'] += 1
                    print(f"\n[{self.stats['processed']}/35] Processing: {filename}")
                    
                    try:
                        # Check if film already exists
                        if Film.objects.filter(file_id=filename).exists():
                            print(f"    ⚠️ Film {filename} already exists, skipping")
                            self.log_video_status(filename, '', f"http://localhost:8000/films/{filename}/", 'FOUND')
                            continue
                        
                        # Get YouTube video information
                        youtube_info = self.get_youtube_video_info(filename)
                        
                        if youtube_info:
                            if youtube_info.get('needs_manual_mapping'):
                                print(f"    ⚠️ Created placeholder entry for {filename} - manual mapping required")
                                self.stats['errors'] += 1
                            else:
                                self.stats['found_youtube'] += 1
                            
                            # Create the film (either real or placeholder)
                            film = self.create_film_from_csv_and_youtube(row, youtube_info)
                        else:
                            print(f"    ❌ No YouTube video found for {filename}")
                            self.log_video_status(filename, status='ERROR')
                            self.stats['errors'] += 1
                            
                    except Exception as e:
                        print(f"    ❌ Error processing {filename}: {str(e)}")
                        self.log_video_status(filename, status='ERROR')
                        self.stats['errors'] += 1
                        
        except FileNotFoundError:
            print(f"❌ CSV file not found: {csv_file}")
            return False
        except Exception as e:
            print(f"❌ Error reading CSV file: {str(e)}")
            return False
        
        return True

    def write_log_file(self):
        """Write the added_videos.log file"""
        log_file = 'added_videos.log'
        
        print(f"\n📝 Writing log file: {log_file}")
        
        with open(log_file, 'w') as f:
            # Write header
            f.write("Filename,YouTube_URL,Local_URL,Status\n")
            
            # Write each entry
            for entry in self.added_videos_log:
                f.write(f"{entry['filename']},{entry['youtube_url']},{entry['local_url']},{entry['status']}\n")
        
        print(f"   ✅ Log file written with {len(self.added_videos_log)} entries")

    def print_summary(self):
        """Print import summary"""
        print("\n" + "="*60)
        print("BATCH D IMPORT SUMMARY")
        print("="*60)
        print(f"Films processed: {self.stats['processed']}")
        print(f"YouTube videos found: {self.stats['found_youtube']}")
        print(f"Films created: {self.stats['created_films']}")
        print(f"Chapters created: {self.stats['created_chapters']}")
        print(f"People created: {self.stats['created_people']}")
        print(f"Locations created: {self.stats['created_locations']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.dry_run:
            print("\n⚠️  DRY RUN - No actual changes were made to the database")

def main():
    parser = argparse.ArgumentParser(description='Import Batch D films from CSV and YouTube')
    parser.add_argument('--csv-file', 
                       default='/home/viblio/family_films/design_docs/family_movies_batchd.csv',
                       help='Path to the family_movies_batchd.csv file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    importer = BatchDImporter(dry_run=args.dry_run)
    
    if importer.process_batch_d_films(args.csv_file):
        importer.write_log_file()
        importer.print_summary()
    else:
        print("❌ Import failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
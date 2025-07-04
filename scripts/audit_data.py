#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

import csv
import json
from main.models import Film

print('=== COMPREHENSIVE DATA AUDIT ===\n')

# 1. Count distinct filenames in CSV
print('1. ANALYZING family_reunion_movies.csv...')
csv_filenames = set()
csv_rows_processed = 0

try:
    with open('family_reunion_movies.csv', 'r', encoding='utf-8') as f:
        # Skip front matter lines until we find the header
        lines = f.readlines()
        header_found = False
        data_lines = []
        
        for i, line in enumerate(lines):
            if 'Filenames' in line and 'Years' in line and 'People' in line:
                header_found = True
                header_line = line
                data_lines = lines[i+1:]
                break
        
        if header_found:
            # Parse the CSV data
            csv_content = header_line + ''.join(data_lines)
            reader = csv.DictReader(csv_content.splitlines())
            
            for row in reader:
                filename = row.get('Filenames', '').strip()
                if filename and filename != 'Filenames':  # Skip empty and header rows
                    csv_filenames.add(filename)
                    csv_rows_processed += 1
        
    print(f'   CSV filenames found: {len(csv_filenames)}')
    print(f'   CSV rows processed: {csv_rows_processed}')
    
except Exception as e:
    print(f'   Error reading CSV: {e}')

print()

# 2. Count YouTube videos
print('2. ANALYZING YouTube videos...')
youtube_videos = []
try:
    with open('youtube_videos.json', 'r') as f:
        youtube_videos = json.load(f)
    
    print(f'   YouTube videos found: {len(youtube_videos)}')
    
    # Show sample
    print('   Sample YouTube videos:')
    for video in youtube_videos[:5]:
        print(f'     {video["video_id"]} - {video["title"][:50]}...')
    
except Exception as e:
    print(f'   Error reading YouTube data: {e}')

print()

# 3. Count local database records
print('3. ANALYZING local database...')
all_films = Film.objects.all()
print(f'   Database film records: {all_films.count()}')

mapped_films = Film.objects.exclude(youtube_id__startswith='placeholder_')
print(f'   Films with YouTube mapping: {mapped_films.count()}')

placeholder_films = Film.objects.filter(youtube_id__startswith='placeholder_')
print(f'   Films with placeholder IDs: {placeholder_films.count()}')

print()

# 4. Compare the datasets
print('4. COMPARING DATASETS...')

# Get database file IDs
db_file_ids = set(Film.objects.values_list('file_id', flat=True))

print(f'   CSV filenames: {len(csv_filenames)}')
print(f'   Database file_ids: {len(db_file_ids)}')
print(f'   YouTube videos: {len(youtube_videos)}')

print()

# Find discrepancies
print('5. FINDING DISCREPANCIES...')

# In CSV but not in database
csv_not_in_db = csv_filenames - db_file_ids
if csv_not_in_db:
    print(f'   CSV filenames NOT in database ({len(csv_not_in_db)}):')
    for filename in sorted(csv_not_in_db):
        print(f'     - {filename}')
else:
    print('   ✅ All CSV filenames found in database')

print()

# In database but not in CSV
db_not_in_csv = db_file_ids - csv_filenames
if db_not_in_csv:
    print(f'   Database file_ids NOT in CSV ({len(db_not_in_csv)}):')
    for file_id in sorted(db_not_in_csv):
        print(f'     - {file_id}')
else:
    print('   ✅ All database file_ids found in CSV')

print()

# Show unmapped films
if placeholder_films.exists():
    print(f'   UNMAPPED FILMS ({placeholder_films.count()}):')
    for film in placeholder_films:
        print(f'     - {film.file_id}: {film.title}')

print()

# Check YouTube video assignments
print('6. YOUTUBE VIDEO ASSIGNMENTS...')
youtube_ids = [v['video_id'] for v in youtube_videos]
assigned_youtube_ids = set(mapped_films.values_list('youtube_id', flat=True))

unassigned_youtube_videos = [vid for vid in youtube_ids if vid not in assigned_youtube_ids]
print(f'   Unassigned YouTube videos: {len(unassigned_youtube_videos)}')
for vid_id in unassigned_youtube_videos[:10]:  # Show first 10
    video = next(v for v in youtube_videos if v['video_id'] == vid_id)
    print(f'     - {vid_id}: {video["title"][:60]}...')

print('\n=== AUDIT COMPLETE ===')
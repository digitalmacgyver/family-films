#!/usr/bin/env python
import os
import sys
import django
import json
import subprocess
import re
import time

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

print('=== VERIFYING ALL YOUTUBE MAPPINGS ===\n')

# Get all films with YouTube mappings
mapped_films = Film.objects.exclude(youtube_id__startswith='placeholder_').order_by('file_id')
print(f'Checking {mapped_films.count()} mapped films...\n')

# Track results
correct_mappings = []
incorrect_mappings = []
no_file_id_found = []
errors = []

# Process each film
for i, film in enumerate(mapped_films):
    print(f'[{i+1}/{mapped_films.count()}] Checking {film.file_id}...')
    
    try:
        # Fetch YouTube description using yt-dlp
        cmd = [
            '~/.local/bin/yt-dlp', '--dump-json', '--no-download',
            '--no-warnings', f'https://www.youtube.com/watch?v={film.youtube_id}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              check=True, shell=True)
        
        data = json.loads(result.stdout)
        description = data.get('description', '')
        title = data.get('title', '')
        
        # Extract File ID from description
        file_id_match = re.search(r'File ID:\s*([^\s\n]+)', description, re.IGNORECASE)
        
        if file_id_match:
            youtube_file_id = file_id_match.group(1).strip()
            
            if youtube_file_id == film.file_id:
                correct_mappings.append({
                    'file_id': film.file_id,
                    'youtube_id': film.youtube_id,
                    'title': film.title
                })
                print(f'  ✅ CORRECT: {film.file_id} -> {film.youtube_id}')
            else:
                incorrect_mappings.append({
                    'db_file_id': film.file_id,
                    'youtube_file_id': youtube_file_id,
                    'youtube_id': film.youtube_id,
                    'db_title': film.title,
                    'youtube_title': title
                })
                print(f'  ❌ INCORRECT: DB has {film.file_id} but YouTube says {youtube_file_id}')
                print(f'     DB Title: {film.title[:60]}...')
                print(f'     YT Title: {title[:60]}...')
        else:
            no_file_id_found.append({
                'file_id': film.file_id,
                'youtube_id': film.youtube_id,
                'title': film.title
            })
            print(f'  ⚠️  NO FILE ID in YouTube description')
        
        # Small delay to be respectful to YouTube
        time.sleep(1)
        
    except subprocess.CalledProcessError as e:
        errors.append({
            'file_id': film.file_id,
            'youtube_id': film.youtube_id,
            'error': str(e)
        })
        print(f'  ❗ ERROR: Failed to fetch YouTube data')
    except json.JSONDecodeError as e:
        errors.append({
            'file_id': film.file_id,
            'youtube_id': film.youtube_id,
            'error': str(e)
        })
        print(f'  ❗ ERROR: Failed to parse JSON')

print('\n=== VERIFICATION SUMMARY ===\n')

print(f'Total checked: {mapped_films.count()}')
print(f'✅ Correct mappings: {len(correct_mappings)}')
print(f'❌ Incorrect mappings: {len(incorrect_mappings)}')
print(f'⚠️  No File ID in description: {len(no_file_id_found)}')
print(f'❗ Errors: {len(errors)}')

if incorrect_mappings:
    print('\n=== INCORRECT MAPPINGS DETAIL ===\n')
    for mapping in incorrect_mappings:
        print(f'YouTube ID: {mapping["youtube_id"]}')
        print(f'  Database has: {mapping["db_file_id"]} - "{mapping["db_title"][:50]}..."')
        print(f'  YouTube says: {mapping["youtube_file_id"]} - "{mapping["youtube_title"][:50]}..."')
        print()

if no_file_id_found:
    print('\n=== VIDEOS WITHOUT FILE ID ===\n')
    for video in no_file_id_found[:5]:  # Show first 5
        print(f'{video["youtube_id"]} - {video["file_id"]} - {video["title"][:50]}...')
    if len(no_file_id_found) > 5:
        print(f'... and {len(no_file_id_found) - 5} more')

# Save results to file
results = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total_checked': mapped_films.count(),
    'correct_mappings': correct_mappings,
    'incorrect_mappings': incorrect_mappings,
    'no_file_id_found': no_file_id_found,
    'errors': errors
}

with open('youtube_mapping_verification.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'\nDetailed results saved to youtube_mapping_verification.json')
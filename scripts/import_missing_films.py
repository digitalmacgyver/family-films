#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from django.core.management import call_command
from main.models import Film

print('=== IMPORTING MISSING FILMS ===\n')

# Films to import (that have titles but were skipped due to missing Years)
missing_films = {
    'P-CC2_FROS': {
        'youtube_id': 'oBXSxjnrhyk',
        'title': 'Michigan Home near Copper Mine in 1951-1952'
    },
    'PB-06_FROS': {
        'youtube_id': 'GwVQqPKoaKI', 
        'title': 'John Sr. & Josephine travel to Yosemite with John Jr., Joy, and Mark - Wren Family Joins towards End'
    },
    'RLA-01_FROS': {
        'youtube_id': 'yoC6HK6UTIo',
        'title': 'Victor Beattie\'s Church Camp (Largely Damaged Film)'
    },
    'RLA-02_FROS': {
        'youtube_id': 'ET9fqZKnqYg',
        'title': 'Unknown Families - Most Likely Bob Lindner\'s Extended Family'
    },
    'RLB-01_FROS': {
        'youtube_id': 'km8G_fx38oU',
        'title': 'Hayward Family Pool at Reed Ave. Home in Reedley, CA (Damaged)'
    },
    'SLB-02_FROS': {
        'youtube_id': 'GosLiczgdH8',
        'title': 'Hayward Family Home at Reed Ave in Reedley, CA (Mostly damaged film)'
    }
}

# Check current state
print('BEFORE IMPORT:')
print(f'Total films in database: {Film.objects.count()}')
print()

# Import the missing films
print('Running import command for family_reunion_movies.csv...')
try:
    call_command('import_family_films', 'family_reunion_movies.csv')
    print('Import completed!')
except Exception as e:
    print(f'Error during import: {e}')

print()
print('AFTER IMPORT:')
print(f'Total films in database: {Film.objects.count()}')

# Now map the YouTube IDs
print('\n=== MAPPING YOUTUBE IDs ===\n')

for file_id, info in missing_films.items():
    try:
        film = Film.objects.get(file_id=file_id)
        old_youtube_id = film.youtube_id
        
        # Update YouTube mapping
        film.youtube_id = info['youtube_id']
        film.youtube_url = f"https://www.youtube.com/watch?v={info['youtube_id']}"
        film.thumbnail_url = f"https://img.youtube.com/vi/{info['youtube_id']}/maxresdefault.jpg"
        film.thumbnail_high_url = f"https://img.youtube.com/vi/{info['youtube_id']}/hqdefault.jpg"
        film.thumbnail_medium_url = f"https://img.youtube.com/vi/{info['youtube_id']}/mqdefault.jpg"
        film.save()
        
        print(f'✅ Mapped {file_id}: {old_youtube_id} -> {info["youtube_id"]}')
        print(f'   Title: {film.title}')
        
    except Film.DoesNotExist:
        print(f'❌ Film not found: {file_id}')
    except Exception as e:
        print(f'❌ Error mapping {file_id}: {e}')

print('\n=== FINAL STATUS ===')
total = Film.objects.count()
mapped = Film.objects.exclude(youtube_id__startswith='placeholder_').count()
print(f'Total films: {total}')
print(f'Mapped films: {mapped}')
print(f'Unmapped films: {total - mapped}')
#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def main():
    print("=== UPDATING YOUTUBE MAPPINGS ===\n")
    
    # Read our verification results to get the correct mappings
    verification_file = 'youtube_verification_results.json'
    
    if not os.path.exists(verification_file):
        print(f"ERROR: {verification_file} not found. Run verify_all_youtube_mappings.py first.")
        return
    
    with open(verification_file, 'r') as f:
        verification_data = json.load(f)
    
    print(f"Found verification data from: {verification_data['timestamp']}")
    print(f"Total incorrect mappings to fix: {len(verification_data['incorrect_mappings'])}\n")
    
    # Create mapping from YouTube video ID to correct File ID
    youtube_to_correct_file_id = {}
    
    # Add the one correct mapping we know
    for correct in verification_data['correct_mappings']:
        youtube_to_correct_file_id[correct['youtube_id']] = correct['file_id']
        print(f"✅ Keeping correct mapping: {correct['file_id']} -> {correct['youtube_id']}")
    
    # For incorrect mappings, map YouTube ID to the correct File ID found in description
    for incorrect in verification_data['incorrect_mappings']:
        youtube_id = incorrect['youtube_id']
        correct_file_id = incorrect['youtube_file_id']
        youtube_to_correct_file_id[youtube_id] = correct_file_id
        print(f"📝 Will map {correct_file_id} -> {youtube_id} (was incorrectly {incorrect['db_file_id']})")
    
    print(f"\n=== UPDATING DATABASE ===\n")
    
    updated_count = 0
    errors = []
    
    # Update each mapping
    for youtube_id, correct_file_id in youtube_to_correct_file_id.items():
        try:
            # Find the film that should have this YouTube ID
            film = Film.objects.get(file_id=correct_file_id)
            
            # Clear any existing film with this YouTube ID
            existing_films = Film.objects.filter(youtube_id=youtube_id).exclude(file_id=correct_file_id)
            for existing_film in existing_films:
                existing_film.youtube_id = f'placeholder_{existing_film.file_id}'
                existing_film.youtube_url = f'https://www.youtube.com/watch?v=placeholder_{existing_film.file_id}'
                existing_film.thumbnail_url = f'https://img.youtube.com/vi/placeholder_{existing_film.file_id}/maxresdefault.jpg'
                existing_film.save()
                print(f"  🔄 Reset {existing_film.file_id} to placeholder (was using {youtube_id})")
            
            # Update the correct film with the YouTube ID
            old_youtube_id = film.youtube_id
            film.youtube_id = youtube_id
            film.youtube_url = f'https://www.youtube.com/watch?v={youtube_id}'
            film.thumbnail_url = f'https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg'
            film.thumbnail_high_url = f'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'
            film.thumbnail_medium_url = f'https://img.youtube.com/vi/{youtube_id}/mqdefault.jpg'
            film.save()
            
            updated_count += 1
            print(f"  ✅ Updated {correct_file_id}: {old_youtube_id} -> {youtube_id}")
            
        except Film.DoesNotExist:
            error_msg = f"Film with file_id '{correct_file_id}' not found"
            errors.append(error_msg)
            print(f"  ❗ ERROR: {error_msg}")
        except Exception as e:
            error_msg = f"Failed to update {correct_file_id} -> {youtube_id}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❗ ERROR: {error_msg}")
    
    print(f"\n=== UPDATE SUMMARY ===")
    print(f"Mappings updated: {updated_count}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    # Verify how many films now have non-placeholder YouTube IDs
    films_with_youtube = Film.objects.exclude(youtube_id__startswith='placeholder_').count()
    total_films = Film.objects.count()
    
    print(f"\nFilms with YouTube mappings: {films_with_youtube}/{total_films}")
    
    if films_with_youtube > 0:
        print("\nFilms with YouTube mappings:")
        for film in Film.objects.exclude(youtube_id__startswith='placeholder_').order_by('file_id'):
            print(f"  {film.file_id} -> {film.youtube_id}")
    
    print(f"\n✓ YouTube mapping update complete!")

if __name__ == '__main__':
    main()
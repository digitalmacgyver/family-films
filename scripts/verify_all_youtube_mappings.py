#!/usr/bin/env python
import os
import sys
import django
import json
import subprocess
import re
import time
from pathlib import Path

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def find_yt_dlp():
    """Find yt-dlp executable"""
    # Check common locations
    paths = [
        'yt-dlp',
        os.path.expanduser('~/.local/bin/yt-dlp'),
        '/usr/local/bin/yt-dlp',
        '/usr/bin/yt-dlp'
    ]
    
    for path in paths:
        try:
            result = subprocess.run([path, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return path
        except FileNotFoundError:
            continue
    
    raise RuntimeError("yt-dlp not found. Please install with: pip install yt-dlp")

def fetch_youtube_description(video_id, yt_dlp_path):
    """Fetch YouTube video description using yt-dlp"""
    url = f'https://www.youtube.com/watch?v={video_id}'
    
    cmd = [
        yt_dlp_path, 
        '--dump-json', 
        '--no-download',
        '--no-warnings', 
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return {
            'success': True,
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'video_id': data.get('id', video_id)
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': f"Command failed: {e.stderr}"
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f"Failed to parse JSON: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def extract_file_id(description):
    """Extract File ID from YouTube description"""
    if not description:
        return None
    
    # Look for File ID pattern
    file_id_match = re.search(r'File ID:\s*([^\s\n]+)', description, re.IGNORECASE)
    if file_id_match:
        return file_id_match.group(1).strip()
    
    return None

def main():
    print('=== VERIFYING ALL YOUTUBE MAPPINGS ===\n')
    
    # Find yt-dlp
    try:
        yt_dlp_path = find_yt_dlp()
        print(f'Using yt-dlp at: {yt_dlp_path}\n')
    except RuntimeError as e:
        print(f'ERROR: {e}')
        return
    
    # Get all films with YouTube mappings
    mapped_films = Film.objects.exclude(youtube_id__startswith='placeholder_').order_by('file_id')
    total_films = mapped_films.count()
    print(f'Found {total_films} films with YouTube mappings\n')
    
    # Track results
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_checked': 0,
        'successful_fetches': 0,
        'failed_fetches': 0,
        'correct_mappings': [],
        'incorrect_mappings': [],
        'no_file_id_found': [],
        'errors': []
    }
    
    # Process each film
    for i, film in enumerate(mapped_films):
        print(f'[{i+1}/{total_films}] Checking {film.file_id} -> {film.youtube_id}')
        
        # Fetch YouTube data
        youtube_data = fetch_youtube_description(film.youtube_id, yt_dlp_path)
        
        if youtube_data['success']:
            results['successful_fetches'] += 1
            
            # Extract File ID from description
            youtube_file_id = extract_file_id(youtube_data['description'])
            
            if youtube_file_id:
                if youtube_file_id == film.file_id:
                    # Correct mapping
                    results['correct_mappings'].append({
                        'file_id': film.file_id,
                        'youtube_id': film.youtube_id,
                        'title': film.title
                    })
                    print(f'  ✅ CORRECT mapping confirmed')
                else:
                    # Incorrect mapping
                    results['incorrect_mappings'].append({
                        'db_file_id': film.file_id,
                        'youtube_file_id': youtube_file_id,
                        'youtube_id': film.youtube_id,
                        'db_title': film.title,
                        'youtube_title': youtube_data['title']
                    })
                    print(f'  ❌ INCORRECT: Database has {film.file_id} but YouTube has {youtube_file_id}')
            else:
                # No File ID in description
                results['no_file_id_found'].append({
                    'file_id': film.file_id,
                    'youtube_id': film.youtube_id,
                    'title': film.title,
                    'youtube_title': youtube_data['title']
                })
                print(f'  ⚠️  No File ID found in YouTube description')
        else:
            # Failed to fetch
            results['failed_fetches'] += 1
            results['errors'].append({
                'file_id': film.file_id,
                'youtube_id': film.youtube_id,
                'error': youtube_data['error']
            })
            print(f'  ❗ ERROR: {youtube_data["error"]}')
        
        results['total_checked'] += 1
        
        # Small delay to be respectful
        if i < total_films - 1:  # Don't delay after last item
            time.sleep(0.5)
    
    # Display summary
    print('\n' + '='*60)
    print('VERIFICATION SUMMARY')
    print('='*60)
    print(f'Total films checked: {results["total_checked"]}')
    print(f'Successful YouTube fetches: {results["successful_fetches"]}')
    print(f'Failed YouTube fetches: {results["failed_fetches"]}')
    print(f'✅ Correct mappings: {len(results["correct_mappings"])}')
    print(f'❌ Incorrect mappings: {len(results["incorrect_mappings"])}')
    print(f'⚠️  No File ID in description: {len(results["no_file_id_found"])}')
    
    # Show incorrect mappings in detail
    if results['incorrect_mappings']:
        print('\n' + '='*60)
        print('INCORRECT MAPPINGS (NEED FIXING)')
        print('='*60)
        for mapping in results['incorrect_mappings']:
            print(f'\nYouTube Video: https://www.youtube.com/watch?v={mapping["youtube_id"]}')
            print(f'  Database says: {mapping["db_file_id"]} - "{mapping["db_title"]}"')
            print(f'  YouTube says:  {mapping["youtube_file_id"]} - "{mapping["youtube_title"]}"')
    
    # Show videos without File ID
    if results['no_file_id_found']:
        print('\n' + '='*60)
        print('VIDEOS WITHOUT FILE ID IN DESCRIPTION')
        print('='*60)
        for video in results['no_file_id_found'][:10]:  # Show first 10
            print(f'  {video["youtube_id"]} - {video["file_id"]} - {video["title"][:50]}...')
        if len(results['no_file_id_found']) > 10:
            print(f'  ... and {len(results["no_file_id_found"]) - 10} more')
    
    # Save detailed results
    output_file = 'youtube_verification_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f'\n✓ Detailed results saved to: {output_file}')
    
    # Create fixes file if there are incorrect mappings
    if results['incorrect_mappings']:
        fixes_file = 'youtube_mapping_fixes.txt'
        with open(fixes_file, 'w') as f:
            f.write('# YouTube Mapping Fixes Needed\n')
            f.write(f'# Generated: {results["timestamp"]}\n\n')
            
            for mapping in results['incorrect_mappings']:
                f.write(f'# YouTube {mapping["youtube_id"]} belongs to {mapping["youtube_file_id"]}, not {mapping["db_file_id"]}\n')
                f.write(f'# Fix: Update {mapping["db_file_id"]} to use a different YouTube video\n')
                f.write(f'#      OR update {mapping["youtube_file_id"]} to use {mapping["youtube_id"]}\n\n')
        
        print(f'✓ Suggested fixes saved to: {fixes_file}')

if __name__ == '__main__':
    main()
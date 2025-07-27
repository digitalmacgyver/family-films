#!/usr/bin/env python
"""
Comprehensive YouTube Management Tool

This script consolidates all YouTube-related functionality:
- Verify YouTube mappings by checking File IDs in descriptions
- Update incorrect mappings
- Check which films use a specific YouTube ID
- Fetch playlist order
- Perform quick verification of specific mappings
"""
import os
import sys
import django
import json
import subprocess
import re
import time
import argparse
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

def check_youtube_id(youtube_id):
    """Check which films are associated with a specific YouTube ID"""
    print(f'=== CHECKING FILE IDs FOR YOUTUBE VIDEO {youtube_id} ===\n')
    
    films = Film.objects.filter(youtube_id=youtube_id)
    
    if films.exists():
        print(f'Films associated with https://www.youtube.com/watch?v={youtube_id}:\n')
        for film in films:
            print(f'* File ID: {film.file_id}')
            print(f'  Title: {film.title}')
            print(f'  Years: {film.years}')
            print(f'  Description: {film.description[:200]}...')
            print()
    else:
        print(f'No films found with YouTube ID: {youtube_id}')
    
    # Also show what this video is in our YouTube data if available
    try:
        with open('youtube_videos.json', 'r') as f:
            videos = json.load(f)
        
        for video in videos:
            if video['video_id'] == youtube_id:
                print(f'\nYouTube video information:')
                print(f'  Video ID: {video["video_id"]}')
                print(f'  Title: {video["title"]}')
                print(f'  URL: {video["url"]}')
                break
    except:
        pass

def update_youtube_mappings(dry_run=False):
    """Update incorrect YouTube mappings based on verification results"""
    print("=== UPDATING YOUTUBE MAPPINGS ===\n")
    
    verification_file = 'youtube_verification_results.json'
    
    if not os.path.exists(verification_file):
        print(f"ERROR: {verification_file} not found. Run verify-all mode first.")
        return
    
    with open(verification_file, 'r') as f:
        verification_data = json.load(f)
    
    print(f"Found verification data from: {verification_data['timestamp']}")
    print(f"Total incorrect mappings to fix: {len(verification_data['incorrect_mappings'])}\n")
    
    # Create mapping from YouTube video ID to correct File ID
    youtube_to_correct_file_id = {}
    
    # Add the correct mappings
    for correct in verification_data['correct_mappings']:
        youtube_to_correct_file_id[correct['youtube_id']] = correct['file_id']
        print(f"✅ Keeping correct mapping: {correct['file_id']} -> {correct['youtube_id']}")
    
    # For incorrect mappings, map YouTube ID to the correct File ID found in description
    for incorrect in verification_data['incorrect_mappings']:
        youtube_id = incorrect['youtube_id']
        correct_file_id = incorrect['youtube_file_id']
        youtube_to_correct_file_id[youtube_id] = correct_file_id
        print(f"📝 Will map {correct_file_id} -> {youtube_id} (was incorrectly {incorrect['db_file_id']})")
    
    if dry_run:
        print("\n[DRY RUN] No changes will be made to the database.")
        return
    
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

def fetch_playlist_order(playlist_url=None):
    """Fetch YouTube playlist order"""
    if not playlist_url:
        playlist_url = "https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm"
    
    print(f"=== FETCHING PLAYLIST ORDER ===\n")
    print(f"Playlist URL: {playlist_url}\n")
    
    try:
        yt_dlp_path = find_yt_dlp()
        cmd = [
            yt_dlp_path,
            '--flat-playlist',
            '--dump-json',
            '--no-warnings',
            playlist_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        playlist_order = {}
        order_index = 1
        
        # Process each line (each video is a separate JSON object)
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    entry = json.loads(line)
                    video_id = entry.get('id')
                    title = entry.get('title', '')
                    
                    if video_id:
                        playlist_order[video_id] = {
                            'order': order_index,
                            'title': title
                        }
                        order_index += 1
                        
                except json.JSONDecodeError:
                    continue
        
        print(f"Found {len(playlist_order)} videos in playlist\n")
        
        # Check which films are in the playlist
        matched = 0
        not_in_db = 0
        
        for youtube_id, data in playlist_order.items():
            try:
                film = Film.objects.get(youtube_id=youtube_id)
                matched += 1
                print(f"  #{data['order']:3d} - {film.file_id} - {film.title[:50]}...")
            except Film.DoesNotExist:
                not_in_db += 1
                print(f"  #{data['order']:3d} - [NOT IN DB] - {data['title'][:50]}...")
        
        print(f"\nSummary:")
        print(f"  Videos in playlist: {len(playlist_order)}")
        print(f"  Matched in database: {matched}")
        print(f"  Not in database: {not_in_db}")
        
        # Save playlist data
        with open('youtube_playlist_order.json', 'w') as f:
            json.dump(playlist_order, f, indent=2)
        print(f"\n✓ Playlist order saved to: youtube_playlist_order.json")
        
        return playlist_order
        
    except subprocess.CalledProcessError as e:
        print(f"Error fetching playlist: {e}")
        return {}

def quick_verify(film_ids=None):
    """Quick verification of specific film mappings"""
    print('=== QUICK VERIFICATION OF YOUTUBE MAPPINGS ===\n')
    
    # Default test cases if none provided
    if not film_ids:
        film_ids = ['P-04', 'P-23', 'P-39', 'P-61', 'PA-03']
    
    yt_dlp_path = find_yt_dlp()
    
    correct = 0
    incorrect = 0
    
    for file_id in film_ids:
        try:
            film = Film.objects.get(file_id=file_id)
            print(f"Checking {film.file_id} -> {film.youtube_id}")
            
            youtube_data = fetch_youtube_description(film.youtube_id, yt_dlp_path)
            
            if youtube_data['success']:
                youtube_file_id = extract_file_id(youtube_data['description'])
                
                if youtube_file_id == film.file_id:
                    print(f"  ✅ CORRECT mapping confirmed")
                    correct += 1
                else:
                    print(f"  ❌ INCORRECT: DB has {film.file_id} but YouTube has {youtube_file_id}")
                    incorrect += 1
            else:
                print(f"  ❗ ERROR: {youtube_data['error']}")
                
        except Film.DoesNotExist:
            print(f"Film {file_id} not found in database")
        
        print()
    
    print(f"Summary: {correct} correct, {incorrect} incorrect")
    if correct > 0:
        print(f"Success rate: {(correct / (correct + incorrect)) * 100:.1f}%")

def verify_all():
    """Verify all YouTube mappings"""
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
    parser = argparse.ArgumentParser(description='YouTube mapping management tool')
    parser.add_argument('command', choices=['verify-all', 'update', 'check-id', 'playlist', 'quick-verify'],
                        help='Command to run')
    parser.add_argument('--youtube-id', help='YouTube video ID (for check-id command)')
    parser.add_argument('--playlist-url', help='YouTube playlist URL (for playlist command)')
    parser.add_argument('--file-ids', nargs='+', help='File IDs to verify (for quick-verify)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    if args.command == 'verify-all':
        verify_all()
    elif args.command == 'update':
        update_youtube_mappings(dry_run=args.dry_run)
    elif args.command == 'check-id':
        if not args.youtube_id:
            print("ERROR: --youtube-id required for check-id command")
            sys.exit(1)
        check_youtube_id(args.youtube_id)
    elif args.command == 'playlist':
        fetch_playlist_order(args.playlist_url)
    elif args.command == 'quick-verify':
        quick_verify(args.file_ids)
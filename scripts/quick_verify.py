#!/usr/bin/env python
import os
import sys
import django
import subprocess
import json
import re

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def test_mapping(film):
    """Test a single film mapping"""
    print(f"Testing {film.file_id} -> {film.youtube_id}")
    
    try:
        cmd = [
            os.path.expanduser('~/.local/bin/yt-dlp'), 
            '--dump-json', 
            '--no-download',
            '--no-warnings', 
            f'https://www.youtube.com/watch?v={film.youtube_id}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        data = json.loads(result.stdout)
        description = data.get('description', '')
        
        # Extract File ID from description
        file_id_match = re.search(r'File ID:\s*([^\s\n]+)', description, re.IGNORECASE)
        
        if file_id_match:
            youtube_file_id = file_id_match.group(1).strip()
            
            if youtube_file_id == film.file_id:
                print(f"  ✅ CORRECT: {film.file_id} matches YouTube File ID")
                return True
            else:
                print(f"  ❌ INCORRECT: Expected {film.file_id}, got {youtube_file_id}")
                return False
        else:
            print(f"  ⚠️  No File ID found in YouTube description")
            return False
            
    except Exception as e:
        print(f"  ❗ ERROR: {str(e)}")
        return False

def main():
    print("=== QUICK YOUTUBE MAPPING VERIFICATION ===\n")
    
    # Test a few key mappings
    test_file_ids = [
        'P-56_FROS',  # This was the only correct one before
        'PB-14_FROS', # This was the conflict case you discovered
        '57-PT_FROS', # First in the list
        'L-59_FROS',  # One of the conflicts we fixed earlier
        'P-61_FROS'   # Another key mapping
    ]
    
    correct_count = 0
    total_count = 0
    
    for file_id in test_file_ids:
        try:
            film = Film.objects.get(file_id=file_id)
            if not film.youtube_id.startswith('placeholder_'):
                total_count += 1
                if test_mapping(film):
                    correct_count += 1
                print()
            else:
                print(f"Skipping {file_id} - still has placeholder YouTube ID")
        except Film.DoesNotExist:
            print(f"Film {file_id} not found")
    
    print(f"=== QUICK VERIFICATION SUMMARY ===")
    print(f"Tested: {total_count}")
    print(f"Correct: {correct_count}")
    print(f"Success rate: {(correct_count/total_count*100):.1f}%" if total_count > 0 else "N/A")
    
    if correct_count == total_count:
        print("🎉 All tested mappings are CORRECT!")
    else:
        print("⚠️  Some mappings still need fixing")

if __name__ == '__main__':
    main()
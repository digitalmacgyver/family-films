#!/usr/bin/env python
"""
Compare database before and after import to show what changes were made
"""
import os
import sys
import django
import sqlite3
from datetime import datetime
from collections import defaultdict

# Setup Django
sys.path.insert(0, '/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Chapter, ChapterPeople, ChapterLocations, ChapterTags, Person, Location, Tag


def get_database_stats(db_path):
    """Get statistics from a database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total chapters with descriptions
    cursor.execute("SELECT COUNT(*) FROM main_chapter WHERE description != ''")
    stats['chapters_with_descriptions'] = cursor.fetchone()[0]
    
    # Total chapters with years
    cursor.execute("SELECT COUNT(*) FROM main_chapter WHERE years != ''") 
    stats['chapters_with_years'] = cursor.fetchone()[0]
    
    # Total chapter-people associations
    cursor.execute("SELECT COUNT(*) FROM main_chapterpeople")
    stats['chapter_people_associations'] = cursor.fetchone()[0]
    
    # Total chapter-location associations
    cursor.execute("SELECT COUNT(*) FROM main_chapterlocations")
    stats['chapter_location_associations'] = cursor.fetchone()[0]
    
    # Total chapter-tag associations
    cursor.execute("SELECT COUNT(*) FROM main_chaptertags")
    stats['chapter_tag_associations'] = cursor.fetchone()[0]
    
    # Total people
    cursor.execute("SELECT COUNT(*) FROM main_person")
    stats['total_people'] = cursor.fetchone()[0]
    
    # Total locations
    cursor.execute("SELECT COUNT(*) FROM main_location")
    stats['total_locations'] = cursor.fetchone()[0]
    
    # Total tags
    cursor.execute("SELECT COUNT(*) FROM main_tag")
    stats['total_tags'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


def get_detailed_chapter_data(db_path):
    """Get detailed chapter data for comparison"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get chapters with their metadata
    cursor.execute("""
        SELECT c.id, c.film_id, c.title, c.description, c.years,
               (SELECT COUNT(*) FROM main_chapterpeople WHERE chapter_id = c.id) as people_count,
               (SELECT COUNT(*) FROM main_chapterlocations WHERE chapter_id = c.id) as location_count,
               (SELECT COUNT(*) FROM main_chaptertags WHERE chapter_id = c.id) as tag_count
        FROM main_chapter c
        ORDER BY c.film_id, c."order"
    """)
    
    chapters = {}
    for row in cursor.fetchall():
        chapters[row[0]] = {
            'film_id': row[1],
            'title': row[2],
            'description': row[3],
            'years': row[4],
            'people_count': row[5],
            'location_count': row[6],
            'tag_count': row[7]
        }
    
    conn.close()
    return chapters


def compare_chapter_details(before_chapters, after_chapters):
    """Compare chapter details and return changes"""
    changes = []
    
    for chapter_id, after_data in after_chapters.items():
        if chapter_id in before_chapters:
            before_data = before_chapters[chapter_id]
            
            # Check what changed
            if before_data != after_data:
                change = {
                    'chapter_id': chapter_id,
                    'film_id': after_data['film_id'],
                    'title': after_data['title'],
                    'changes': []
                }
                
                # Description changes
                if before_data['description'] != after_data['description']:
                    change['changes'].append({
                        'field': 'description',
                        'before': before_data['description'][:50] + '...' if before_data['description'] and len(before_data['description']) > 50 else before_data['description'],
                        'after': after_data['description'][:50] + '...' if after_data['description'] and len(after_data['description']) > 50 else after_data['description']
                    })
                
                # Year changes
                if before_data['years'] != after_data['years']:
                    change['changes'].append({
                        'field': 'years',
                        'before': before_data['years'],
                        'after': after_data['years']
                    })
                
                # People count changes
                if before_data['people_count'] != after_data['people_count']:
                    change['changes'].append({
                        'field': 'people_count',
                        'before': before_data['people_count'],
                        'after': after_data['people_count'],
                        'added': after_data['people_count'] - before_data['people_count']
                    })
                
                # Location count changes
                if before_data['location_count'] != after_data['location_count']:
                    change['changes'].append({
                        'field': 'location_count',
                        'before': before_data['location_count'],
                        'after': after_data['location_count'],
                        'added': after_data['location_count'] - before_data['location_count']
                    })
                
                # Tag count changes
                if before_data['tag_count'] != after_data['tag_count']:
                    change['changes'].append({
                        'field': 'tag_count',
                        'before': before_data['tag_count'],
                        'after': after_data['tag_count'],
                        'added': after_data['tag_count'] - before_data['tag_count']
                    })
                
                if change['changes']:
                    changes.append(change)
    
    return changes


def print_comparison_report(backup_path, current_path):
    """Generate and print comparison report"""
    print("\nDATABASE COMPARISON REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backup database: {backup_path}")
    print(f"Current database: {current_path}")
    print()
    
    # Get statistics
    before_stats = get_database_stats(backup_path)
    after_stats = get_database_stats(current_path)
    
    # Print overall statistics
    print("OVERALL STATISTICS")
    print("-" * 80)
    print(f"{'Metric':<40} {'Before':>10} {'After':>10} {'Change':>10}")
    print("-" * 80)
    
    for key in sorted(before_stats.keys()):
        before = before_stats[key]
        after = after_stats[key]
        change = after - before
        change_str = f"+{change}" if change > 0 else str(change)
        print(f"{key.replace('_', ' ').title():<40} {before:>10} {after:>10} {change_str:>10}")
    
    # Get detailed changes
    print("\n\nDETAILED CHAPTER CHANGES")
    print("=" * 80)
    
    before_chapters = get_detailed_chapter_data(backup_path)
    after_chapters = get_detailed_chapter_data(current_path)
    changes = compare_chapter_details(before_chapters, after_chapters)
    
    # Group changes by film
    changes_by_film = defaultdict(list)
    for change in changes:
        changes_by_film[change['film_id']].append(change)
    
    total_chapters_updated = len(changes)
    print(f"Total chapters updated: {total_chapters_updated}")
    print()
    
    # Print changes by film
    for film_id in sorted(changes_by_film.keys()):
        film_changes = changes_by_film[film_id]
        print(f"\nFilm: {film_id}")
        print("-" * 80)
        
        for chapter_change in film_changes:
            print(f"\n  Chapter: {chapter_change['title'][:60]}...")
            for change in chapter_change['changes']:
                if change['field'] in ['people_count', 'location_count', 'tag_count']:
                    field_name = change['field'].replace('_count', 's')
                    print(f"    - {field_name}: {change['before']} → {change['after']} (+{change['added']})")
                else:
                    print(f"    - {change['field']}: '{change['before']}' → '{change['after']}'")
    
    # Summary of new entities created
    print("\n\nNEW ENTITIES CREATED")
    print("=" * 80)
    
    # Get new people
    conn_before = sqlite3.connect(backup_path)
    conn_after = sqlite3.connect(current_path)
    
    cursor_before = conn_before.cursor()
    cursor_after = conn_after.cursor()
    
    # New people
    cursor_before.execute("SELECT id FROM main_person")
    before_people_ids = set(row[0] for row in cursor_before.fetchall())
    
    cursor_after.execute("SELECT id, first_name, last_name, hayward_index FROM main_person")
    after_people = cursor_after.fetchall()
    
    new_people = [p for p in after_people if p[0] not in before_people_ids]
    if new_people:
        print("\nNew People Added:")
        for person in new_people:
            name = f"{person[1]} {person[2]}".strip()
            hayward = f" (Hayward family member, index {person[3]})" if person[3] is not None else ""
            print(f"  - {name}{hayward}")
    
    # New locations
    cursor_before.execute("SELECT id FROM main_location")
    before_location_ids = set(row[0] for row in cursor_before.fetchall())
    
    cursor_after.execute("SELECT id, name FROM main_location")
    after_locations = cursor_after.fetchall()
    
    new_locations = [l for l in after_locations if l[0] not in before_location_ids]
    if new_locations:
        print("\nNew Locations Added:")
        for location in new_locations[:20]:  # Limit to first 20
            print(f"  - {location[1]}")
        if len(new_locations) > 20:
            print(f"  ... and {len(new_locations) - 20} more")
    
    conn_before.close()
    conn_after.close()
    
    print("\n" + "=" * 80)
    print("Import completed successfully!")


if __name__ == '__main__':
    import glob
    
    # Find the backup file
    backup_files = sorted(glob.glob('/home/viblio/family_films/db_backup_*.sqlite3'))
    if not backup_files:
        print("No backup file found!")
        sys.exit(1)
    
    backup_path = backup_files[-1]  # Most recent backup
    current_path = '/home/viblio/family_films/db.sqlite3'
    
    print_comparison_report(backup_path, current_path)
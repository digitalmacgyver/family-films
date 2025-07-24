#!/usr/bin/env python
"""
Generate a report showing what metadata would be imported from Excel files
"""
import os
import sys
import django
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

# Setup Django
sys.path.insert(0, '/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Chapter, Person, Location, Tag


def extract_bitfield_key(df):
    """Extract bitfield key from row 8"""
    for col in range(len(df.columns)):
        cell_value = str(df.iloc[7, col]) if not pd.isna(df.iloc[7, col]) else ''
        if 'bitfield:' in cell_value.lower():
            match = re.search(r'Bitfield:\s*(.+)', cell_value, re.IGNORECASE)
            if match:
                names = [name.strip() for name in match.group(1).split(',')]
                return names
    return []


def find_header_row(df):
    """Find the row containing headers"""
    for idx in range(5, min(15, len(df))):
        row = df.iloc[idx]
        row_str = ' '.join(str(cell).lower() for cell in row if pd.notna(cell))
        if 'start' in row_str and 'title' in row_str:
            return idx
    return None


def parse_time_to_seconds(time_str):
    """Convert MM:SS or HH:MM:SS to seconds"""
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0


def find_matching_chapter(film, title, timecode):
    """Find chapter by title similarity and/or timecode match"""
    chapters = film.chapters.all()
    
    # First try exact title match
    exact_match = chapters.filter(title__iexact=title).first()
    if exact_match:
        return exact_match
    
    # Try timecode match
    if timecode:
        seconds = parse_time_to_seconds(timecode)
        timecode_match = chapters.filter(
            start_time_seconds__gte=seconds-2,
            start_time_seconds__lte=seconds+2
        ).first()
        if timecode_match:
            return timecode_match
    
    # Try partial title match
    title_words = title.lower().split()
    for chapter in chapters:
        chapter_words = chapter.title.lower().split()
        common_words = set(title_words) & set(chapter_words)
        if len(common_words) >= min(3, len(title_words) // 2):
            return chapter
    
    return None


def parse_bitfield_people(bitfield, bitfield_key):
    """Parse bitfield and return list of people names"""
    people = []
    if bitfield and len(bitfield) == len(bitfield_key):
        for idx, (bit, name) in enumerate(zip(bitfield, bitfield_key)):
            if bit == '1':
                people.append(name)
    return people


def parse_locations(locations_str):
    """Parse locations string"""
    if not locations_str or pd.isna(locations_str):
        return []
    locations = re.split(r'[,;/]|\sand\s', str(locations_str))
    return [loc.strip() for loc in locations if loc.strip()]


def parse_other_people(other_people_str):
    """Parse other people string"""
    if not other_people_str or pd.isna(other_people_str):
        return []
    people = re.split(r'[,;/]|\sand\s', str(other_people_str))
    return [p.strip() for p in people if p.strip()]


def generate_report():
    """Generate report of what would be imported"""
    sheet_dir = Path('/home/viblio/family_films/chapter_sheets')
    files = list(sheet_dir.glob('*.xls'))
    
    report_data = []
    
    for file_path in sorted(files):
        if file_path.name == 'README.txt.docx':
            continue
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, header=None)
            
            # Extract film ID
            film_id_cell = str(df.iloc[2, 0]) if not pd.isna(df.iloc[2, 0]) else ''
            film_id_prefix = film_id_cell.strip()
            
            if not film_id_prefix:
                continue
            
            # Find matching film
            films = Film.objects.filter(file_id__startswith=film_id_prefix)
            if not films.exists() or films.count() > 1:
                continue
            
            film = films.first()
            
            # Extract bitfield key
            bitfield_key = extract_bitfield_key(df)
            
            # Find header row
            header_row_idx = find_header_row(df)
            if header_row_idx is None:
                continue
            
            # Process data rows
            headers = df.iloc[header_row_idx].str.lower().str.strip()
            header_map = {col: idx for idx, col in enumerate(headers) if pd.notna(col)}
            
            for idx in range(header_row_idx + 1, len(df)):
                row = df.iloc[idx]
                
                # Extract data
                title = str(row[header_map.get('title', 0)]).strip() if not pd.isna(row[header_map.get('title', 0)]) else ''
                if not title:
                    continue
                
                fps16_timecode = str(row[header_map.get('16fps start timecode', 0)]).strip() if '16fps start timecode' in header_map else ''
                
                # Find matching chapter
                chapter = find_matching_chapter(film, title, fps16_timecode)
                if not chapter:
                    continue
                
                # Collect new metadata
                new_data = {
                    'film_id': film.file_id,
                    'film_title': film.title[:50] + '...' if len(film.title) > 50 else film.title,
                    'chapter_title': chapter.title[:40] + '...' if len(chapter.title) > 40 else chapter.title,
                    'current_description': chapter.description[:30] + '...' if chapter.description and len(chapter.description) > 30 else chapter.description or '',
                    'new_description': '',
                    'current_year': chapter.years or '',
                    'new_year': '',
                    'current_people': ', '.join([p.full_name() for p in chapter.people.all()]) or '',
                    'new_people': '',
                    'current_locations': ', '.join([l.name for l in chapter.locations.all()]) or '',
                    'new_locations': ''
                }
                
                # New description
                description = str(row[header_map.get('description', 0)]).strip() if 'description' in header_map and not pd.isna(row[header_map.get('description', 0)]) else ''
                technical_notes = str(row[header_map.get('technical notes', 0)]).strip() if 'technical notes' in header_map and not pd.isna(row[header_map.get('technical notes', 0)]) else ''
                if description or technical_notes:
                    combined = '\n'.join(filter(None, [description, technical_notes]))
                    new_data['new_description'] = combined[:30] + '...' if len(combined) > 30 else combined
                
                # New year
                year_data = str(row[header_map.get('year', 0)]).strip() if 'year' in header_map and not pd.isna(row[header_map.get('year', 0)]) else ''
                if year_data:
                    new_data['new_year'] = year_data
                
                # New people
                people_list = []
                if 'haywards present' in header_map and bitfield_key:
                    bitfield = str(row[header_map['haywards present']]).strip()
                    people_list.extend(parse_bitfield_people(bitfield, bitfield_key))
                
                if 'other people' in header_map:
                    other_people_str = str(row[header_map['other people']]).strip() if not pd.isna(row[header_map['other people']]) else ''
                    people_list.extend(parse_other_people(other_people_str))
                
                if people_list:
                    new_data['new_people'] = ', '.join(people_list)
                
                # New locations
                if 'locations' in header_map:
                    locations_str = str(row[header_map['locations']]).strip() if not pd.isna(row[header_map['locations']]) else ''
                    locations = parse_locations(locations_str)
                    if locations:
                        new_data['new_locations'] = ', '.join(locations)
                
                # Only add if there's new data
                if any([new_data['new_description'], new_data['new_year'], new_data['new_people'], new_data['new_locations']]):
                    report_data.append(new_data)
        
        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")
            continue
    
    return report_data


def print_report(report_data):
    """Print report in tabular format"""
    print("\nCHAPTER METADATA IMPORT PREVIEW REPORT")
    print("=" * 150)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total changes to be applied: {len(report_data)}")
    print("\n")
    
    if not report_data:
        print("No changes would be applied.")
        return
    
    # Group by film
    from itertools import groupby
    
    for film_id, film_chapters in groupby(report_data, key=lambda x: x['film_id']):
        film_chapters = list(film_chapters)
        print(f"\n{'='*150}")
        print(f"FILM: {film_id} - {film_chapters[0]['film_title']}")
        print(f"{'='*150}\n")
        
        # Print headers
        print(f"{'Chapter':<45} | {'Field':<12} | {'Current Value':<40} | {'New Value':<40}")
        print(f"{'-'*45}-+-{'-'*12}-+-{'-'*40}-+-{'-'*40}")
        
        for chapter in film_chapters:
            # Print each field that has changes
            fields_to_check = [
                ('Description', 'current_description', 'new_description'),
                ('Year', 'current_year', 'new_year'),
                ('People', 'current_people', 'new_people'),
                ('Locations', 'current_locations', 'new_locations')
            ]
            
            first_field = True
            for field_name, current_key, new_key in fields_to_check:
                if chapter[new_key]:
                    chapter_title = chapter['chapter_title'] if first_field else ''
                    print(f"{chapter_title:<45} | {field_name:<12} | {chapter[current_key]:<40} | {chapter[new_key]:<40}")
                    first_field = False
            
            if not first_field:  # If we printed any fields, add a separator
                print(f"{'-'*45}-+-{'-'*12}-+-{'-'*40}-+-{'-'*40}")


if __name__ == '__main__':
    print("Analyzing Excel files for metadata import...")
    report_data = generate_report()
    print_report(report_data)
    
    print(f"\n\nSummary: {len(report_data)} chapter updates would be applied.")
    print("\nTo apply these changes, run:")
    print("  python manage.py import_chapter_metadata")
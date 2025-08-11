#!/usr/bin/env python3
"""
Batch D Chapter Processor

Creates chapters for Batch D films from Excel files and processes all metadata:
- Chapter creation with start times
- People relationships from bitfield and Other People column
- Location relationships
- Year relationships
- Chapter thumbnail extraction and processing
"""

import os
import sys
import django
import pandas as pd
import re
import subprocess
from pathlib import Path
from datetime import timedelta

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Chapter, Person, Location, Tag, ChapterPeople, ChapterLocations, ChapterTags
from django.db import transaction

class BatchDChapterProcessor:
    def __init__(self):
        self.chapter_sheets_dir = Path('/home/viblio/family_films/chapter_sheets')
        self.thumbnail_dir = Path('/home/viblio/family_films/main/static/thumbnails/chapters')
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard Hayward family bitfield mapping
        self.hayward_bitfield_map = {
            0: "John Hayward Jr",
            1: "Linda Hayward (nee Thompson)", 
            2: "Jonathan Hayward",
            3: "Matthew Hayward"
        }
        
        self.stats = {
            'files_processed': 0,
            'chapters_created': 0,
            'people_relationships': 0,
            'location_relationships': 0,
            'thumbnails_extracted': 0,
            'errors': 0
        }

    def get_batch_d_excel_files(self):
        """Get list of Excel files for Batch D films"""
        batch_d_patterns = [
            '75-SLD_FROS', '76A-SLD_FROS', '76B-SLD_FROS', '76C-SLD_FROS', 
            '76D-SLD_FROS', '76E-SLD_FROS', '77-SLD_FROS', 'RLD-R01_FROS', 
            'RLD-R02_FROS', 'SLD-01_FROS', 'SLD-02_FROS', 'SLD-03_FROS', 
            'SLD-04_FROS', 'SLD-05_FROS', 'SLD-06_FROS', 'SLD-07_FROS', 
            'SLD-08_FROS', 'SLD-09_FROS', 'SLD-10_FROS', 'SLD-11_FROS', 
            'SLD-12_FROS', 'SLD-13_FROS', 'SLD-14_FROS', 'SLD-15_FROS', 
            'SLD-16_FROS', 'SLD-17_FROS', 'SLD-18_FROS', 'SLD-19_FROS', 
            'SLD-20_FROS', 'SLD-21_FROS', 'SLD-22_FROS', 'SLD-R01_FROS', 
            'SLD-R02_FROS', 'SLD-R03_FROS', 'SLD-R04_FROS'
        ]
        
        excel_files = []
        for pattern in batch_d_patterns:
            matching_files = list(self.chapter_sheets_dir.glob(f'{pattern}*.xls'))
            excel_files.extend(matching_files)
        
        return sorted(excel_files)

    def parse_time_to_seconds(self, time_str):
        """Parse MM:SS or HH:MM:SS or seconds to total seconds"""
        if not time_str or str(time_str).strip() == '':
            return 0
        
        time_str = str(time_str).strip()
        
        # If it's already a number (seconds)
        if time_str.replace('.', '').isdigit():
            return int(float(time_str))
        
        # Parse MM:SS or HH:MM:SS format
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError):
            pass
        
        return 0

    def extract_film_id_from_file(self, file_path):
        """Extract film ID from Excel file"""
        try:
            df = pd.read_excel(file_path, header=None)
            
            # Check row 3 (index 2) for film ID
            if len(df) > 2:
                cell_value = str(df.iloc[2, 0]).strip()
                # Extract just the film ID part before any dash or description
                film_id = cell_value.split(' - ')[0].strip()
                return film_id
        except Exception:
            pass
        
        # Fallback: extract from filename
        filename = file_path.stem
        parts = filename.split(' - ')
        if parts:
            return parts[0].strip()
        
        return None

    def find_header_row(self, df):
        """Find the row containing headers like 'Start', 'End', 'Title', etc."""
        for idx in range(5, min(15, len(df))):
            row = df.iloc[idx]
            row_str = ' '.join(str(cell).lower() for cell in row if pd.notna(cell))
            if 'start' in row_str and 'title' in row_str:
                return idx
        return None

    def extract_bitfield_key(self, df):
        """Extract bitfield key from row around index 7"""
        for idx in range(5, min(10, len(df))):
            for col in range(min(10, len(df.columns))):
                cell_value = str(df.iloc[idx, col]).strip() if not pd.isna(df.iloc[idx, col]) else ''
                if 'bitfield:' in cell_value.lower():
                    # Extract names after "Bitfield:"
                    match = re.search(r'Bitfield:\s*(.+)', cell_value, re.IGNORECASE)
                    if match:
                        names = [name.strip() for name in match.group(1).split(',')]
                        return names
        return []

    def find_or_create_person(self, name):
        """Find existing person or create new one"""
        if not name or not name.strip():
            return None
            
        name = name.strip()
        
        # Handle special name cases
        name_mappings = {
            'John Jr': 'John Hayward Jr',
            'Linda': 'Linda Hayward (nee Thompson)',
            'Jonathan': 'Jonathan Hayward', 
            'Matthew': 'Matthew Hayward'
        }
        
        if name in name_mappings:
            name = name_mappings[name]
        
        # Try to find existing person (case-insensitive search on full name)
        persons = Person.objects.filter(
            first_name__iexact=name.split()[0] if name.split() else name,
            last_name__iexact=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
        )
        
        if persons.exists():
            return persons.first()
        
        # Create new person
        parts = name.split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = ' '.join(parts[1:])
        else:
            first_name = name
            last_name = ''
        
        return Person.objects.create(
            first_name=first_name,
            last_name=last_name
        )

    def find_or_create_location(self, location_name):
        """Find existing location or create new one"""
        if not location_name or not location_name.strip():
            return None
            
        location_name = location_name.strip()
        
        # Try to find existing location (case-insensitive)
        location = Location.objects.filter(name__iexact=location_name).first()
        if location:
            return location
        
        # Create new location
        return Location.objects.create(name=location_name)

    def process_hayward_bitfield(self, chapter, bitfield, bitfield_key=None):
        """Process Hayward family bitfield (e.g., '0110') and add people to chapter"""
        if not bitfield or len(bitfield) != 4:
            return
        
        # Use provided bitfield key or default mapping
        if bitfield_key and len(bitfield_key) == 4:
            name_mapping = {i: name for i, name in enumerate(bitfield_key)}
        else:
            name_mapping = self.hayward_bitfield_map
        
        for idx, bit in enumerate(bitfield):
            if bit == '1' and idx in name_mapping:
                person = self.find_or_create_person(name_mapping[idx])
                if person:
                    ChapterPeople.objects.get_or_create(
                        chapter=chapter,
                        person=person,
                        defaults={'is_primary': True}
                    )
                    self.stats['people_relationships'] += 1

    def process_other_people(self, chapter, people_str):
        """Process comma-separated list of other people"""
        if not people_str or str(people_str).strip() == 'nan':
            return
        
        people_list = re.split(r'[,;/]|\sand\s', str(people_str))
        for person_name in people_list:
            person_name = person_name.strip()
            if person_name and person_name.lower() not in ['nan', 'unknown']:
                person = self.find_or_create_person(person_name)
                if person:
                    ChapterPeople.objects.get_or_create(
                        chapter=chapter,
                        person=person,
                        defaults={'is_primary': False}
                    )
                    self.stats['people_relationships'] += 1

    def process_locations(self, chapter, locations_str):
        """Process comma-separated list of locations"""
        if not locations_str or str(locations_str).strip() == 'nan':
            return
        
        locations_list = re.split(r'[,;/]|\sand\s', str(locations_str))
        for location_name in locations_list:
            location_name = location_name.strip()
            if location_name and location_name.lower() not in ['nan', 'unknown']:
                location = self.find_or_create_location(location_name)
                if location:
                    ChapterLocations.objects.get_or_create(
                        chapter=chapter,
                        location=location,
                        defaults={'is_primary': False}
                    )
                    self.stats['location_relationships'] += 1

    def extract_images_from_excel(self, excel_file, film_id):
        """Extract images from Excel file using the XLS image extractor"""
        try:
            # Create output directory for this film
            output_dir = self.thumbnail_dir / film_id
            output_dir.mkdir(exist_ok=True)
            
            # Use the existing XLS image extractor
            extractor_path = Path('/home/viblio/family_films/xls_image_extractor.py')
            if not extractor_path.exists():
                print(f"    ⚠️ XLS image extractor not found at {extractor_path}")
                return []
            
            result = subprocess.run([
                'python', str(extractor_path), str(excel_file), '-o', str(output_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Find extracted images
                extracted_files = []
                for i in range(50):  # Check up to 50 images
                    image_path = output_dir / f"{excel_file.stem}_image_{i:03d}.jpg"
                    if image_path.exists():
                        extracted_files.append(image_path)
                
                print(f"    📷 Extracted {len(extracted_files)} images")
                self.stats['thumbnails_extracted'] += len(extracted_files)
                return extracted_files
            else:
                print(f"    ❌ Image extraction failed: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"    ❌ Error extracting images: {e}")
            return []

    def process_excel_file(self, file_path):
        """Process a single Excel file and create chapters"""
        print(f"\n📁 Processing: {file_path.name}")
        
        try:
            # Extract film ID
            film_id = self.extract_film_id_from_file(file_path)
            if not film_id:
                print(f"    ❌ Could not extract film ID")
                self.stats['errors'] += 1
                return
            
            # Find film in database
            try:
                film = Film.objects.get(file_id=film_id)
                print(f"    🎬 Found film: {film_id} - {film.title}")
            except Film.DoesNotExist:
                print(f"    ❌ Film not found in database: {film_id}")
                self.stats['errors'] += 1
                return
            
            # Read Excel file
            df = pd.read_excel(file_path, header=None)
            
            # Extract bitfield key
            bitfield_key = self.extract_bitfield_key(df)
            print(f"    🔑 Bitfield key: {bitfield_key}")
            
            # Find header row
            header_row_idx = self.find_header_row(df)
            if header_row_idx is None:
                print(f"    ❌ Could not find header row")
                self.stats['errors'] += 1
                return
            
            # Extract images first (all images should be from Start column A)
            extracted_images = self.extract_images_from_excel(file_path, film_id)
            # Use all extracted images since they should be from column A (Start column)
            start_column_images = extracted_images
            
            # Process data rows
            headers = df.iloc[header_row_idx].str.lower().str.strip()
            header_map = {col: idx for idx, col in enumerate(headers) if pd.notna(col)}
            
            print(f"    📋 Headers found: {list(header_map.keys())}")
            
            chapters_created = 0
            
            # Process each chapter row
            for row_idx in range(header_row_idx + 1, len(df)):
                row = df.iloc[row_idx]
                
                # Skip empty rows
                title_col = header_map.get('title', 2)  # Default to column 2
                if pd.isna(row[title_col]) or not str(row[title_col]).strip():
                    continue
                
                with transaction.atomic():
                    chapter = self.create_chapter_from_row(film, row, header_map, bitfield_key, start_column_images, chapters_created)
                    if chapter:
                        chapters_created += 1
            
            print(f"    ✅ Created {chapters_created} chapters")
            self.stats['chapters_created'] += chapters_created
            self.stats['files_processed'] += 1
            
        except Exception as e:
            print(f"    ❌ Error processing file: {e}")
            self.stats['errors'] += 1

    def create_chapter_from_row(self, film, row, header_map, bitfield_key, extracted_images, chapter_index):
        """Create a single chapter from Excel row data"""
        try:
            # Extract basic chapter data
            title = str(row[header_map.get('title', 2)]).strip()
            
            # Handle description - check for NaN first
            description = ''
            if header_map.get('description') is not None and not pd.isna(row[header_map.get('description')]):
                desc_val = row[header_map.get('description')]
                description = str(desc_val).strip() if desc_val != 'nan' else ''
            
            # Handle technical notes - check for NaN first  
            technical_notes = ''
            if header_map.get('technical notes') is not None and not pd.isna(row[header_map.get('technical notes')]):
                tech_val = row[header_map.get('technical notes')]
                technical_notes = str(tech_val).strip() if tech_val != 'nan' else ''
            
            # Parse start time - check multiple columns
            start_seconds = 0
            if header_map.get('18fps start seconds') and not pd.isna(row[header_map.get('18fps start seconds')]):
                start_seconds = int(float(row[header_map.get('18fps start seconds')]))
            elif header_map.get('16fps start seconds') and not pd.isna(row[header_map.get('16fps start seconds')]):  
                start_seconds = int(float(row[header_map.get('16fps start seconds')]))
            elif header_map.get('18fps start timecode') and not pd.isna(row[header_map.get('18fps start timecode')]):
                start_seconds = self.parse_time_to_seconds(row[header_map.get('18fps start timecode')])
            elif header_map.get('16fps start timecode') and not pd.isna(row[header_map.get('16fps start timecode')]):
                start_seconds = self.parse_time_to_seconds(row[header_map.get('16fps start timecode')])
            
            # Create combined description
            combined_description = '\n'.join(filter(None, [description, technical_notes]))
            
            # Handle year data - check for NaN first
            year_data = ''
            if header_map.get('year') is not None and not pd.isna(row[header_map.get('year')]):
                year_val = row[header_map.get('year')]
                year_data = str(year_val).strip() if year_val != 'nan' else ''
            
            # Create start_time string in MM:SS format
            start_time_str = f"{start_seconds // 60:02d}:{start_seconds % 60:02d}"
            
            # Create chapter
            chapter = Chapter.objects.create(
                film=film,
                title=title,
                description=combined_description,
                start_time=start_time_str,
                order=chapter_index + 1,
                years=year_data if year_data and year_data != 'nan' else ''
            )
            
            print(f"      📝 Created: {title} ({start_seconds}s)")
            
            # Process Hayward bitfield
            haywards_col = header_map.get('haywards present', 5)
            if haywards_col is not None and not pd.isna(row[haywards_col]):
                bitfield_val = row[haywards_col]
                bitfield = str(bitfield_val).strip()
                if bitfield and bitfield != 'nan' and bitfield != 'nan':
                    self.process_hayward_bitfield(chapter, bitfield, bitfield_key)
            
            # Process locations
            locations_col = header_map.get('locations', 6)
            if locations_col is not None and not pd.isna(row[locations_col]):
                locations_val = row[locations_col]
                locations_str = str(locations_val).strip()
                if locations_str and locations_str != 'nan':
                    self.process_locations(chapter, locations_str)
            
            # Process other people
            other_people_col = header_map.get('other people', 9)
            if other_people_col is not None and not pd.isna(row[other_people_col]):
                people_val = row[other_people_col]
                other_people_str = str(people_val).strip()
                if other_people_str and other_people_str != 'nan':
                    self.process_other_people(chapter, other_people_str)
            
            # Assign chapter thumbnail if available
            if extracted_images and chapter_index < len(extracted_images):
                self.assign_chapter_thumbnail(chapter, extracted_images[chapter_index])
            
            return chapter
            
        except Exception as e:
            print(f"      ❌ Error creating chapter: {e}")
            return None

    def assign_chapter_thumbnail(self, chapter, image_path):
        """Assign extracted image as chapter thumbnail"""
        try:
            # Create meaningful filename
            filename = f"{chapter.film.file_id}_ch{chapter.order:02d}_{chapter.start_time_seconds}s.jpg"
            dest_path = self.thumbnail_dir / filename
            
            # Copy image to thumbnails directory
            import shutil
            shutil.copy2(image_path, dest_path)
            
            # Update chapter with thumbnail URL
            chapter.thumbnail_url = f"/static/thumbnails/chapters/{filename}"
            chapter.save()
            
            print(f"      📷 Thumbnail: {filename}")
            
        except Exception as e:
            print(f"      ❌ Error assigning thumbnail: {e}")

    def process_all_batch_d_films(self):
        """Process all Batch D Excel files"""
        print("=== BATCH D CHAPTER PROCESSOR ===\n")
        
        excel_files = self.get_batch_d_excel_files()
        print(f"Found {len(excel_files)} Batch D Excel files to process\n")
        
        for file_path in excel_files:
            self.process_excel_file(file_path)
        
        self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("BATCH D CHAPTER PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Excel files processed: {self.stats['files_processed']}")
        print(f"Chapters created: {self.stats['chapters_created']}")
        print(f"People relationships: {self.stats['people_relationships']}")
        print(f"Location relationships: {self.stats['location_relationships']}")
        print(f"Thumbnails extracted: {self.stats['thumbnails_extracted']}")
        print(f"Errors: {self.stats['errors']}")

def main():
    processor = BatchDChapterProcessor()
    processor.process_all_batch_d_films()
    return 0

if __name__ == "__main__":
    sys.exit(main())
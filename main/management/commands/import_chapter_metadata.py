import os
import re
import subprocess
import shutil
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Film, Chapter, Person, Location, Tag, ChapterPeople, ChapterLocations, ChapterTags
import pandas as pd
import openpyxl
from openpyxl_image_loader import SheetImageLoader
from datetime import timedelta
from pathlib import Path


class Command(BaseCommand):
    help = 'Import chapter metadata from Excel spreadsheets in chapter_sheets directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Process only a specific Excel file (filename only, not path)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--save-thumbnails',
            type=str,
            default='static/thumbnails/chapters',
            help='Directory to save extracted thumbnail images',
        )

    def handle(self, *args, **options):
        sheet_dir = Path('/home/viblio/family_films/chapter_sheets')
        
        if options['file']:
            files = [sheet_dir / options['file']]
        else:
            files = list(sheet_dir.glob('*.xls'))
        
        self.stdout.write(f"Found {len(files)} Excel files to process")
        
        for file_path in files:
            if file_path.name == 'README.txt.docx':
                continue
                
            self.stdout.write(f"\nProcessing: {file_path.name}")
            try:
                self.process_excel_file(file_path, options['dry_run'], options['save_thumbnails'])
            except Exception as e:
                self.stderr.write(f"Error processing {file_path.name}: {str(e)}")
    
    def process_excel_file(self, file_path, dry_run, thumbnail_dir):
        # Read Excel file
        df = pd.read_excel(file_path, header=None)
        
        # Extract film ID from cell A3
        film_id_cell = str(df.iloc[2, 0]) if not pd.isna(df.iloc[2, 0]) else ''
        film_id_prefix = film_id_cell.strip()
        
        if not film_id_prefix:
            self.stderr.write(f"No film ID found in cell A3 of {file_path.name}")
            return
        
        # Find matching film in database
        films = Film.objects.filter(file_id__startswith=film_id_prefix)
        if not films.exists():
            self.stderr.write(f"No film found with ID starting with '{film_id_prefix}'")
            return
        elif films.count() > 1:
            self.stderr.write(f"Multiple films found with ID starting with '{film_id_prefix}': {list(films.values_list('file_id', flat=True))}")
            return
        
        film = films.first()
        self.stdout.write(f"Found film: {film.file_id} - {film.title}")
        
        # Extract bitfield key from row 8
        bitfield_key = self.extract_bitfield_key(df)
        
        # Find header row (typically around row 9)
        header_row_idx = self.find_header_row(df)
        if header_row_idx is None:
            self.stderr.write("Could not find header row")
            return
        
        # Process data rows
        headers = df.iloc[header_row_idx].str.lower().str.strip()
        header_map = {col: idx for idx, col in enumerate(headers) if pd.notna(col)}
        
        # Extract images from Excel file
        extracted_images = None
        image_loader = None
        
        if file_path.suffix.lower() == '.xls':
            # Extract images using binary parsing for .xls files
            try:
                all_extracted_images = self.extract_images_from_xls(file_path, thumbnail_dir)
                # Filter to only use Start column images (every other image, starting from index 0)
                extracted_images = [img for i, img in enumerate(all_extracted_images) if i % 2 == 0]
                if extracted_images:
                    self.stdout.write(f"Extracted {len(all_extracted_images)} images total, using {len(extracted_images)} from Start column")
            except Exception as e:
                self.stdout.write(f"Note: Could not extract images from .xls file: {str(e)}")
        
        elif file_path.suffix.lower() == '.xlsx':
            try:
                wb = openpyxl.load_workbook(file_path)
                sheet = wb.active
                image_loader = SheetImageLoader(sheet)
            except Exception as e:
                self.stdout.write(f"Note: Could not load images from Excel file: {str(e)}")
        
        processed_count = 0
        for idx in range(header_row_idx + 1, len(df)):
            row = df.iloc[idx]
            
            # Skip empty rows
            if pd.isna(row[header_map.get('title', 0)]):
                continue
            
            if not dry_run:
                with transaction.atomic():
                    self.process_chapter_row(
                        film, row, header_map, bitfield_key, 
                        image_loader, idx + 1, thumbnail_dir, extracted_images  # +1 for Excel row number
                    )
            else:
                self.stdout.write(f"[DRY RUN] Would process chapter: {row[header_map.get('title', 0)]}")
            
            processed_count += 1
        
        self.stdout.write(f"Processed {processed_count} chapters for {film.file_id}")
    
    def extract_bitfield_key(self, df):
        """Extract bitfield key from row 8, typically in column 5"""
        bitfield_info = None
        for col in range(len(df.columns)):
            cell_value = str(df.iloc[7, col]) if not pd.isna(df.iloc[7, col]) else ''
            if 'bitfield:' in cell_value.lower():
                bitfield_info = cell_value
                break
        
        if not bitfield_info:
            return []
        
        # Extract names from "Bitfield: John Sr, Josephine, ..."
        match = re.search(r'Bitfield:\s*(.+)', bitfield_info, re.IGNORECASE)
        if match:
            names = [name.strip() for name in match.group(1).split(',')]
            return names
        
        return []
    
    def find_header_row(self, df):
        """Find the row containing headers like 'Start', 'End', 'Title', etc."""
        for idx in range(5, min(15, len(df))):  # Check rows 6-15
            row = df.iloc[idx]
            row_str = ' '.join(str(cell).lower() for cell in row if pd.notna(cell))
            if 'start' in row_str and 'title' in row_str:
                return idx
        return None
    
    def process_chapter_row(self, film, row, header_map, bitfield_key, image_loader, excel_row_num, thumbnail_dir, extracted_images=None):
        """Process a single chapter row from the Excel file"""
        
        # Extract data from row
        title = str(row[header_map.get('title', 0)]).strip() if not pd.isna(row[header_map.get('title', 0)]) else ''
        if not title:
            return
        
        # Get 16fps start timecode for matching
        fps16_timecode = str(row[header_map.get('16fps start timecode', 0)]).strip() if '16fps start timecode' in header_map else ''
        
        # Find matching chapter by title and/or timecode
        chapter = self.find_matching_chapter(film, title, fps16_timecode)
        if not chapter:
            self.stderr.write(f"No matching chapter found for '{title}' at {fps16_timecode}")
            return
        
        self.stdout.write(f"Updating chapter: {chapter.title}")
        
        # Update description
        description = str(row[header_map.get('description', 0)]).strip() if 'description' in header_map and not pd.isna(row[header_map.get('description', 0)]) else ''
        technical_notes = str(row[header_map.get('technical notes', 0)]).strip() if 'technical notes' in header_map and not pd.isna(row[header_map.get('technical notes', 0)]) else ''
        
        if description or technical_notes:
            combined_description = '\n'.join(filter(None, [description, technical_notes]))
            chapter.description = combined_description
            chapter.save()
        
        # Update year
        year_data = str(row[header_map.get('year', 0)]).strip() if 'year' in header_map and not pd.isna(row[header_map.get('year', 0)]) else ''
        if year_data:
            chapter.years = year_data
            chapter.save()
        
        # Process Haywards Present bitfield
        if 'haywards present' in header_map and bitfield_key:
            bitfield = str(row[header_map['haywards present']]).strip()
            if bitfield and len(bitfield) == len(bitfield_key):
                self.process_haywards_bitfield(chapter, bitfield, bitfield_key)
        
        # Process locations
        if 'locations' in header_map:
            locations_str = str(row[header_map['locations']]).strip() if not pd.isna(row[header_map['locations']]) else ''
            if locations_str:
                self.process_locations(chapter, locations_str)
        
        # Process tags
        if 'tags' in header_map:
            tags_str = str(row[header_map['tags']]).strip() if not pd.isna(row[header_map['tags']]) else ''
            if tags_str:
                self.process_tags(chapter, tags_str)
        
        # Process other people
        if 'other people' in header_map:
            other_people_str = str(row[header_map['other people']]).strip() if not pd.isna(row[header_map['other people']]) else ''
            if other_people_str:
                self.process_other_people(chapter, other_people_str)
        
        # Extract thumbnail image from Start column
        if 'start' in header_map:
            chapter_row_index = excel_row_num - (self.find_header_row_index(film) + 2)  # Adjust for header offset
            
            if image_loader:  # .xlsx file
                start_col_letter = openpyxl.utils.get_column_letter(header_map['start'] + 1)
                cell_coord = f"{start_col_letter}{excel_row_num}"
                
                if image_loader.image_in(cell_coord):
                    self.extract_thumbnail_xlsx(chapter, image_loader, cell_coord, thumbnail_dir)
            
            elif extracted_images and chapter_row_index < len(extracted_images):  # .xls file
                # Use the extracted image for this chapter
                image_path = extracted_images[chapter_row_index]
                self.assign_extracted_thumbnail(chapter, image_path, thumbnail_dir)
        
        # Update metadata flags
        chapter.update_metadata_flags()
    
    def find_matching_chapter(self, film, title, timecode):
        """Find chapter by title similarity and/or timecode match"""
        chapters = film.chapters.all()
        
        # First try exact title match
        exact_match = chapters.filter(title__iexact=title).first()
        if exact_match:
            return exact_match
        
        # Try timecode match (convert MM:SS or HH:MM:SS to seconds)
        if timecode:
            try:
                seconds = Chapter.parse_time_to_seconds(timecode)
                # Allow 2 second tolerance
                timecode_match = chapters.filter(
                    start_time_seconds__gte=seconds-2,
                    start_time_seconds__lte=seconds+2
                ).first()
                if timecode_match:
                    return timecode_match
            except:
                pass
        
        # Try partial title match
        title_words = title.lower().split()
        for chapter in chapters:
            chapter_words = chapter.title.lower().split()
            # If significant overlap in words, consider it a match
            common_words = set(title_words) & set(chapter_words)
            if len(common_words) >= min(3, len(title_words) // 2):
                return chapter
        
        return None
    
    def process_haywards_bitfield(self, chapter, bitfield, bitfield_key):
        """Process the Haywards Present bitfield and add people to chapter"""
        for idx, (bit, name) in enumerate(zip(bitfield, bitfield_key)):
            if bit == '1':
                # Find or create person
                person = self.find_or_create_person(name, hayward_index=idx)
                ChapterPeople.objects.get_or_create(
                    chapter=chapter,
                    person=person,
                    defaults={'is_primary': False}
                )
    
    def find_or_create_person(self, name, hayward_index=None):
        """Find existing person or create new one"""
        # Parse name (handle "John Sr", "John Jr", etc.)
        parts = name.strip().split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = ' '.join(parts[1:])
        else:
            first_name = name
            # For Hayward family members without last name in bitfield, default to Hayward
            last_name = 'Hayward' if hayward_index is not None else ''
        
        # Try to find existing person
        if hayward_index is not None:
            person = Person.objects.filter(hayward_index=hayward_index).first()
            if person:
                return person
        
        # Try by name
        person = Person.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name
        ).first()
        
        if person:
            # Update hayward_index if not set
            if hayward_index is not None and person.hayward_index is None:
                person.hayward_index = hayward_index
                person.save()
            return person
        
        # Create new person
        return Person.objects.create(
            first_name=first_name,
            last_name=last_name,
            hayward_index=hayward_index
        )
    
    def process_locations(self, chapter, locations_str):
        """Process locations string and add to chapter"""
        # Split by common delimiters
        locations = re.split(r'[,;/]|\sand\s', locations_str)
        
        for location_name in locations:
            location_name = location_name.strip()
            if not location_name:
                continue
            
            # Find or create location
            location, created = Location.objects.get_or_create(
                name__iexact=location_name,
                defaults={'name': location_name}
            )
            
            ChapterLocations.objects.get_or_create(
                chapter=chapter,
                location=location,
                defaults={'is_primary': False}
            )
    
    def process_tags(self, chapter, tags_str):
        """Process tags string and add to chapter"""
        # Split by common delimiters
        tags = re.split(r'[,;/]|\sand\s', tags_str)
        
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            
            # Find or create tag
            tag, created = Tag.objects.get_or_create(
                tag=tag_name
            )
            
            ChapterTags.objects.get_or_create(
                chapter=chapter,
                tag=tag,
                defaults={'is_auto': False}
            )
    
    def process_other_people(self, chapter, other_people_str):
        """Process other people string and add to chapter"""
        # Split by common delimiters
        people = re.split(r'[,;/]|\sand\s', other_people_str)
        
        for person_name in people:
            person_name = person_name.strip()
            if not person_name:
                continue
            
            person = self.find_or_create_person(person_name)
            ChapterPeople.objects.get_or_create(
                chapter=chapter,
                person=person,
                defaults={'is_primary': False}
            )
    
    def extract_images_from_xls(self, xls_file, output_dir):
        """Extract images from .xls file using binary parsing"""
        try:
            # Use the existing XLS image extractor script
            script_path = Path(__file__).parent.parent.parent.parent / 'xls_image_extractor.py'
            
            result = subprocess.run([
                'python', str(script_path), str(xls_file), '-o', output_dir
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse the output to find extracted image paths
                extracted_files = []
                base_name = xls_file.stem
                output_path = Path(output_dir)
                
                # Look for extracted images with the expected naming pattern
                for i in range(20):  # Check up to 20 images
                    image_path = output_path / f"{base_name}_image_{i:03d}.jpg"
                    if image_path.exists():
                        extracted_files.append(str(image_path))
                
                return extracted_files
            else:
                self.stderr.write(f"XLS extraction failed: {result.stderr}")
                return []
        except Exception as e:
            self.stderr.write(f"Error extracting images from XLS: {str(e)}")
            return []
    
    def find_header_row_index(self, film):
        """Find the header row index for this film (helper method)"""
        # This would need to be stored or recalculated - for now return a default
        return 8  # Most Excel files have headers around row 9 (0-indexed as 8)
    
    def extract_thumbnail_xlsx(self, chapter, image_loader, cell_coord, thumbnail_dir):
        """Extract thumbnail image from XLSX Excel cell and save"""
        try:
            image = image_loader.get(cell_coord)
            
            # Create thumbnail directory if needed
            thumb_path = Path(thumbnail_dir)
            thumb_path.mkdir(parents=True, exist_ok=True)
            
            # Save image with meaningful filename
            filename = f"{chapter.film.file_id}_ch{chapter.order:02d}_{chapter.start_time_seconds}s.png"
            filepath = thumb_path / filename
            
            image.save(filepath)
            
            # Update chapter thumbnail URL (relative to static root)
            chapter.thumbnail_url = f"/static/thumbnails/chapters/{filename}"
            chapter.save()
            
            self.stdout.write(f"  Saved thumbnail: {filename}")
        except Exception as e:
            self.stderr.write(f"  Failed to extract thumbnail: {str(e)}")
    
    def assign_extracted_thumbnail(self, chapter, image_path, thumbnail_dir):
        """Assign an extracted image as chapter thumbnail"""
        try:
            # Create thumbnail directory if needed
            thumb_path = Path(thumbnail_dir)
            thumb_path.mkdir(parents=True, exist_ok=True)
            
            # Copy image to thumbnail directory with meaningful filename
            filename = f"{chapter.film.file_id}_ch{chapter.order:02d}_{chapter.start_time_seconds}s.jpg"
            dest_path = thumb_path / filename
            
            shutil.copy2(image_path, dest_path)
            
            # Update chapter thumbnail URL (relative to static root)
            chapter.thumbnail_url = f"/static/thumbnails/chapters/{filename}"
            chapter.save()
            
            self.stdout.write(f"  Assigned thumbnail: {filename}")
        except Exception as e:
            self.stderr.write(f"  Failed to assign thumbnail: {str(e)}")
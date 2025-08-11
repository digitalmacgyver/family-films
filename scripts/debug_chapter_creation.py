#!/usr/bin/env python3
"""Debug chapter creation"""

import os
import sys
import django
import pandas as pd
from datetime import timedelta
from pathlib import Path

sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Chapter

def debug_create_chapter():
    # Read the problematic Excel file
    file_path = Path('/home/viblio/family_films/chapter_sheets/75-SLD_FROS - Baby Jonathan Bathtime Crib and Zoo Visit.xls')
    df = pd.read_excel(file_path, header=None)
    
    # Get the film
    film = Film.objects.get(file_id='75-SLD_FROS')
    
    # Find header row (row 9, index 8)
    header_row_idx = 8
    headers = df.iloc[header_row_idx].str.lower().str.strip()
    header_map = {col: idx for idx, col in enumerate(headers) if pd.notna(col)}
    
    print(f"Headers: {header_map}")
    
    # Process first data row (row 10, index 9)  
    row = df.iloc[9]
    
    print(f"\nRow data:")
    for col_name, col_idx in header_map.items():
        cell_val = row[col_idx]
        print(f"  {col_name} (col {col_idx}): {type(cell_val).__name__} = {repr(cell_val)}")
    
    try:
        # Extract basic data
        title = str(row[header_map.get('title', 2)]).strip()
        print(f"\nTitle: {repr(title)}")
        
        # Handle description
        description = ''
        if header_map.get('description') is not None and not pd.isna(row[header_map.get('description')]):
            desc_val = row[header_map.get('description')]
            print(f"Description raw: {type(desc_val).__name__} = {repr(desc_val)}")
            description = str(desc_val).strip() if desc_val != 'nan' else ''
            print(f"Description processed: {repr(description)}")
        
        # Start time
        start_seconds = 0
        if header_map.get('18fps start seconds') and not pd.isna(row[header_map.get('18fps start seconds')]):
            start_seconds = int(float(row[header_map.get('18fps start seconds')]))
        print(f"Start seconds: {start_seconds}")
        
        # Year
        year_data = ''
        if header_map.get('year') is not None and not pd.isna(row[header_map.get('year')]):
            year_val = row[header_map.get('year')]
            print(f"Year raw: {type(year_val).__name__} = {repr(year_val)}")
            year_data = str(year_val).strip() if year_val != 'nan' else ''
            print(f"Year processed: {repr(year_data)}")
        
        # Attempt chapter creation
        print(f"\nAttempting to create chapter...")
        chapter = Chapter.objects.create(
            film=film,
            title=title,
            description=description,
            start_time_seconds=start_seconds,
            start_time=timedelta(seconds=start_seconds),
            order=1,
            years=year_data if year_data and year_data != 'nan' else ''
        )
        print(f"✅ Chapter created successfully: {chapter.id}")
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(f"Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_create_chapter()
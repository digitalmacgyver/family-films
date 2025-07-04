#!/usr/bin/env python
import csv

# Files that appear in CSV but not in database
missing_files = ['ADS_FROS', 'ADS_FROS-SAFE', 'CART_FROS', 'CART_FROS-SAFE', 'P-CC2_FROS', 'PB-06_FROS', 'RLA-01_FROS', 'RLA-02_FROS', 'RLB-01_FROS', 'SLB-02_FROS']

print('=== CHECKING MISSING FILES IN CSV ===\n')

try:
    with open('family_reunion_movies.csv', 'r', encoding='utf-8') as f:
        # Skip front matter lines until we find the header
        lines = f.readlines()
        header_found = False
        
        for i, line in enumerate(lines):
            if 'Filenames' in line and 'Years' in line and 'People' in line:
                header_found = True
                header_line = line
                data_lines = lines[i+1:]
                break
        
        if header_found:
            # Parse the CSV data
            csv_content = header_line + ''.join(data_lines)
            reader = csv.DictReader(csv_content.splitlines())
            
            found_files = {}
            
            for row_num, row in enumerate(reader, start=1):
                filename = row.get('Filenames', '').strip()
                if filename in missing_files:
                    found_files[filename] = row
                    print(f'FOUND: {filename}')
                    print(f'  Title: {row.get("Title", "").strip()}')
                    print(f'  Years: {row.get("Years", "").strip()}')
                    print(f'  Workflow State: {row.get("Workflow State", "").strip()}')
                    print(f'  Description: {row.get("Description", "")[:100].strip()}...')
                    
                    # Check if it has required fields for import
                    has_title = bool(row.get('Title', '').strip())
                    has_years = bool(row.get('Years', '').strip())
                    
                    print(f'  Has Title: {has_title}')
                    print(f'  Has Years: {has_years}')
                    print(f'  Would be imported: {has_title and has_years and filename}')
                    print()
            
            # Check which files were not found
            not_found = set(missing_files) - set(found_files.keys())
            if not_found:
                print(f'NOT FOUND in CSV: {list(not_found)}')
                
except Exception as e:
    print(f'Error reading CSV: {e}')
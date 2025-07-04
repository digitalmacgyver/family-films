#!/usr/bin/env python
import csv

print('=== EXTRACTING PB-14_FROS RECORD FROM CSV ===\n')

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
            
            for row in reader:
                if row.get('Filenames', '').strip() == 'PB-14_FROS':
                    print('Found PB-14_FROS record:')
                    print('-' * 80)
                    
                    # Print all fields in order
                    for field_name, field_value in row.items():
                        # Clean up the value
                        value = field_value.strip() if field_value else ''
                        
                        # Format multiline values
                        if '\n' in value:
                            print(f'\n* {field_name} :\n{value}\n')
                        else:
                            print(f'* {field_name} : {value}')
                    
                    print('-' * 80)
                    break
            else:
                print('PB-14_FROS not found in CSV')
                
except Exception as e:
    print(f'Error reading CSV: {e}')
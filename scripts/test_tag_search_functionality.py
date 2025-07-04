#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Tag

def test_tag_search_functionality():
    """Test tag search functionality on search by tags page"""
    
    print("=== Testing Tag Search Functionality ===\n")
    
    # Get all tags
    tags = Tag.objects.all()
    print(f"Total tags in database: {tags.count()}")
    
    if tags.count() == 0:
        print("No tags found. Creating test tags...")
        
        # Create some test tags
        test_tags = [
            {'tag': 'Christmas', 'category': 'holidays', 'description': 'Christmas celebrations'},
            {'tag': 'Birthday', 'category': 'events', 'description': 'Birthday parties'},
            {'tag': 'Family', 'category': 'people', 'description': 'Family gatherings'},
            {'tag': 'Vacation', 'category': 'activities', 'description': 'Vacation trips'},
            {'tag': 'TestTag', 'category': 'other', 'description': 'Test tag for autocomplete'},
        ]
        
        for tag_data in test_tags:
            tag, created = Tag.objects.get_or_create(
                tag=tag_data['tag'],
                defaults={
                    'category': tag_data['category'],
                    'description': tag_data['description']
                }
            )
            if created:
                print(f"Created tag: {tag.tag}")
    
    # Show some example tags for testing
    sample_tags = list(tags[:10])
    print(f"\nSample tags for testing autocomplete:")
    for tag in sample_tags:
        print(f"- {tag.tag} ({tag.category})")
    
    print(f"\n✅ Tag search setup complete!")
    print(f"\nTo test:")
    print(f"1. Visit: http://localhost:8000/search/tags/")
    print(f"2. Start typing in the 'Find Tag' input field")
    print(f"3. Verify autocomplete suggestions appear")
    print(f"4. Click on a suggestion or press Enter to search")
    print(f"5. Verify the text stays in the input field (doesn't move to main search)")

if __name__ == '__main__':
    test_tag_search_functionality()
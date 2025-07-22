#!/usr/bin/env python
# Run this script on production to update chapter thumbnail URLs
# Usage: python manage.py shell < exports/update_chapter_thumbnails_prod.py

from main.models import Chapter
import json

print("Updating chapter thumbnail URLs...")

with open('exports/chapter_thumbnail_updates.json', 'r') as f:
    updates = json.load(f)

updated_count = 0
for update in updates:
    try:
        chapter = Chapter.objects.get(id=update['id'])
        chapter.thumbnail_url = update['thumbnail_url']
        chapter.save()
        updated_count += 1
        if updated_count % 50 == 0:
            print(f"Updated {updated_count} chapters...")
    except Chapter.DoesNotExist:
        print(f"Warning: Chapter {update['id']} not found")
    except Exception as e:
        print(f"Error updating chapter {update['id']}: {e}")

print(f"Successfully updated {updated_count} chapter thumbnails")

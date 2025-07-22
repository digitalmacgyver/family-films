import json
from django.core.management.base import BaseCommand
from main.models import Chapter


class Command(BaseCommand):
    help = 'Export chapter thumbnail URL updates as SQL for production'

    def handle(self, *args, **options):
        # Get all chapters with new thumbnail URLs (those containing " - " and "_image_")
        chapters = Chapter.objects.filter(
            thumbnail_url__contains=" - "
        ).filter(
            thumbnail_url__contains="_image_"
        ).select_related('film')
        
        sql_statements = []
        json_data = []
        
        self.stdout.write(f"Found {chapters.count()} chapters with new thumbnail URLs")
        
        for chapter in chapters:
            # Create SQL update statement
            sql = f"UPDATE main_chapter SET thumbnail_url = '{chapter.thumbnail_url}' WHERE id = {chapter.id};"
            sql_statements.append(sql)
            
            # Also create JSON format for alternative update method
            json_data.append({
                'id': chapter.id,
                'film_id': chapter.film.file_id,
                'film_title': chapter.film.title,
                'chapter_title': chapter.title,
                'thumbnail_url': chapter.thumbnail_url
            })
        
        # Write SQL file
        sql_file = 'exports/update_chapter_thumbnails.sql'
        with open(sql_file, 'w') as f:
            f.write("-- SQL script to update chapter thumbnail URLs in production\n")
            f.write("-- Generated from local database after running update_chapter_thumbnails management command\n")
            f.write(f"-- Total updates: {len(sql_statements)}\n\n")
            f.write("BEGIN;\n\n")
            for sql in sql_statements:
                f.write(sql + "\n")
            f.write("\nCOMMIT;\n")
        
        self.stdout.write(self.style.SUCCESS(f"Exported {len(sql_statements)} SQL updates to {sql_file}"))
        
        # Write JSON file
        json_file = 'exports/chapter_thumbnail_updates.json'
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        self.stdout.write(self.style.SUCCESS(f"Exported {len(json_data)} updates to {json_file}"))
        
        # Create a Python script that can be run on production
        py_file = 'exports/update_chapter_thumbnails_prod.py'
        with open(py_file, 'w') as f:
            f.write("""#!/usr/bin/env python
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
""")
        
        self.stdout.write(self.style.SUCCESS(f"Created Python update script at {py_file}"))
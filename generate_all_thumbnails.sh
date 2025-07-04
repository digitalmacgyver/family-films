#!/bin/bash

# Generate animated thumbnails and chapter thumbnails for all films
# This script can be run periodically to generate thumbnails for new films

echo "Starting comprehensive thumbnail generation for all films..."

# Step 1: Generate animated preview thumbnails
echo "=== Generating animated preview thumbnails ==="

# Get list of films without animated thumbnails
python manage.py shell -c "
from main.models import Film
films = Film.objects.exclude(youtube_id__startswith='placeholder_').filter(preview_sprite_url='')
print(' '.join([f.file_id for f in films]))
" > /tmp/films_without_thumbnails.txt

FILM_IDS=$(cat /tmp/films_without_thumbnails.txt)

if [ ! -z "$FILM_IDS" ]; then
    echo "Found $(echo $FILM_IDS | wc -w) films without animated thumbnails"
    
    # Process films in batches to avoid overloading
    for film_id in $FILM_IDS; do
        echo "Generating animated thumbnail for: $film_id"
        python manage.py generate_thumbnail_previews --file-ids "$film_id"
        
        if [ $? -eq 0 ]; then
            echo "✓ Success: $film_id"
        else
            echo "✗ Failed: $film_id"
        fi
        
        # Small delay to be respectful to YouTube
        sleep 1
    done
else
    echo "All films already have animated thumbnails!"
fi

# Step 2: Generate chapter-based thumbnails
echo ""
echo "=== Generating chapter-based thumbnails ==="

# Get list of films without chapter thumbnails
python manage.py shell -c "
from main.models import Film, Chapter
films_needing_chapter_thumbs = []
for film in Film.objects.exclude(youtube_id__startswith='placeholder_'):
    chapters = film.chapters.all()
    if chapters.exists():
        # Check if any chapters are missing thumbnails
        missing_thumbs = chapters.filter(thumbnail_url='')
        if missing_thumbs.exists():
            films_needing_chapter_thumbs.append(film.file_id)
    elif not chapters.exists():
        # Films without chapters should get interval thumbnails
        films_needing_chapter_thumbs.append(film.file_id)
print(' '.join(films_needing_chapter_thumbs))
" > /tmp/films_without_chapter_thumbnails.txt

CHAPTER_FILM_IDS=$(cat /tmp/films_without_chapter_thumbnails.txt)

if [ ! -z "$CHAPTER_FILM_IDS" ]; then
    echo "Found $(echo $CHAPTER_FILM_IDS | wc -w) films needing chapter thumbnails"
    
    for film_id in $CHAPTER_FILM_IDS; do
        echo "Generating chapter thumbnails for: $film_id"
        python manage.py generate_chapter_thumbnails --file-ids "$film_id"
        
        if [ $? -eq 0 ]; then
            echo "✓ Success: $film_id"
        else
            echo "✗ Failed: $film_id"
        fi
        
        # Small delay to be respectful to YouTube
        sleep 1
    done
else
    echo "All films already have chapter thumbnails!"
fi

echo ""
echo "=== Thumbnail Generation Summary ==="
echo "✓ Animated preview thumbnails: Complete"
echo "✓ Chapter-based thumbnails: Complete"
echo ""
echo "Comprehensive thumbnail generation complete!"

# Clean up
rm -f /tmp/films_without_thumbnails.txt
rm -f /tmp/films_without_chapter_thumbnails.txt
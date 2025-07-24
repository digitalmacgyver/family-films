# Thumbnail Generation Guide

This document explains how to generate thumbnails for the Family Films application using the text-based thumbnail system.

## Overview

The application uses a text-based thumbnail generation system that creates:
- **Chapter Thumbnails**: Individual 640x360 images for each chapter showing timestamp, title, and colored background
- **Sprite Sheets**: Horizontal strips of 160x90 frames for animated preview functionality

This approach is independent of YouTube's API and works reliably in all environments.

## Commands

### Generate Chapter Thumbnails

Creates individual thumbnail images for each chapter:

```bash
python manage.py generate_text_thumbnails [options]
```

**Options:**
- `--file-ids FILM_ID [FILM_ID ...]` - Process specific films only
- `--force` - Regenerate thumbnails even if they already exist

**Examples:**
```bash
# Generate thumbnails for all films
python manage.py generate_text_thumbnails

# Force regenerate all thumbnails
python manage.py generate_text_thumbnails --force

# Generate thumbnails for specific films
python manage.py generate_text_thumbnails --file-ids P-61_FROS 62-SF_FROS
```

### Generate Sprite Sheets

Creates sprite sheet images for animated hover previews:

```bash
python manage.py generate_sprite_thumbnails [options]
```

**Options:**
- `--file-ids FILM_ID [FILM_ID ...]` - Process specific films only
- `--force` - Regenerate sprites even if they already exist
- `--cleanup-old` - Remove old individual chapter thumbnails

**Examples:**
```bash
# Generate sprites for all films
python manage.py generate_sprite_thumbnails

# Force regenerate all sprites
python manage.py generate_sprite_thumbnails --force

# Generate sprites for specific films
python manage.py generate_sprite_thumbnails --file-ids P-61_FROS 62-SF_FROS
```

## Output Locations

### Chapter Thumbnails
- **Directory**: `static/thumbnails/chapters/`
- **Naming**: `{FILM_ID}_{CHAPTER_ID}.jpg`
- **Example**: `static/thumbnails/chapters/P-61_FROS_585.jpg`
- **Size**: 640x360 pixels (16:9 aspect ratio)

### Sprite Sheets
- **Directory**: `static/thumbnails/previews/`
- **Naming**: `{FILM_ID}_sprite.jpg`
- **Example**: `static/thumbnails/previews/P-61_FROS_sprite.jpg`
- **Frame Size**: 160x90 pixels per frame
- **Layout**: Horizontal strip of frames

## How It Works

### Chapter Thumbnails
1. For each film, processes all chapters in order
2. Creates a 640x360 image with:
   - Colored background (rotates through 12-color palette)
   - Chapter timestamp at top
   - Chapter order subtitle
   - Wrapped chapter title text with shadow effects
3. Saves image and updates `Chapter.thumbnail_url` in database

### Sprite Sheets
1. For films with chapters: Uses chapter data to create frames
2. For films without chapters: Creates 4 generic film preview frames
3. Limits to 6-8 frames maximum for performance
4. Creates horizontal sprite sheet with all frames
5. Updates film database fields:
   - `preview_sprite_url`
   - `preview_frame_count`
   - `preview_frame_interval` (800ms)
   - `preview_sprite_width` (160px)
   - `preview_sprite_height` (90px)

## Color Palette

The system uses a 12-color palette for visual variety:
- Soft Red (#FF6B6B)
- Teal (#4ECDC4)
- Sky Blue (#45B7D1)
- Mint Green (#96CEB4)
- Soft Yellow (#F7DC6F)
- Lavender (#BB8FCE)
- Light Blue (#85C1E9)
- Orange (#F8B500)
- Purple (#6C5CE7)
- Pale Green (#A8E6CF)
- Golden Yellow (#FFD93D)
- Coral (#FF8B94)

Colors are assigned consistently based on chapter order.

## Font Handling

The system attempts to use system fonts in this order:
1. DejaVu Sans Bold (Linux)
2. Liberation Sans Bold (Linux)
3. Helvetica (macOS)
4. Arial (Windows)
5. PIL default font (fallback)

## Dependencies

- **PIL/Pillow**: For image generation and manipulation
- **Django**: For database access and management commands
- **textwrap**: For text wrapping functionality

## Troubleshooting

### Common Issues

**"Font not found" warnings:**
- The system will fall back to default fonts automatically
- Install DejaVu fonts for better text rendering: `sudo apt-get install fonts-dejavu`

**Permission errors:**
- Ensure the `static/thumbnails/` directories are writable
- Check file permissions: `chmod -R 755 static/thumbnails/`

**Missing thumbnails:**
- Run with `--force` flag to regenerate
- Check that chapters exist in the database
- Verify `STATIC_ROOT` and `BASE_DIR` settings

### Debugging

Add `-v 2` for verbose output:
```bash
python manage.py generate_text_thumbnails -v 2
```

Check generated files:
```bash
ls -la static/thumbnails/chapters/ | head -10
ls -la static/thumbnails/previews/ | head -10
```

Verify database updates:
```bash
python manage.py shell -c "from main.models import Film; f = Film.objects.first(); print(f.preview_sprite_url)"
```

## Deployment Notes

- Ensure `static/thumbnails/` directories exist and are writable
- Consider running thumbnail generation as part of deployment process
- Generated images are served as static files via Django's static file handling
- In production, thumbnails should be served directly by web server (nginx/Apache) for better performance
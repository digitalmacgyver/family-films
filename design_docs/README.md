# Family Films Website

A Django-based website for browsing and viewing digitized family home movies with YouTube integration.

## Current Features

### Core Functionality
- **Film Catalog**: Browse all digitized family films with thumbnails and metadata
- **YouTube Integration**: All films are hosted on YouTube and embedded in the site
- **Chapter Navigation**: Films are divided into chapters with timestamps for easy navigation
- **Animated Thumbnails**: Films display animated preview thumbnails on hover
- **Real-time Search**: Dynamic search that updates results as you type
- **Clickable Video Tiles**: Click anywhere on a video tile to go to detail page and auto-play

### Metadata Management
- **People Tracking**: Track family members and other people appearing in films
- **Location Tracking**: Record filming locations with geographic information
- **Tag System**: Categorize films with descriptive tags
- **Year Tracking**: Track filming years for both films and individual chapters

### Search Capabilities
- **Overall Search**: Search across films, chapters, people, locations, and tags
- **Faceted Search**: Browse by people, locations, years, or tags
- **Timeline View**: Browse films chronologically by year/decade

### Admin Features
- **Chapter Metadata Editor**: Add/edit people, locations, tags for each chapter
- **Notes System**: Add personal notes to films and chapters
- **User Authentication**: Secure login for family members
- **Admin Interface**: Django admin for managing all content

## Technical Stack

- **Backend**: Django 5.2.4 with PostgreSQL (production) / SQLite (development)
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Video Hosting**: YouTube with iframe API integration
- **Deployment**: Heroku (production) with WhiteNoise for static files
- **Image Processing**: Pillow for thumbnail generation

## Data Model

### Films
- Basic info: title, description, YouTube ID, duration
- Metadata: people, locations, tags, years
- Technical: thumbnail URLs, sprite animation data
- Relationships: chapters, notes

### Chapters
- Timing: start/end times within parent film
- Metadata: title, description, people, locations, tags, years
- Visual: thumbnail image from Excel metadata

### People
- Name: first_name, last_name
- Relationships: films, chapters they appear in
- Special handling for maiden names (e.g., "nee Hayward")

### Locations
- Geographic: name, city, state, country, coordinates
- Relationships: films, chapters filmed there

### Tags
- Categorized: Event, Activity, Holiday, etc.
- Relationships: films, chapters they're associated with

## Recent Updates

### UI Improvements (July 2025)
- Made video tiles clickable for direct playback
- Implemented real-time search with debouncing
- Fixed chapter metadata editor layout (3 columns → 3 rows)
- Added chapter-based animated thumbnails

### Data Cleanup (July 2025)
- Normalized person names (e.g., "John" → "John Hayward Sr.")
- Imported chapter thumbnails from Excel metadata
- Fixed duplicate person entries

## Project Structure

```
family_films/
├── films/          # Main film browsing app
├── people/         # People directory and details
├── locations/      # Location browsing
├── search/         # Search functionality
├── main/           # Core models and utilities
├── static/         # CSS, JS, thumbnails
├── scripts/        # Utility and maintenance scripts
├── design_docs/    # Documentation and requirements
└── chapter_sheets/ # Excel files with chapter metadata
```

## Local Development

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with:
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Deployment

### Heroku
- Automatic deploys from master branch
- Uses PostgreSQL add-on
- Environment variables configured in Heroku dashboard

### Static Files
- Served via WhiteNoise
- Collected with `python manage.py collectstatic`
- Thumbnails stored in `static/thumbnails/`

## Maintenance Scripts

Located in `scripts/` directory:
- `normalize_person_names.py` - Clean up person name variations
- `analyze_thumbnail_issues.py` - Debug thumbnail problems
- `import_chapter_metadata.py` - Import from Excel files
- Various data import/export utilities

## Future Enhancements

- Mobile app version
- Advanced video analytics
- Family tree integration
- Facial recognition for automatic person tagging
- Map view for location-based browsing
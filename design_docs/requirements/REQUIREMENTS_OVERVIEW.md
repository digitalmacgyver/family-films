# Family Films Website Requirements

## Executive Summary

The Family Films Website is a web application designed to index, search, and explore a collection of digitized family home movies hosted on YouTube. The system provides rich metadata capabilities to tag films with information about people, locations, dates, and subjects, making decades of family history easily discoverable and accessible.

## Project Goals

1. **Centralized Access**: Provide a single, searchable interface for all digitized family films hosted on YouTube
2. **Rich Metadata**: Enable detailed tagging of films with people, locations, dates, and subjects
3. **Easy Discovery**: Allow family members to quickly find specific moments, people, or events
4. **Preservation**: Document and preserve family history through structured metadata
5. **Scalability**: Support hundreds of films with thousands of tagged segments

## Key Features

### 1. Film Catalog
- Display all films from the YouTube playlist (PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm)
- Show film thumbnails, titles, durations, and basic metadata
- Support pagination and sorting options

### 2. Advanced Search & Filtering
- **People Search**: Find all films featuring specific family members
- **Location Search**: Find films shot at specific locations
- **Date Range Search**: Find films from specific years or date ranges
- **Tag-based Search**: Find films by subject matter tags
- **Full-text Search**: Search film descriptions and notes

### 3. Film Detail Pages
- Embedded YouTube player
- Chapter navigation with timestamps
- Complete metadata display
- Related films suggestions

### 4. Data Management
- Import existing metadata from CSV and Excel files
- Admin interface for adding/editing film metadata
- Bulk tagging capabilities
- Data validation and consistency checks

### 5. User Features
- Public viewing interface (no authentication required)
- Admin authentication for data management
- Responsive design for mobile and desktop

## Technical Architecture

### Frontend
- Django templates with Bootstrap 5
- JavaScript for interactive features
- YouTube IFrame API for video playback

### Backend
- Django web framework
- PostgreSQL database
- RESTful API endpoints for data access

### Data Sources
- YouTube playlist API
- Existing CSV/Excel metadata files
- Manual data entry through admin interface

## Stakeholders

- **End Users**: Family members seeking to view and discover family films
- **Administrators**: Family archivists managing metadata
- **Content Owners**: Family members who own the original films

## Success Criteria

1. All films from the YouTube playlist are indexed and searchable
2. Users can find specific films in under 30 seconds using search/filters
3. Metadata is accurate and comprehensive for all films
4. System supports at least 500+ films without performance degradation
5. Mobile-responsive design works on all modern devices
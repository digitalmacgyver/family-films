# Functional Requirements

## 1. Film Browsing and Display

### 1.1 Film Catalog Page
**Description**: Main page displaying all films in the collection

**Requirements**:
- Display films in a grid layout with thumbnails
- **Animated Thumbnails**:
  - Static thumbnail displayed by default
  - On mouse hover, display animated preview cycling through evenly spaced frames
  - Preload preview frames for smooth animation
  - Fallback to static image on mobile/touch devices
  - Generate preview sprites during import process
- Show key metadata for each film:
  - Title
  - Year(s)
  - Primary people
  - Primary location
  - Duration
  - View count (if available from YouTube)
- Support multiple view modes:
  - Grid view (default)
  - List view with more details
  - Timeline view (chronological)
- Implement pagination (12-24 films per page)
- Sort options:
  - Chronological (oldest first/newest first)
  - Alphabetical by title
  - Most recently added
  - Duration

### 1.2 Film Detail Page
**Description**: Individual film page with full metadata and playback

**Requirements**:
- Embedded YouTube player using iframe API
- Chapter navigation:
  - Clickable chapter list with timestamps
  - Jump to specific timestamp on click
  - Highlight current chapter during playback
  - Visual timeline with chapter markers
- **Chapter/Segment Metadata Editor**:
  - Interface for marking people in specific chapters
  - Add/remove locations for each segment
  - Set date ranges for segments
  - Tag segments with custom tags
  - Bulk edit capabilities for multiple segments
  - Visual indicators showing which segments have metadata
  - Save draft changes before committing
  - Permission-based editing (admin only)
- Full metadata display:
  - Complete description
  - All people with links to their pages
  - All locations with links
  - All tags
  - Technical notes
  - File ID
- Related films sidebar:
  - Films with same people
  - Films from same year
  - Films at same location
- Social sharing buttons
- Download metadata as JSON/CSV option

## 2. Search and Filtering

### 2.1 Advanced Search Interface
**Description**: Comprehensive search functionality

**Requirements**:
- **Overall Search Function**:
  - Full-text search across all content:
    - Film titles and descriptions
    - Chapter/segment descriptions
    - People names
    - Location names
    - Tag names
    - Technical notes
  - Weighted search results (title matches rank higher)
  - Search highlighting in results
  - "Did you mean?" suggestions for typos
- Search fields:
  - Full-text search (title, description, notes)
  - People (multi-select dropdown)
  - Locations (multi-select dropdown)
  - Date range (from year - to year)
  - Tags (multi-select)
  - Film format (16mm, 8mm, etc.)
  - Has sound (yes/no/any)
- Search logic:
  - AND logic within field types
  - OR logic across field types
  - Exclude option for each criterion
- Save search functionality
- Search history for logged-in users
- Export search results

### 2.2 Quick Search
**Description**: Simple search box in navigation

**Requirements**:
- Autocomplete suggestions as user types
- Search across titles, people, locations
- Instant results dropdown
- "See all results" link to advanced search

### 2.3 Filter Sidebar
**Description**: Faceted filtering on catalog page

**Requirements**:
- Dynamic filters based on current results:
  - Years (with count)
  - People (top 20 with count)
  - Locations (top 20 with count)
  - Tags (all with count)
- Multiple selection within categories
- Clear all filters button
- Filter count indicators

## 3. People Management

### 3.1 People Directory
**Description**: Browse all people in the database

**Requirements**:
- Alphabetical listing by last name
- Family tree visualization option
- Statistics per person:
  - Number of films appeared in
  - Total screen time (if available)
  - Date range of appearances
- Link to person detail page

### 3.2 Person Detail Page
**Description**: Individual person page

### 3.3 Top-Level People Search Page
**Description**: Dedicated search page for finding films by people

**Requirements**:
- **URL**: `/search/people/`
- Large, prominent person selector
- Auto-complete person names
- Show person photo/thumbnail if available
- Quick stats for each person (film count, year range)
- Results display:
  - Grid of films featuring selected person(s)
  - Timeline view option
  - Filter by additional criteria (year, location)
  - Export results as playlist

**Requirements**:
- Personal information display
- Family relationships visualization
- Filmography:
  - List all films they appear in
  - Chronological timeline
  - Film thumbnails and links
- Photo gallery (extracted from films)
- Edit capabilities for admins

## 4. Location Management

### 4.1 Locations Map
**Description**: Interactive map of filming locations

**Requirements**:
- Map integration (Google Maps or OpenStreetMap)
- Markers for each location with geocoordinates
- Cluster markers for zoom levels
- Click marker to see location details
- List view alternative to map

### 4.2 Location Detail Page
**Description**: Individual location page

**Requirements**:
- Location information and description
- Map showing specific location
- All films shot at this location
- Photo gallery from films
- Historical notes about the location

### 4.3 Top-Level Location Search Page
**Description**: Dedicated search page for finding films by location

**Requirements**:
- **URL**: `/search/locations/`
- Interactive map for selecting locations
- Search by location name or address
- Radius search (films within X miles)
- Location categories (National Parks, Cities, etc.)
- Results display:
  - Films grouped by location
  - Map view with film counts
  - Timeline of visits to location
  - Export location-based playlists

## 5. Additional Search Pages

### 5.1 Top-Level Year Search Page
**Description**: Search films by year or date range

**Requirements**:
- **URL**: `/search/years/`
- Visual timeline interface
- Decade groupings with film counts
- Date range selector
- Calendar heat map showing filming frequency
- Results display:
  - Chronological film listing
  - Group by year with collapsible sections
  - Historical context for each year
  - Export year-based playlists

### 5.2 Top-Level Tag Search Page
**Description**: Browse films by tags/themes

**Requirements**:
- **URL**: `/search/tags/`
- Tag cloud visualization (size by frequency)
- Tag categories (Holidays, Events, Activities, etc.)
- Multi-select tag combinations
- Suggested tag combinations
- Results display:
  - Films matching selected tags
  - Related tags suggestion
  - Tag co-occurrence visualization
  - Export tag-based playlists

## 6. Data Management (Admin)

### 6.1 Film Data Import
**Description**: Import film metadata from various sources

**Requirements**:
- CSV import for family_reunion_movies.csv
- Excel import for individual film metadata
- YouTube playlist sync:
  - Fetch new videos from playlist
  - Update metadata from YouTube
  - Match with existing records by File ID
- **Thumbnail Generation**:
  - Extract static thumbnails from YouTube
  - Generate preview frame sequences for animated thumbnails
  - Create sprite sheets for hover animations
  - Store multiple resolutions for performance
- Validation and error reporting
- Preview changes before import
- Rollback capability

### 6.2 Metadata Editor
**Description**: Web interface for editing film metadata

**Requirements**:
- Edit all film fields
- Batch editing capabilities:
  - Add tags to multiple films
  - Add people to multiple films
- Chapter editor with timestamp validation
- Rich text editor for descriptions
- Image upload for custom thumbnails
- Change history tracking

### 6.3 People and Location Management
**Description**: Admin tools for managing people and locations

**Requirements**:
- Add/edit/merge people records
- Family relationship editor
- Add/edit locations with map picker
- Bulk geocoding for locations
- Import people from Haywards Present bitfield

## 7. YouTube Integration

### 7.1 Playlist Synchronization
**Description**: Keep local data in sync with YouTube playlist

**Requirements**:
- Scheduled sync (daily)
- Manual sync trigger
- Detect:
  - New videos added
  - Videos removed
  - Metadata changes
  - View count updates
- Sync status dashboard
- Error notifications

### 6.2 Video Playback
**Description**: Embedded YouTube player with enhanced features

**Requirements**:
- YouTube IFrame API integration
- Custom controls:
  - Chapter navigation
  - Playback speed control
  - Timestamp sharing
- Track viewing analytics
- Resume playback feature
- Playlist queue functionality

## 7. User Interface

### 7.1 Responsive Design
**Description**: Mobile-friendly interface

**Requirements**:
- Bootstrap 5 responsive grid
- Touch-friendly controls
- Mobile-optimized video player
- Simplified navigation on mobile
- Progressive web app capabilities

### 7.2 Accessibility
**Description**: WCAG 2.1 AA compliance

**Requirements**:
- Keyboard navigation
- Screen reader support
- High contrast mode
- Closed captions for films with sound
- Alt text for all images

## 8. Performance Requirements

### 8.1 Page Load Times
- Catalog page: < 2 seconds
- Film detail page: < 1.5 seconds
- Search results: < 1 second

### 8.2 Scalability
- Support 500+ films
- Support 1000+ people records
- Support 500+ locations
- Handle 100 concurrent users

## 9. Security Requirements

### 9.1 Authentication
- Django admin authentication
- Optional social login for users
- Role-based permissions:
  - Admin: Full access
  - Editor: Edit metadata
  - Viewer: Read-only access

### 9.2 Data Protection
- HTTPS everywhere
- CSRF protection
- SQL injection prevention
- XSS protection
- Rate limiting on API endpoints
# Technical Requirements

## 1. Technology Stack

### 1.1 Backend
- **Framework**: Django 5.2+
- **Language**: Python 3.10+
- **Database**: PostgreSQL 14+
- **Cache**: Redis (optional, for performance)
- **Task Queue**: Celery (for async tasks like YouTube sync)
- **Web Server**: Gunicorn + Nginx

### 1.2 Frontend
- **CSS Framework**: Bootstrap 5.3
- **JavaScript**: Vanilla JS with modern ES6+
- **Video Player**: YouTube IFrame API
- **Maps**: Leaflet.js with OpenStreetMap
- **Icons**: Bootstrap Icons
- **Charts**: Chart.js (for statistics)

### 1.3 Third-Party Services
- **YouTube Data API v3**: For playlist and video metadata
- **Geocoding API**: For location coordinates
- **AWS S3**: For static file storage (optional)
- **Sentry**: For error monitoring (optional)

## 2. Application Architecture

### 2.1 Django Apps Structure
```
family_films/
├── films/              # Core film models and views
├── people/             # Person management
├── locations/          # Location management
├── search/             # Search and filtering
├── youtube_sync/       # YouTube integration
├── data_import/        # CSV/Excel import tools
└── api/               # REST API endpoints
```

### 2.2 Models Architecture
- Use Django ORM with PostgreSQL-specific features
- Implement model managers for complex queries
- Use select_related() and prefetch_related() for performance
- Database indexes on all foreign keys and search fields

### 2.3 URL Structure
```
/                           # Home page with featured films
/films/                     # Film catalog
/films/<file_id>/          # Film detail page
/people/                    # People directory
/people/<id>/              # Person detail page
/locations/                 # Locations list/map
/locations/<id>/           # Location detail
/search/                    # Advanced search
/search/people/            # Top-level people search
/search/locations/         # Top-level location search
/search/years/             # Top-level year/timeline search
/search/tags/              # Top-level tag/theme search
/api/v1/                   # REST API
/admin/                    # Django admin
```

## 3. Database Design

### 3.1 PostgreSQL Features
- Full-text search with pg_trgm
- JSON fields for flexible metadata
- Array fields for tags
- Geographic data types for coordinates

### 3.2 Migrations Strategy
- Keep migrations small and focused
- Always provide reverse migrations
- Test migrations on copy of production data
- Use data migrations for complex changes

### 3.3 Backup Strategy
- Daily automated backups
- Point-in-time recovery capability
- Test restore procedures monthly
- Backup YouTube metadata separately

## 4. API Design

### 4.1 REST API Endpoints
```
GET /api/v1/films/                 # List films with filters
GET /api/v1/films/<file_id>/      # Film details
GET /api/v1/films/<file_id>/chapters/  # Film chapters with metadata
POST /api/v1/films/<file_id>/chapters/<id>/people/  # Add people to chapter
GET /api/v1/people/                # List people
GET /api/v1/people/<id>/           # Person details
GET /api/v1/locations/             # List locations
GET /api/v1/search/                # Overall search endpoint
GET /api/v1/search/people/         # People-specific search
GET /api/v1/search/locations/      # Location-specific search
GET /api/v1/search/years/          # Year/timeline search
GET /api/v1/search/tags/           # Tag-based search
GET /api/v1/thumbnails/<file_id>/preview/  # Animated thumbnail data
```

### 4.2 API Features
- JSON responses
- Pagination with limit/offset
- Filtering via query parameters
- Sorting options
- Field selection
- CORS headers for frontend apps

### 4.3 Authentication
- Token-based auth for write operations
- Public read access
- Rate limiting by IP
- API documentation with Swagger/OpenAPI

## 5. YouTube Integration

### 5.1 YouTube Data API
- API key management
- Quota monitoring (10,000 units/day)
- Efficient batch requests
- Error handling and retries
- Caching API responses

### 5.2 Video Embedding
- Responsive iframe embedding
- Player API for custom controls
- Privacy-enhanced mode
- Lazy loading for performance

### 5.3 Synchronization
- Celery task for playlist sync
- Incremental updates only
- Detect deleted videos
- Update view counts periodically
- Log all sync activities

### 5.4 Thumbnail Generation
- Extract frames from YouTube videos using youtube-dl/yt-dlp
- Generate static thumbnails at multiple resolutions
- Create animated preview sequences:
  - Extract 8-12 evenly spaced frames
  - Create CSS sprite sheets
  - Optimize for web delivery
- Store in cloud storage (S3) for CDN delivery
- Fallback to YouTube thumbnails if generation fails

## 6. Data Import System

### 6.1 CSV Import
- Parse family_reunion_movies.csv format
- Handle multi-line cells
- Validate data types
- Map to Django models
- Progress reporting

### 6.2 Excel Import
- Read .xls format files
- Parse front matter rows
- Extract timestamps with images
- Parse Haywards Present bitfield
- Handle multiple sheet formats

### 6.3 Import Pipeline
```python
1. Upload file
2. Validate format
3. Parse and preview
4. Map fields to models
5. Validate data
6. Import with transaction
7. Generate report
```

## 7. Search Implementation

### 7.1 Full-Text Search
- PostgreSQL full-text search with pg_trgm extension
- Search vector fields across:
  - Film titles and descriptions
  - Chapter descriptions
  - People names
  - Location names
  - Tag names
- Weighted search (title matches rank higher than descriptions)
- Stemming and synonyms
- Search suggestions and "did you mean?" features
- Highlight matching terms in results

### 7.2 Faceted Search
- Efficient count queries for dynamic filters
- Dynamic facet generation based on search results
- Cache facet counts for performance
- URL-based state management for bookmarkable searches
- Real-time filter updates

### 7.3 Specialized Search Pages
- **People Search**: Autocomplete, family tree integration
- **Location Search**: Map-based interface, radius search
- **Year Search**: Timeline visualization, decade groupings
- **Tag Search**: Tag cloud, category groupings
- Export search results as playlists/collections

### 7.4 Search Performance
- Denormalized search table for complex queries
- Elasticsearch integration (future enhancement)
- Query result caching with Redis
- Async search for large datasets
- Search analytics and optimization

## 8. Frontend Architecture

### 8.1 JavaScript Organization
```
static/js/
├── components/
│   ├── video-player.js
│   ├── search-filters.js
│   ├── chapter-nav.js
│   ├── animated-thumbnail.js
│   ├── chapter-metadata-editor.js
│   └── tag-cloud.js
├── utils/
│   ├── api-client.js
│   ├── formatters.js
│   └── sprite-animator.js
└── pages/
    ├── film-detail.js
    ├── search.js
    ├── people-search.js
    ├── location-search.js
    └── timeline-search.js
```

### 8.2 Progressive Enhancement
- Server-side rendering first
- JavaScript enhancements for interactive features
- Graceful degradation (works without JavaScript)
- Lazy load heavy components
- Animated thumbnails fallback to static on mobile

### 8.3 Animated Thumbnail Implementation
- CSS sprite-based animation using JavaScript
- Preload sprite sheets on page load
- Mouseover/mouseout event handlers
- Mobile detection for fallback behavior
- Performance optimization with requestAnimationFrame

### 8.4 Performance Optimization
- Minified CSS/JS in production
- Image lazy loading with intersection observer
- CDN for static assets and thumbnails
- HTTP/2 push for critical resources
- Service worker for offline access
- Sprite sheet compression and optimization

## 9. Development Workflow

### 9.1 Environment Setup
```bash
# Development
DEBUG=True
DATABASE_URL=postgres://localhost/family_films_dev

# Staging
DEBUG=False
DATABASE_URL=postgres://staging-server/family_films

# Production
DEBUG=False
DATABASE_URL=postgres://prod-server/family_films
```

### 9.2 Testing Strategy
- Unit tests for models and utilities
- Integration tests for views
- API endpoint tests
- Selenium tests for critical paths
- 80% code coverage target

### 9.3 CI/CD Pipeline
1. GitHub Actions on push
2. Run tests and linting
3. Build Docker image
4. Deploy to staging
5. Run smoke tests
6. Manual approval for production
7. Deploy to production
8. Run health checks

## 10. Monitoring and Logging

### 10.1 Application Monitoring
- Django logging to files
- Sentry for error tracking
- Performance monitoring
- Uptime monitoring
- YouTube API quota alerts

### 10.2 Metrics to Track
- Page load times
- Search query performance
- YouTube sync success rate
- User engagement metrics
- Error rates by page

### 10.3 Logging Strategy
- Structured JSON logs
- Log rotation
- Centralized log aggregation
- Security event logging
- GDPR-compliant retention

## 11. Security Measures

### 11.1 Application Security
- Django security middleware
- Content Security Policy
- HTTPS only with HSTS
- Secure session cookies
- SQL injection prevention

### 11.2 Data Security
- Encrypted database connections
- Backup encryption
- API rate limiting
- Input validation
- XSS prevention

### 11.3 Access Control
- Role-based permissions
- Audit logging
- Session management
- Password policies
- Two-factor auth (optional)

## 12. Deployment Requirements

### 12.1 Infrastructure
- EC2 instance (t3.medium minimum)
- RDS PostgreSQL instance
- S3 bucket for media
- CloudFront CDN
- Route 53 for DNS

### 12.2 Scaling Strategy
- Horizontal scaling ready
- Database read replicas
- Redis cache layer
- CDN for static assets
- Load balancer ready

### 12.3 Backup and Recovery
- Automated daily backups
- 30-day retention
- Cross-region backup copies
- Disaster recovery plan
- Regular restore tests
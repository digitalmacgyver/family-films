# Data Model Requirements

## Overview

The data model must support comprehensive metadata for digitized family films, including information about the physical reels, film segments, people appearing in films, locations, and tags. The model is based on the draft schema but adapted for Django ORM.

## Core Entities

### 1. Films (YouTube Videos)
**Purpose**: Represents individual videos uploaded to YouTube

**Fields**:
- `file_id` (CharField, unique): Unique identifier matching CSV file ID (e.g., "57-PT_FROS")
- `youtube_url` (URLField): Full YouTube video URL
- `youtube_id` (CharField): YouTube video ID for embedding
- `title` (CharField): Film title
- `description` (TextField): Full description from YouTube
- `summary` (TextField): Brief summary of film contents
- `duration` (DurationField): Total video duration
- `upload_date` (DateField): Date uploaded to YouTube
- `thumbnail_url` (URLField): YouTube thumbnail URL
- **Animated Thumbnail Support**:
  - `preview_sprite_url` (URLField, optional): Path to sprite sheet for hover animation
  - `preview_frame_count` (IntegerField, default=0): Number of frames in preview
  - `preview_frame_interval` (FloatField): Seconds between preview frames
  - `preview_sprite_width` (IntegerField): Width of individual sprite frames
  - `preview_sprite_height` (IntegerField): Height of individual sprite frames

**Relationships**:
- Has many Chapters
- Has many FilmPeople (through table)
- Has many FilmLocations (through table)
- Has many FilmTags (through table)

### 2. Digital Reels
**Purpose**: Represents the original physical film reels that were digitized

**Fields**:
- `reel_id` (CharField, primary key): Label from physical canister
- `filename` (CharField): Digital file name
- `format` (CharField, choices): 16mm, 8mm, Super-8, etc.
- `fps` (IntegerField): Original frames per second
- `frame_count` (IntegerField): Total number of frames
- `has_sound` (BooleanField): Audio track present
- `scan_batch` (CharField): A, B, or C
- `scan_resolution` (CharField): e.g., "4976x3472"

**Relationships**:
- Has many Sequences

### 3. Sequences
**Purpose**: Logical segments within a reel representing distinct scenes

**Fields**:
- `reel` (ForeignKey to DigitalReel)
- `sequence_num` (IntegerField): Order within reel
- `title` (CharField): Short title for segment
- `description` (TextField): Detailed description
- `start_frame` (IntegerField): First frame number
- `duration_frames` (IntegerField): Number of frames
- `start_time_16fps` (FloatField): Start time in seconds at 16fps
- `intro_text` (TextField, optional): Text for title cards

**Relationships**:
- Belongs to one DigitalReel
- Has many SequencePeople (through table)
- Has many SequenceLocations (through table)
- Has many SequenceTags (through table)

### 4. Chapters
**Purpose**: Timestamp-based segments within YouTube videos

**Fields**:
- `film` (ForeignKey to Film)
- `start_time` (CharField): "MM:SS" or "HH:MM:SS" format
- `start_time_seconds` (IntegerField): Start time converted to seconds for sorting/calculations
- `title` (CharField): Chapter description
- `description` (TextField, optional): Detailed chapter description
- `order` (IntegerField): Display order
- **Metadata Support**:
  - `has_people_metadata` (BooleanField, default=False): Quick check for UI indicators
  - `has_location_metadata` (BooleanField, default=False): Quick check for UI indicators
  - `has_tags_metadata` (BooleanField, default=False): Quick check for UI indicators

**Relationships**:
- Belongs to one Film
- Has many ChapterPeople (through table)
- Has many ChapterLocations (through table)
- Has many ChapterTags (through table)

### 5. People
**Purpose**: Family members and other individuals in films

**Fields**:
- `id` (AutoField)
- `first_name` (CharField)
- `last_name` (CharField)
- `birth_date` (DateField, optional)
- `death_date` (DateField, optional)
- `father` (ForeignKey to self, optional)
- `mother` (ForeignKey to self, optional)
- `spouse` (ForeignKey to self, optional)
- `notes` (TextField)
- `hayward_index` (IntegerField, optional): Position in Haywards Present bitfield

**Methods**:
- `full_name()`: Returns formatted full name
- `is_hayward_family()`: Returns True if hayward_index is set

### 6. Locations
**Purpose**: Places where films were shot

**Fields**:
- `id` (AutoField)
- `name` (CharField): Location name
- `description` (TextField)
- `city` (CharField, optional)
- `state` (CharField, optional)
- `country` (CharField, default="USA")
- `latitude` (DecimalField, optional)
- `longitude` (DecimalField, optional)

### 7. Tags
**Purpose**: Subject matter categories

**Fields**:
- `tag` (CharField, primary key): Tag name
- `category` (CharField, choices): holidays, events, activities, etc.
- `description` (TextField)

## Association Tables

### FilmPeople
- `film` (ForeignKey)
- `person` (ForeignKey)
- `is_primary` (BooleanField): Main subject of film

### FilmLocations
- `film` (ForeignKey)
- `location` (ForeignKey)
- `is_primary` (BooleanField): Main location

### FilmTags
- `film` (ForeignKey)
- `tag` (ForeignKey)
- `is_auto` (BooleanField): Applied by automation

### ChapterPeople
**Purpose**: Track people appearing in specific chapters/segments
- `chapter` (ForeignKey to Chapter)
- `person` (ForeignKey to Person)
- `is_primary` (BooleanField): Main person in this chapter
- `confidence` (FloatField, optional): AI confidence score for auto-tagging

### ChapterLocations
**Purpose**: Track locations for specific chapters/segments
- `chapter` (ForeignKey to Chapter)
- `location` (ForeignKey to Location)
- `is_primary` (BooleanField): Main location for this chapter

### ChapterTags
**Purpose**: Tag specific chapters/segments with themes
- `chapter` (ForeignKey to Chapter)
- `tag` (ForeignKey to Tag)
- `is_auto` (BooleanField): Applied by automation
- `confidence` (FloatField, optional): AI confidence score

### SequencePeople
- `sequence` (ForeignKey)
- `person` (ForeignKey)

### SequenceLocations
- `sequence` (ForeignKey)
- `location` (ForeignKey)
- `is_primary` (BooleanField)

### SequenceTags
- `sequence` (ForeignKey)
- `tag` (ForeignKey)
- `is_auto` (BooleanField)

## Data Import Considerations

### From CSV File
- Film-level metadata (title, description, years, people, locations)
- Technical notes and workflow state
- Tag assignments

### From Excel Files
- Sequence-level metadata with timestamps
- Haywards Present bitfield parsing
- Chapter information

## Indexes and Performance

Required indexes:
- Film.file_id (unique)
- Film.youtube_id (unique)
- Person.last_name
- Location.name
- All foreign keys
- Composite indexes on association tables
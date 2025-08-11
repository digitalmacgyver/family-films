# Project Purpose
A front end UI to browse family films served from YouTube, with features to set metadata on films and subsequences of films called chapters such as: years, people, locations, and tags.

# Technologies
- Python
- Django
- JavaScript

# Production Deployment
- Deployed in Heroku using Heroku commandline tools
- Production database is Postgresql hosted on Heroku

# Directory Structure
- backups : Local development and production database backups
- design_docs : Requirements documentation and implementation notes - review these at the start of each conversation and session
- scripts : Ad-hoc scripting and debugging tools created to extract film metadata, set or repair film metadata, copy data between development and production, debug issues, etc. - code that is required to operate the family films application in production must never be placed in this directory
- venv : Our Python virtual environment. At the start of each conversation source the file in venv/bin/activate to ensure correct Python binaries and modules are in use

# Script Operations
- When asked to do some task, such as generating thumbnail images or copying data from local development databases to production, first search to see if there is an existing utility script designed for this purpose. If there is, refine that script with any changes due to recent code updates and use that script rather than starting from scratch.
- **All new ad-hoc scripts and debugging tools must be created in the scripts/ directory.** This includes one-time data fixes, experimental analysis tools, migration scripts, and debugging utilities that are not part of the core web application functionality.

# Consolidated Management Scripts

The scripts directory has been cleaned up and consolidated into 7 comprehensive management tools. **ALWAYS use these existing scripts rather than creating new ones** for the following tasks:

## Available Management Scripts

### 1. `youtube_manager.py` - YouTube Mapping Management
**Use for:** YouTube video mapping, verification, playlist management
```bash
python scripts/youtube_manager.py verify-all
python scripts/youtube_manager.py update --dry-run
python scripts/youtube_manager.py check-id --youtube-id VIDEO_ID
python scripts/youtube_manager.py playlist --playlist-url URL
python scripts/youtube_manager.py quick-verify --file-ids P-04 P-23
```

### 2. `person_manager.py` - Person Data Management  
**Use for:** Merging duplicates, normalizing names, person cleanup
```bash
python scripts/person_manager.py merge-duplicates --dry-run
python scripts/person_manager.py normalize
python scripts/person_manager.py remove-orphans
python scripts/person_manager.py update-csv --csv-file name_cleanup.csv
python scripts/person_manager.py analyze  # Directory analysis & missing people detection
python scripts/person_manager.py all --dry-run
```

### 3. `location_manager.py` - Location Data Management
**Use for:** Location updates, cleanup, orphan removal
```bash
python scripts/location_manager.py update-csv --csv-file location_cleanup.csv
python scripts/location_manager.py remove-orphans --dry-run
python scripts/location_manager.py fix-specific
python scripts/location_manager.py statistics
python scripts/location_manager.py analyze  # Directory analysis & missing locations detection
python scripts/location_manager.py all --dry-run
```

### 4. `thumbnail_manager.py` - Thumbnail & Sprite Management
**Use for:** Creating sprites, chapter thumbnails, verification
```bash
python scripts/thumbnail_manager.py create-sprites --use-youtube
python scripts/thumbnail_manager.py create-chapters --film-ids P-04 P-23
python scripts/thumbnail_manager.py verify
python scripts/thumbnail_manager.py analyze
python scripts/thumbnail_manager.py storyboard --film-ids P-04  # Extract YouTube storyboard data
python scripts/thumbnail_manager.py all --placeholder-only
```

### 5. `data_manager.py` - Data Import & Auditing
**Use for:** CSV imports, data validation, reporting
```bash
python scripts/data_manager.py import-csv --csv-file films.csv --dry-run
python scripts/data_manager.py audit
python scripts/data_manager.py extract --film-id P-04
python scripts/data_manager.py report --output-file report.json
python scripts/data_manager.py all --dry-run
```

### 6. `excel_manager.py` - Excel/XLS File Management
**Use for:** Image extraction from XLS files, batch processing, validation
```bash
python scripts/excel_manager.py input.xls -o output_dir/
python scripts/excel_manager.py chapter_sheets/ --batch -o thumbnails/
python scripts/excel_manager.py chapter.xls  # Extract to same directory
```

### 7. `genealogy_manager.py` - Genealogy Data Management
**Use for:** Family tree relationships, genealogy sync, data validation
```bash
python scripts/genealogy_manager.py export --output-file backups/genealogy.json
python scripts/genealogy_manager.py sync --data-file genealogy.json --dry-run
python scripts/genealogy_manager.py validate  # Check relationship integrity
python scripts/genealogy_manager.py report --output-file genealogy_report.json
python scripts/genealogy_manager.py all  # Export, validate, and report
```

## Script Usage Guidelines

1. **ALWAYS check if an existing consolidated script can handle the task** before writing new code
2. **Use dry-run options** (`--dry-run`) when testing operations
3. **These scripts support multiple modes** - check their help with `-h` or `--help`
4. **All scripts have comprehensive error handling** and validation
5. **Each script can process single items or bulk operations**

## When NOT to Use These Scripts

- When the task requires functionality genuinely not covered by these tools
- When working with non-standard data formats not supported
- When debugging very specific edge cases requiring custom analysis

**Remember: These consolidated scripts represent 43+ individual scripts that were merged. They contain extensive functionality that covers nearly all routine data management tasks, including genealogy family tree management.**

## Additional Specialized Tools

### Core XLS Image Extractor
- **`xls_image_extractor.py`** (root directory) - Core binary XLS image extraction used by Django import_chapter_metadata command
- This is the production tool used for extracting chapter thumbnails from Excel files in chapter_sheets/ directory

# MANDATORY Production Sync Procedure

## CRITICAL: Database Sync Requirements

**When syncing development database to production, you MUST follow this exact procedure:**

### Required Script and Command
**ALWAYS use:** `scripts/sync_to_production.py`
**ALWAYS run:** `echo "YES" | python scripts/sync_to_production.py`

### Why This Exact Command is Required
1. **Essential-0 Dyno Compatibility**: Production uses essential-0 dynos which cannot use standard-2x dynos
2. **Stdin Data Loading**: Script uses `cat database_export.json | heroku run --no-tty -- python manage.py loaddata --format=json -` method
3. **Automatic Confirmation**: The `echo "YES"` automatically confirms the destructive database reset
4. **Proper Verification**: Script includes essential-0 compatible verification commands

### What You MUST NOT Do
- ❌ Never run `heroku run --size=standard-2x` (not available on essential-0 plan)
- ❌ Never try to upload files to Heroku filesystem (ephemeral, won't work)
- ❌ Never manually run `heroku pg:reset` without the sync script
- ❌ Never skip the verification step

### Documentation Reference
Complete procedure documented in: `design_docs/PRODUCTION_SYNC_PROCEDURE.md`

**This procedure is MANDATORY. Deviation will cause sync failures.**


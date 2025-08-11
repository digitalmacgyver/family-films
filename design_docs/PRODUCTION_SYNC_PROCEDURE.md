# Production Sync Procedure

## Overview
This document describes the correct procedure for syncing development database data to production on Heroku. The production environment uses essential-0 dynos which have specific limitations that must be accommodated.

## Prerequisites
- Heroku CLI installed and authenticated
- Access to family-films Heroku app
- Local development database with up-to-date data

## Sync Script Location
The main sync script is located at: `scripts/sync_to_production.py`

## Correct Sync Command
```bash
echo "YES" | python scripts/sync_to_production.py
```

**Important:** The `echo "YES"` is required to automatically confirm the destructive database reset operation.

## What the Script Does
1. **Export Local Database**: Creates `database_export.json` with all data except contenttypes and auth.Permission
2. **Backup Production**: Creates Heroku database backup automatically 
3. **Reset Production Database**: Completely destroys and recreates the production database
4. **Run Migrations**: Ensures database schema is up-to-date
5. **Load Data via Stdin**: Uses pipe method compatible with essential-0 dynos
6. **Verify Data**: Confirms all objects were loaded correctly

## Key Technical Details

### Essential-0 Dyno Limitations
- Cannot use `--size=standard-2x` flag
- Must use basic `heroku run` without size specifications
- File system is ephemeral - cannot rely on uploaded files

### Correct Data Loading Method
```bash
cat database_export.json | heroku run --no-tty -- python manage.py loaddata --format=json -
```

**Why this works:**
- Uses stdin pipe to send data directly to the Django management command
- `--no-tty` prevents terminal interaction issues
- `--format=json -` tells Django to read JSON from stdin

### Verification Command
```bash
heroku run -- python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings'); django.setup(); from main.models import Person, Location, Film; print(f'People: {Person.objects.count()}, Locations: {Location.objects.count()}, Films: {Film.objects.count()}')"
```

## Expected Results
After successful sync, production should contain:
- ~62 People (after duplicate cleanup)
- ~116 Locations (after duplicate cleanup and orphan removal)
- ~82 Films
- ~488 Chapters
- Total: ~2,673+ database objects

## Common Issues and Solutions

### Issue: "Standard-2X dynos not available"
**Solution:** Script has been fixed to remove `--size=standard-2x` flags

### Issue: "No fixture named 'database_export' found"
**Solution:** Script now uses stdin pipe method instead of trying to access local files on Heroku

### Issue: EOFError during cleanup prompt
**Solution:** Script handles non-interactive mode gracefully

## Safety Features
- Automatic Heroku database backup before reset
- Confirmation prompt for destructive operations
- Verification step to ensure data loaded correctly
- Transaction handling for data integrity

## Post-Sync Verification
1. Check object counts match expectations
2. Verify key data like films, people, and locations are present
3. Test site functionality at https://family-films-5e88b75c353b.herokuapp.com/

## Troubleshooting
If sync fails:
1. Check Heroku app status: `heroku status`
2. Verify database connectivity: `heroku pg:info`
3. Check recent backups: `heroku pg:backups`
4. Review error logs: `heroku logs --tail`

## NEVER DO
- Never run manual SQL commands on production database
- Never use `heroku pg:reset` without the sync script
- Never assume file uploads work on Heroku ephemeral filesystem
- Never skip the verification step
#!/usr/bin/env python
"""
Script to sync local development database to Heroku production.
This script handles the complete data transfer process.
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    print(f"Running: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: {description} failed!")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    else:
        print(f"SUCCESS: {description} completed")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True

def main():
    print("=== Syncing Local Database to Heroku Production ===\n")
    
    # Step 1: Export local database
    if not run_command(
        "python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > database_export.json",
        "Exporting local database"
    ):
        return False
    
    # Step 2: Check export file size
    if not run_command(
        "ls -la database_export.json",
        "Checking export file"
    ):
        return False
    
    # Step 3: Reset Heroku database (this will destroy all data!)
    print("\n" + "="*60)
    print("WARNING: This will DESTROY all data in the production database!")
    print("="*60)
    
    confirmation = input("Type 'YES' to continue with production database reset: ")
    if confirmation != "YES":
        print("Operation cancelled.")
        return False
    
    if not run_command(
        "heroku pg:reset DATABASE_URL --confirm family-films",
        "Resetting Heroku database"
    ):
        return False
    
    # Step 4: Run migrations on Heroku
    if not run_command(
        "heroku run python manage.py migrate",
        "Running migrations on Heroku"
    ):
        return False
    
    # Step 5: Load data to Heroku
    if not run_command(
        "heroku run --size=standard-2x python manage.py loaddata database_export.json",
        "Loading data to Heroku (this may take several minutes)"
    ):
        return False
    
    # Step 6: Verify data was loaded
    if not run_command(
        "heroku run python manage.py shell -c \"from main.models import Person, Location, Film; print(f'People: {Person.objects.count()}, Locations: {Location.objects.count()}, Films: {Film.objects.count()}')\"",
        "Verifying data was loaded"
    ):
        return False
    
    print("\n" + "="*60)
    print("SUCCESS: Database sync completed!")
    print("="*60)
    
    # Cleanup
    if input("Remove local export file? (y/n): ").lower() == 'y':
        os.remove("database_export.json")
        print("Export file removed.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
# Genealogy Management System

## Overview

The family films application includes comprehensive genealogy management functionality to track family tree relationships alongside film metadata. This system handles parent-child relationships, spouse relationships, and biographical data for all people in the database.

## Architecture

### Core Models
The genealogy system extends the existing `Person` model with family relationship fields:

- `father` - ForeignKey to another Person
- `mother` - ForeignKey to another Person  
- `spouse` - ForeignKey to another Person
- `notes` - TextField for biographical information
- `birth_date` - DateField
- `death_date` - DateField
- `hayward_index` - IntegerField for family indexing

### Relationship Types
1. **Parent-Child**: `father` and `mother` fields create generational links
2. **Spouse**: Mutual relationship between married individuals
3. **Sibling**: Derived from shared parent relationships
4. **Children**: Reverse lookup from parent relationships

## Management Operations

### 1. Data Export (`genealogy_manager.py export`)
Exports complete genealogy dataset from local development database:

```bash
python scripts/genealogy_manager.py export --output-file backups/genealogy_data.json
```

**Output Format:**
```json
[
  {
    "pk": 123,
    "first_name": "John",
    "last_name": "Doe",
    "father_pk": 45,
    "mother_pk": 67,
    "spouse_pk": 89,
    "notes": "Biography text...",
    "birth_date": "1950-01-15",
    "death_date": null,
    "hayward_index": 42
  }
]
```

### 2. Production Sync (`genealogy_manager.py sync`)
Syncs genealogy data from development to production environment:

```bash
python scripts/genealogy_manager.py sync --data-file genealogy_data.json --dry-run
```

**Sync Logic:**
- Only updates genealogy fields (relationships, notes, dates)
- Preserves existing person records and film associations
- Adds missing relationships without overwriting existing ones
- Validates relationship targets exist before creating links
- Reports statistics on sync operations

### 3. Data Validation (`genealogy_manager.py validate`)
Performs integrity checks on genealogy relationships:

```bash
python scripts/genealogy_manager.py validate
```

**Validation Checks:**
- Circular relationship detection (person as own parent/spouse)
- Impossible relationships (father equals mother)
- Mutual spouse relationship verification
- Generational loop detection
- Orphaned relationship references

### 4. Comprehensive Reporting (`genealogy_manager.py report`)
Generates detailed genealogy analysis reports:

```bash
python scripts/genealogy_manager.py report --output-file genealogy_report.json
```

**Report Contents:**
- Complete family tree structure
- Relationship statistics and coverage
- People with children counts
- Largest family sizes
- Biography completion rates
- Film association cross-references

## Data Flow Patterns

### Development to Production Sync
1. **Export** genealogy data from local development
2. **Transfer** JSON file to production environment
3. **Sync** genealogy relationships to production database
4. **Validate** relationship integrity post-sync
5. **Report** on sync success and coverage

### Genealogy Data Management Workflow
1. **Input** - Family tree research and biographical data
2. **Import** - Add relationships through Django admin or scripts
3. **Validate** - Check for integrity issues and conflicts
4. **Export** - Backup genealogy data for preservation
5. **Sync** - Deploy verified data to production

## Integration Points

### Film Metadata Integration
- People appear in both films (FilmPeople) and genealogy trees
- Genealogy relationships provide context for film subjects
- Biography notes enhance film descriptions
- Family connections explain film participant relationships

### Production Deployment
- Genealogy data syncs independently of main film data
- Incremental updates preserve existing relationships
- Validation prevents data corruption during deployment
- Rollback capability through JSON export backups

## Security Considerations

### Data Privacy
- Biographical data may contain sensitive personal information
- Export files should be handled securely
- Production sync requires appropriate database permissions
- Backup files should be encrypted for long-term storage

### Relationship Integrity
- Validation prevents impossible family structures
- Circular relationship detection maintains data consistency
- Mutual relationship enforcement ensures bilateral accuracy
- Orphaned reference cleanup prevents broken links

## Maintenance Operations

### Regular Validation
- Run integrity checks after major genealogy updates
- Validate relationships before production deployments
- Monitor for orphaned records and circular references
- Check mutual relationship consistency

### Backup Strategy
- Export genealogy data before major changes
- Maintain versioned backups of family tree data
- Test restore procedures from JSON exports
- Document relationship changes for audit trails

## Usage Guidelines

### Best Practices
1. **Always validate** genealogy data before production sync
2. **Use dry-run mode** when testing sync operations
3. **Export backups** before making major relationship changes
4. **Check integrity** after bulk imports or updates
5. **Document sources** for genealogy information in notes fields

### Common Operations
- **Adding new family members**: Use Django admin, then validate
- **Correcting relationships**: Update via admin, export, sync to production
- **Bulk genealogy import**: Prepare JSON, import to development, validate, sync
- **Family tree analysis**: Generate reports for relationship mapping
- **Production deployment**: Export, transfer, sync, validate

This system provides comprehensive genealogy management while maintaining data integrity and supporting production deployment workflows.
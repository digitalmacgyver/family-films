# Genealogy Features Technical Design

## Architecture Overview

The genealogy features will extend the existing Family Films application with minimal architectural changes, leveraging the existing Person model and adding new views, forms, and frontend visualization.

## Database Design

### Existing Schema Utilization
Our current Person model already supports the required relationships:

```python
class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255) 
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    father = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children_as_father')
    mother = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children_as_mother')  
    spouse = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='spouse_of')
    notes = models.TextField(blank=True)
    # ... existing fields
```

### Enhanced Model Methods
Add utility methods to Person model for genealogy operations:

```python
# New methods to add to Person model
def get_parents(self):
    """Return tuple of (father, mother)"""
    
def get_children(self):
    """Return queryset of all children"""
    
def get_siblings(self):
    """Return queryset of siblings (same parents)"""
    
def get_ancestors(self, generations=3):
    """Return hierarchical dict of ancestors"""
    
def get_descendants(self, generations=3):
    """Return hierarchical dict of descendants"""
    
def get_family_tree_data(self, center_person=True):
    """Return JSON-serializable family tree data"""
```

### Data Validation
Implement model validation to ensure data integrity:

```python
def clean(self):
    """Validate person relationships"""
    # Prevent self-reference
    if self.father == self or self.mother == self or self.spouse == self:
        raise ValidationError("Person cannot be their own relative")
    
    # Prevent circular relationships (basic check)
    if self.father and self._check_circular_ancestry(self.father):
        raise ValidationError("Circular ancestry detected")
```

## URL Structure

```
/genealogy/                          # Main genealogy page
/genealogy/tree/                     # Interactive family tree
/genealogy/tree/<int:person_id>/     # Tree centered on specific person
/genealogy/person/<int:pk>/edit/     # Edit person relationships
/genealogy/person/<int:pk>/bio/      # Biography view/edit
/api/genealogy/tree/<int:person_id>/ # API endpoint for tree data
```

## Backend Implementation

### Views Architecture

```python
# genealogy/views.py

class GenealogyHomeView(TemplateView):
    """Main genealogy landing page"""
    
class FamilyTreeView(DetailView):
    """Interactive family tree centered on a person"""
    
class PersonRelationshipEditView(UpdateView):
    """Edit person's family relationships"""
    
class PersonBiographyView(DetailView):
    """Display person biography"""
    
class PersonBiographyEditView(UpdateView):
    """Edit person biography"""
    
# API Views
class FamilyTreeAPIView(APIView):
    """JSON API for family tree data"""
```

### Forms Design

```python
# genealogy/forms.py

class PersonRelationshipForm(forms.ModelForm):
    """Form for editing person relationships"""
    
    class Meta:
        model = Person
        fields = ['father', 'mother', 'spouse']
        widgets = {
            'father': forms.Select(attrs={'class': 'form-control'}),
            'mother': forms.Select(attrs={'class': 'form-control'}), 
            'spouse': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude self from relationship choices
        if self.instance and self.instance.pk:
            queryset = Person.objects.exclude(pk=self.instance.pk)
            self.fields['father'].queryset = queryset.filter(/* male filter if available */)
            self.fields['mother'].queryset = queryset.filter(/* female filter if available */)
            self.fields['spouse'].queryset = queryset

class PersonBiographyForm(forms.ModelForm):
    """Form for editing person biography"""
    
    class Meta:
        model = Person
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter biographical information...'
            })
        }
```

## Frontend Implementation

### Template Structure

```
templates/genealogy/
├── base.html                 # Base template with genealogy navigation
├── home.html                # Main genealogy landing page
├── tree.html                # Interactive family tree page
├── person_edit.html         # Edit person relationships
├── person_bio.html          # Person biography view
└── person_bio_edit.html     # Edit person biography
```

### Family Tree Visualization

Use the family-chart JavaScript library for interactive visualization:

```html
<!-- tree.html -->
<div id="family-tree-container"></div>

<script src="https://unpkg.com/d3@5/dist/d3.min.js"></script>
<script src="https://unpkg.com/family-chart/dist/family-chart.min.js"></script>

<script>
// Initialize family tree
const familyChart = new FamilyChart('#family-tree-container', {
    data: familyTreeData,  // Loaded from Django API
    width: 800,
    height: 600,
    // Configuration options
});
</script>
```

### Data Flow for Tree Visualization

1. Django view renders tree.html with person_id
2. JavaScript makes AJAX call to `/api/genealogy/tree/<person_id>/`
3. Django API returns JSON tree data
4. family-chart library renders interactive tree
5. User clicks on person → reload tree centered on that person

## API Design

### Family Tree Data Format

```json
{
  "person": {
    "id": 123,
    "name": "John Hayward Sr.",
    "birth_date": "1920-01-01",
    "death_date": null,
    "notes_preview": "Born in Michigan..."
  },
  "parents": [
    {
      "id": 124, 
      "name": "Earl Hayward",
      "relation": "father"
    },
    {
      "id": 125,
      "name": "Rosabell Hayward", 
      "relation": "mother"
    }
  ],
  "spouse": {
    "id": 126,
    "name": "Josephine Hayward (nee Myre)"
  },
  "children": [
    {
      "id": 127,
      "name": "John Hayward Jr."
    },
    {
      "id": 128, 
      "name": "Joy Hofer (nee Hayward)"
    }
  ],
  "siblings": [
    {
      "id": 129,
      "name": "Marjorie Lindner (nee Hayward)"
    }
  ]
}
```

## Integration with Existing Features

### Navigation Updates
Add genealogy section to main navigation:

```html
<!-- base.html navigation -->
<nav class="navbar">
  <ul class="nav">
    <li><a href="/">Films</a></li>
    <li><a href="/people/">People</a></li>
    <li><a href="/locations/">Locations</a></li>
    <li><a href="/genealogy/">Genealogy</a></li> <!-- NEW -->
  </ul>
</nav>
```

### Person Page Enhancements
Add genealogy links to existing person detail pages:

```html
<!-- people/detail.html -->
<div class="person-actions">
  <a href="/genealogy/tree/{{ person.id }}/" class="btn btn-info">
    View Family Tree
  </a>
  <a href="/genealogy/person/{{ person.id }}/edit/" class="btn btn-secondary">
    Edit Relationships
  </a>
</div>
```

## Security Considerations

### Access Control
- All genealogy features require authenticated users
- Admin users can edit any person's relationships
- Regular users can only view genealogy data

### Data Validation
- Server-side validation prevents circular relationships
- Form validation provides immediate feedback
- Database constraints ensure data integrity

### Privacy
- Biographical notes may contain sensitive information
- Consider adding privacy levels in future versions

## Performance Considerations

### Database Optimization
- Add indexes for relationship lookups:
  ```sql
  CREATE INDEX idx_person_father ON main_person(father_id);
  CREATE INDEX idx_person_mother ON main_person(mother_id);
  CREATE INDEX idx_person_spouse ON main_person(spouse_id);
  ```

### Query Optimization
- Use select_related() for relationship queries
- Implement caching for frequently accessed trees
- Limit tree depth to prevent performance issues

### Frontend Performance
- Lazy load tree data via AJAX
- Implement tree virtualization for large families
- Cache tree visualizations in browser storage

## Testing Strategy

### Unit Tests
- Model method tests (get_ancestors, get_descendants)
- Form validation tests
- API endpoint tests

### Integration Tests
- Full genealogy workflow tests
- Relationship consistency tests
- Tree visualization rendering tests

### Data Integrity Tests
- Circular relationship prevention
- Bulk relationship updates
- Edge case handling (orphaned records)

## Deployment Considerations

### Database Migrations
- Add indexes for new relationship queries
- Validate existing data integrity
- Create database constraints

### Static Files
- Include family-chart library assets
- Optimize CSS for genealogy pages
- Ensure responsive design

### Configuration
- Add genealogy feature flags if needed
- Configure caching for tree data
- Set up monitoring for performance

## Future Extensions

### Phase 2 Enhancements
- Rich text editor for biographies
- Photo galleries for each person
- Timeline view of family events
- Advanced search and filtering

### Integration Opportunities
- GEDCOM import/export
- Integration with external genealogy APIs
- Automated relationship suggestions
- DNA matching integration (future)

## Implementation Timeline

### Week 1: Backend Foundation
- Enhance Person model methods
- Create basic views and forms
- Implement data validation
- Set up URL routing

### Week 2: Basic UI
- Create genealogy templates
- Implement relationship editing forms
- Add biography management
- Basic navigation integration

### Week 3: Tree Visualization
- Integrate family-chart library
- Create tree data API
- Implement interactive tree
- Add responsive design

### Week 4: Polish & Testing
- Comprehensive testing
- Performance optimization
- Documentation
- Bug fixes and refinement

This design provides a solid foundation for implementing genealogy features while maintaining the existing application architecture and leveraging the current data model.
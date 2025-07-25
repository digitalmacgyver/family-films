from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.postgres.search import SearchVector
import re


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    father = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children_as_father')
    mother = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children_as_mother')
    spouse = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='spouse_of')
    notes = models.TextField(blank=True)
    hayward_index = models.IntegerField(null=True, blank=True, help_text="Position in Haywards Present bitfield")
    
    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = [['first_name', 'last_name']]
        indexes = [
            models.Index(fields=['last_name']),
            models.Index(fields=['hayward_index']),
        ]
    
    def __str__(self):
        return self.full_name()
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_name_reversed(self):
        """Return name in 'LASTNAME, FIRSTNAME' format"""
        return f"{self.last_name}, {self.first_name}"
    
    def is_hayward_family(self):
        return self.hayward_index is not None
    
    def get_absolute_url(self):
        return reverse('people:detail', kwargs={'pk': self.pk})
    
    def get_age_at_death(self):
        """Calculate age at death if both birth and death dates are available"""
        if self.birth_date and self.death_date:
            return self.death_date.year - self.birth_date.year
        return None
    
    # Genealogy methods
    def get_parents(self):
        """Return tuple of (father, mother)"""
        return (self.father, self.mother)
    
    def get_children(self):
        """Return queryset of all children"""
        return Person.objects.filter(
            models.Q(father=self) | models.Q(mother=self)
        ).order_by('birth_date', 'first_name')
    
    def get_siblings(self):
        """Return queryset of siblings (same parents, excluding self)"""
        if not self.father and not self.mother:
            return Person.objects.none()
        
        siblings_query = models.Q()
        if self.father:
            siblings_query |= models.Q(father=self.father)
        if self.mother:
            siblings_query |= models.Q(mother=self.mother)
        
        return Person.objects.filter(siblings_query).exclude(pk=self.pk).distinct().order_by('birth_date', 'first_name')
    
    def get_ancestors(self, generations=3):
        """Return hierarchical dict of ancestors up to specified generations"""
        if generations <= 0:
            return {}
        
        ancestors = {}
        if self.father:
            ancestors['father'] = {
                'person': self.father,
                'ancestors': self.father.get_ancestors(generations - 1)
            }
        if self.mother:
            ancestors['mother'] = {
                'person': self.mother,
                'ancestors': self.mother.get_ancestors(generations - 1)
            }
        
        return ancestors
    
    def get_descendants(self, generations=3):
        """Return hierarchical dict of descendants up to specified generations"""
        if generations <= 0:
            return {}
        
        descendants = {}
        children = self.get_children()
        
        for child in children:
            descendants[child.pk] = {
                'person': child,
                'descendants': child.get_descendants(generations - 1)
            }
        
        return descendants
    
    def get_family_tree_data(self, center_person=True):
        """Return JSON-serializable family tree data"""
        data = {
            'person': {
                'id': self.pk,
                'name': self.full_name(),
                'birth_date': self.birth_date.isoformat() if self.birth_date else None,
                'death_date': self.death_date.isoformat() if self.death_date else None,
                'notes_preview': self.notes[:100] + '...' if len(self.notes) > 100 else self.notes
            }
        }
        
        # Add parents
        parents = []
        if self.father:
            parents.append({
                'id': self.father.pk,
                'name': self.father.full_name(),
                'relation': 'father',
                'birth_date': self.father.birth_date.isoformat() if self.father.birth_date else None,
                'death_date': self.father.death_date.isoformat() if self.father.death_date else None,
            })
        if self.mother:
            parents.append({
                'id': self.mother.pk,
                'name': self.mother.full_name(),
                'relation': 'mother',
                'birth_date': self.mother.birth_date.isoformat() if self.mother.birth_date else None,
                'death_date': self.mother.death_date.isoformat() if self.mother.death_date else None,
            })
        data['parents'] = parents
        
        # Add spouse
        if self.spouse:
            data['spouse'] = {
                'id': self.spouse.pk,
                'name': self.spouse.full_name(),
                'birth_date': self.spouse.birth_date.isoformat() if self.spouse.birth_date else None,
                'death_date': self.spouse.death_date.isoformat() if self.spouse.death_date else None,
            }
        else:
            data['spouse'] = None
        
        # Add children
        children = []
        for child in self.get_children():
            children.append({
                'id': child.pk,
                'name': child.full_name(),
                'birth_date': child.birth_date.isoformat() if child.birth_date else None,
                'death_date': child.death_date.isoformat() if child.death_date else None,
            })
        data['children'] = children
        
        # Add siblings
        siblings = []
        for sibling in self.get_siblings():
            siblings.append({
                'id': sibling.pk,
                'name': sibling.full_name(),
                'birth_date': sibling.birth_date.isoformat() if sibling.birth_date else None,
                'death_date': sibling.death_date.isoformat() if sibling.death_date else None,
            })
        data['siblings'] = siblings
        
        return data
    
    def clean(self):
        """Validate person relationships"""
        from django.core.exceptions import ValidationError
        
        # Prevent self-reference
        if self.father == self:
            raise ValidationError("Person cannot be their own father")
        if self.mother == self:
            raise ValidationError("Person cannot be their own mother")
        if self.spouse == self:
            raise ValidationError("Person cannot be their own spouse")
        
        # Basic circular relationship check for parents
        if self.father and self._check_circular_ancestry(self.father):
            raise ValidationError("Circular ancestry detected with father")
        if self.mother and self._check_circular_ancestry(self.mother):
            raise ValidationError("Circular ancestry detected with mother")
    
    def _check_circular_ancestry(self, ancestor, visited=None):
        """Check for circular ancestry relationships"""
        if visited is None:
            visited = set()
        
        if ancestor.pk in visited:
            return True
        
        visited.add(ancestor.pk)
        
        # Check if this person appears as an ancestor of the proposed ancestor
        if ancestor.father and ancestor.father.pk == self.pk:
            return True
        if ancestor.mother and ancestor.mother.pk == self.pk:
            return True
        
        # Recursively check ancestors
        if ancestor.father and self._check_circular_ancestry(ancestor.father, visited.copy()):
            return True
        if ancestor.mother and self._check_circular_ancestry(ancestor.mother, visited.copy()):
            return True
        
        return False
    
    def save(self, *args, **kwargs):
        """Override save to handle bidirectional spouse relationships"""
        # Get the original spouse before saving (if this is an update)
        original_spouse = None
        if self.pk:
            try:
                original_spouse = Person.objects.get(pk=self.pk).spouse
            except Person.DoesNotExist:
                pass
        
        # Save the current instance first
        super().save(*args, **kwargs)
        
        # Handle spouse relationship changes
        current_spouse = self.spouse
        
        # If spouse changed, update relationships
        if original_spouse != current_spouse:
            # Clear old spouse relationship (set their spouse to None)
            if original_spouse and original_spouse.spouse == self:
                original_spouse.spouse = None
                # Use update to avoid triggering save() recursion
                Person.objects.filter(pk=original_spouse.pk).update(spouse=None)
            
            # Set new spouse relationship (set their spouse to self)
            if current_spouse and current_spouse.spouse != self:
                # Use update to avoid triggering save() recursion
                Person.objects.filter(pk=current_spouse.pk).update(spouse=self.pk)


class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="USA")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['city', 'state']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('locations:detail', kwargs={'pk': self.pk})


class Tag(models.Model):
    CATEGORY_CHOICES = [
        ('holidays', 'Holidays'),
        ('events', 'Events'),
        ('activities', 'Activities'),
        ('people', 'People'),
        ('places', 'Places'),
        ('themes', 'Themes'),
        ('other', 'Other'),
    ]
    
    tag = models.CharField(max_length=100, primary_key=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['tag']
    
    def __str__(self):
        return self.tag


class DigitalReel(models.Model):
    reel_id = models.CharField(max_length=50, primary_key=True, help_text="Label from physical canister")
    filename = models.CharField(max_length=200)
    format = models.CharField(max_length=20, choices=[
        ('16mm', '16mm'),
        ('8mm', '8mm'),
        ('super8', 'Super 8'),
        ('other', 'Other'),
    ])
    fps = models.IntegerField(help_text="Original frames per second")
    frame_count = models.IntegerField(help_text="Total number of frames")
    has_sound = models.BooleanField(default=False)
    scan_batch = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    scan_resolution = models.CharField(max_length=20, help_text="e.g., 4976x3472")
    
    class Meta:
        ordering = ['reel_id']
    
    def __str__(self):
        return self.reel_id


class Film(models.Model):
    file_id = models.CharField(max_length=50, unique=True, help_text="Unique identifier matching CSV file ID")
    youtube_url = models.URLField()
    youtube_id = models.CharField(max_length=50, unique=True, help_text="YouTube video ID for embedding")
    title = models.CharField(max_length=500)
    description = models.TextField()
    summary = models.TextField(help_text="Brief summary of film contents")
    duration = models.DurationField(null=True, blank=True)
    upload_date = models.DateField(null=True, blank=True)
    thumbnail_url = models.URLField(help_text="YouTube thumbnail URL (maxresdefault)")
    thumbnail_high_url = models.URLField(blank=True, help_text="High quality thumbnail (hqdefault)")
    thumbnail_medium_url = models.URLField(blank=True, help_text="Medium quality thumbnail (mqdefault)")
    
    # Animated thumbnail support
    preview_sprite_url = models.URLField(blank=True, help_text="Path to sprite sheet for hover animation")
    preview_frame_count = models.IntegerField(default=0, help_text="Number of frames in preview")
    preview_frame_interval = models.FloatField(default=0.0, help_text="Seconds between preview frames")
    preview_sprite_width = models.IntegerField(default=0, help_text="Width of individual sprite frames")
    preview_sprite_height = models.IntegerField(default=0, help_text="Height of individual sprite frames")
    
    # Metadata
    years = models.CharField(max_length=100, blank=True, help_text="Years when filmed")
    technical_notes = models.TextField(blank=True)
    workflow_state = models.CharField(max_length=50, blank=True)
    playlist_order = models.IntegerField(null=True, blank=True, help_text="Order in YouTube playlist")
    
    # Search vector for full-text search
    # Note: This will be populated in views/managers, not as a model field
    
    # Relationships
    people = models.ManyToManyField(Person, through='FilmPeople', blank=True)
    locations = models.ManyToManyField(Location, through='FilmLocations', blank=True)
    tags = models.ManyToManyField(Tag, through='FilmTags', blank=True)
    
    class Meta:
        ordering = ['-upload_date', 'title']
        indexes = [
            models.Index(fields=['file_id']),
            models.Index(fields=['youtube_id']),
            models.Index(fields=['upload_date']),
            models.Index(fields=['years']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('films:detail', kwargs={'file_id': self.file_id})
    
    def get_youtube_embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}"
    
    def get_year_list(self):
        """Parse years string into list of integers"""
        if not self.years:
            return []
        years = re.findall(r'\d{4}', self.years)
        return sorted([int(year) for year in years])
    
    def has_animated_thumbnail(self):
        """Check if film has either sprite-based or chapter-based animation"""
        return bool(self.preview_sprite_url and self.preview_frame_count > 0) or self.has_chapter_thumbnails()
    
    def has_chapter_thumbnails(self):
        """Check if film has chapter thumbnails for animation"""
        return self.chapters.exclude(thumbnail_url__isnull=True).exclude(thumbnail_url__exact="").count() >= 2
    
    def get_chapter_thumbnail_urls(self):
        """Get list of chapter thumbnail URLs for animation"""
        return list(self.chapters.exclude(thumbnail_url__isnull=True).exclude(thumbnail_url__exact="")
                   .order_by('order').values_list('thumbnail_url', flat=True))


class Chapter(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='chapters')
    start_time = models.CharField(max_length=20, help_text="MM:SS or HH:MM:SS format")
    start_time_seconds = models.IntegerField(help_text="Start time converted to seconds")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    years = models.CharField(max_length=100, blank=True, help_text="Years when this chapter was filmed")
    order = models.IntegerField()
    
    # Chapter thumbnail
    thumbnail_url = models.URLField(blank=True, help_text="Thumbnail image URL for this chapter")
    
    # Metadata indicators for UI
    has_people_metadata = models.BooleanField(default=False)
    has_location_metadata = models.BooleanField(default=False)
    has_tags_metadata = models.BooleanField(default=False)
    has_years_metadata = models.BooleanField(default=False)
    
    # Relationships
    people = models.ManyToManyField(Person, through='ChapterPeople', blank=True)
    locations = models.ManyToManyField(Location, through='ChapterLocations', blank=True)
    tags = models.ManyToManyField(Tag, through='ChapterTags', blank=True)
    
    class Meta:
        ordering = ['film', 'order']
        indexes = [
            models.Index(fields=['film', 'order']),
            models.Index(fields=['start_time_seconds']),
            models.Index(fields=['years']),
        ]
    
    def __str__(self):
        return f"{self.film.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Convert start_time to seconds
        self.start_time_seconds = self.parse_time_to_seconds(self.start_time)
        super().save(*args, **kwargs)
    
    @staticmethod
    def parse_time_to_seconds(time_str):
        """Convert MM:SS or HH:MM:SS to seconds"""
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    def update_metadata_flags(self):
        """Update metadata indicator flags"""
        self.has_people_metadata = self.people.exists()
        self.has_location_metadata = self.locations.exists()
        self.has_tags_metadata = self.tags.exists()
        self.has_years_metadata = bool(self.years and self.years.strip())
        self.save(update_fields=['has_people_metadata', 'has_location_metadata', 'has_tags_metadata', 'has_years_metadata'])
    
    def get_thumbnail_url(self):
        """Get thumbnail URL with fallback to film thumbnail"""
        if self.thumbnail_url:
            return self.thumbnail_url
        # Fallback to film's thumbnail or YouTube thumbnail variants
        # Use different YouTube thumbnail types for variety
        variants = ['1', '2', '3', 'default']
        variant = variants[self.order % len(variants)]
        return f"https://img.youtube.com/vi/{self.film.youtube_id}/{variant}.jpg"


# Association Tables

class FilmPeople(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False, help_text="Main subject of film")
    
    class Meta:
        unique_together = ('film', 'person')


class FilmLocations(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False, help_text="Main location")
    
    class Meta:
        unique_together = ('film', 'location')


class FilmTags(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    is_auto = models.BooleanField(default=False, help_text="Applied by automation")
    
    class Meta:
        unique_together = ('film', 'tag')


class ChapterPeople(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False, help_text="Main person in this chapter")
    confidence = models.FloatField(null=True, blank=True, help_text="AI confidence score for auto-tagging")
    
    class Meta:
        unique_together = ('chapter', 'person')


class ChapterLocations(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False, help_text="Main location for this chapter")
    
    class Meta:
        unique_together = ('chapter', 'location')


class ChapterTags(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    is_auto = models.BooleanField(default=False, help_text="Applied by automation")
    confidence = models.FloatField(null=True, blank=True, help_text="AI confidence score")
    
    class Meta:
        unique_together = ('chapter', 'tag')


# Legacy models for sequences (if needed)
class Sequence(models.Model):
    reel = models.ForeignKey(DigitalReel, on_delete=models.CASCADE, related_name='sequences')
    sequence_num = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_frame = models.IntegerField()
    duration_frames = models.IntegerField()
    start_time_16fps = models.FloatField(help_text="Start time in seconds at 16fps")
    intro_text = models.TextField(blank=True)
    
    # Relationships
    people = models.ManyToManyField(Person, through='SequencePeople', blank=True)
    locations = models.ManyToManyField(Location, through='SequenceLocations', blank=True)
    tags = models.ManyToManyField(Tag, through='SequenceTags', blank=True)
    
    class Meta:
        ordering = ['reel', 'sequence_num']
        unique_together = ('reel', 'sequence_num')
    
    def __str__(self):
        return f"{self.reel.reel_id} - {self.title}"


class SequencePeople(models.Model):
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('sequence', 'person')


class SequenceLocations(models.Model):
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('sequence', 'location')


class SequenceTags(models.Model):
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    is_auto = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('sequence', 'tag')
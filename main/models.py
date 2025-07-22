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
        indexes = [
            models.Index(fields=['last_name']),
            models.Index(fields=['hayward_index']),
        ]
    
    def __str__(self):
        return self.full_name()
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_hayward_family(self):
        return self.hayward_index is not None
    
    def get_absolute_url(self):
        return reverse('people:detail', kwargs={'pk': self.pk})


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
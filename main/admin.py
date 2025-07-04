from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Person, Location, Tag, DigitalReel, Film, Chapter,
    FilmPeople, FilmLocations, FilmTags,
    ChapterPeople, ChapterLocations, ChapterTags,
    Sequence, SequencePeople, SequenceLocations, SequenceTags
)


class FilmPeopleInline(admin.TabularInline):
    model = FilmPeople
    extra = 1
    autocomplete_fields = ['person']


class FilmLocationsInline(admin.TabularInline):
    model = FilmLocations
    extra = 1
    autocomplete_fields = ['location']


class FilmTagsInline(admin.TabularInline):
    model = FilmTags
    extra = 1
    autocomplete_fields = ['tag']


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ['order', 'start_time', 'title', 'has_people_metadata', 'has_location_metadata', 'has_tags_metadata']
    readonly_fields = ['has_people_metadata', 'has_location_metadata', 'has_tags_metadata']


class ChapterPeopleInline(admin.TabularInline):
    model = ChapterPeople
    extra = 1
    autocomplete_fields = ['person']


class ChapterLocationsInline(admin.TabularInline):
    model = ChapterLocations
    extra = 1
    autocomplete_fields = ['location']


class ChapterTagsInline(admin.TabularInline):
    model = ChapterTags
    extra = 1
    autocomplete_fields = ['tag']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_date', 'hayward_index', 'is_hayward_family']
    list_filter = ['hayward_index']
    search_fields = ['first_name', 'last_name']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'notes')
        }),
        ('Family Information', {
            'fields': ('birth_date', 'death_date', 'father', 'mother', 'spouse', 'hayward_index')
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'country']
    list_filter = ['state', 'country']
    search_fields = ['name', 'city', 'state', 'description']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['tag', 'category', 'description']
    list_filter = ['category']
    search_fields = ['tag', 'description']
    ordering = ['tag']


@admin.register(DigitalReel)
class DigitalReelAdmin(admin.ModelAdmin):
    list_display = ['reel_id', 'format', 'fps', 'has_sound', 'scan_batch']
    list_filter = ['format', 'has_sound', 'scan_batch']
    search_fields = ['reel_id', 'filename']
    ordering = ['reel_id']


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_id', 'years', 'duration', 'has_animated_thumbnail', 'workflow_state']
    list_filter = ['workflow_state', 'upload_date']
    search_fields = ['title', 'file_id', 'description', 'summary']
    ordering = ['-upload_date', 'title']
    
    inlines = [ChapterInline, FilmPeopleInline, FilmLocationsInline, FilmTagsInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('file_id', 'title', 'summary', 'description')
        }),
        ('YouTube Information', {
            'fields': ('youtube_url', 'youtube_id', 'thumbnail_url', 'duration', 'upload_date')
        }),
        ('Animated Thumbnails', {
            'fields': ('preview_sprite_url', 'preview_frame_count', 'preview_frame_interval', 
                      'preview_sprite_width', 'preview_sprite_height'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('years', 'technical_notes', 'workflow_state')
        }),
    )
    
    def has_animated_thumbnail(self, obj):
        return obj.has_animated_thumbnail()
    has_animated_thumbnail.boolean = True
    has_animated_thumbnail.short_description = 'Animated Thumbnail'
    
    def get_youtube_link(self, obj):
        if obj.youtube_url:
            return format_html('<a href="{}" target="_blank">View on YouTube</a>', obj.youtube_url)
        return '-'
    get_youtube_link.short_description = 'YouTube Link'


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['film', 'order', 'start_time', 'title', 'metadata_indicators']
    list_filter = ['film', 'has_people_metadata', 'has_location_metadata', 'has_tags_metadata']
    search_fields = ['title', 'description', 'film__title']
    ordering = ['film', 'order']
    
    inlines = [ChapterPeopleInline, ChapterLocationsInline, ChapterTagsInline]
    
    def metadata_indicators(self, obj):
        indicators = []
        if obj.has_people_metadata:
            indicators.append('👥 People')
        if obj.has_location_metadata:
            indicators.append('📍 Location')
        if obj.has_tags_metadata:
            indicators.append('🏷️ Tags')
        return ' | '.join(indicators) if indicators else 'No metadata'
    metadata_indicators.short_description = 'Metadata'
    
    actions = ['update_metadata_flags']
    
    def update_metadata_flags(self, request, queryset):
        for chapter in queryset:
            chapter.update_metadata_flags()
        self.message_user(request, f'Updated metadata flags for {queryset.count()} chapters.')
    update_metadata_flags.short_description = 'Update metadata flags'


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ['reel', 'sequence_num', 'title', 'start_frame', 'duration_frames']
    list_filter = ['reel']
    search_fields = ['title', 'description', 'reel__reel_id']
    ordering = ['reel', 'sequence_num']


# Register association models for direct editing if needed
admin.site.register(FilmPeople)
admin.site.register(FilmLocations)
admin.site.register(FilmTags)
admin.site.register(ChapterPeople)
admin.site.register(ChapterLocations)
admin.site.register(ChapterTags)
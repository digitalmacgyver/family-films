from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import timedelta
import json

from main.models import Film, Chapter, Person, Location, Tag


class MetadataEditingTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        
        # Create test film
        self.film = Film.objects.create(
            file_id='TEST-001',
            title='Test Film',
            description='Test Description',
            years='2023',
            duration=timedelta(hours=1, minutes=30),
            youtube_id='test_youtube_id',
            thumbnail_url='https://example.com/thumb.jpg'
        )
        
        # Create test chapter
        self.chapter = Chapter.objects.create(
            film=self.film,
            title='Test Chapter',
            start_time='05:00',
            order=1,
            description='Test chapter description'
        )
        
        # Create test metadata objects
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe'
        )
        
        self.location = Location.objects.create(
            name='Test Location',
            city='Test City'
        )
        
        self.tag = Tag.objects.create(
            tag='test-tag'
        )
    
    def test_film_metadata_addition(self):
        """Test adding people, locations, and tags to films"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add person to film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'people',
                'action': 'add',
                'value': 'Jane Smith'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify person was added
        self.film.refresh_from_db()
        self.assertTrue(self.film.people.filter(first_name='Jane', last_name='Smith').exists())
        
        # Add location to film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'locations',
                'action': 'add',
                'value': 'New York'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify location was added
        self.film.refresh_from_db()
        self.assertTrue(self.film.locations.filter(name='New York').exists())
        
        # Add tag to film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'tags',
                'action': 'add',
                'value': 'family'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify tag was added
        self.film.refresh_from_db()
        self.assertTrue(self.film.tags.filter(tag='family').exists())
    
    def test_film_metadata_removal(self):
        """Test removing people, locations, and tags from films"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add metadata first
        self.film.people.add(self.person)
        self.film.locations.add(self.location)
        self.film.tags.add(self.tag)
        
        # Remove person from film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'people',
                'action': 'remove',
                'id': self.person.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify person was removed
        self.film.refresh_from_db()
        self.assertFalse(self.film.people.filter(id=self.person.id).exists())
        
        # Remove location from film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'locations',
                'action': 'remove',
                'id': self.location.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify location was removed
        self.film.refresh_from_db()
        self.assertFalse(self.film.locations.filter(id=self.location.id).exists())
        
        # Remove tag from film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'tags',
                'action': 'remove',
                'id': self.tag.tag
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify tag was removed
        self.film.refresh_from_db()
        self.assertFalse(self.film.tags.filter(tag=self.tag.tag).exists())
    
    def test_film_years_update(self):
        """Test updating film years"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('films:update_film_years', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'years': '2022, 2023'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify years were updated
        self.film.refresh_from_db()
        self.assertEqual(self.film.years, '2022, 2023')
    
    def test_chapter_metadata_addition(self):
        """Test adding people, locations, and tags to chapters"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add person to chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'people',
                'action': 'add',
                'value': 'Bob Johnson'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify person was added
        self.chapter.refresh_from_db()
        self.assertTrue(self.chapter.people.filter(first_name='Bob', last_name='Johnson').exists())
        
        # Add location to chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'locations',
                'action': 'add',
                'value': 'San Francisco'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify location was added
        self.chapter.refresh_from_db()
        self.assertTrue(self.chapter.locations.filter(name='San Francisco').exists())
        
        # Add tag to chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'tags',
                'action': 'add',
                'value': 'vacation'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify tag was added
        self.chapter.refresh_from_db()
        self.assertTrue(self.chapter.tags.filter(tag='vacation').exists())
    
    def test_chapter_metadata_removal(self):
        """Test removing people, locations, and tags from chapters"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add metadata first
        self.chapter.people.add(self.person)
        self.chapter.locations.add(self.location)
        self.chapter.tags.add(self.tag)
        
        # Remove person from chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'people',
                'action': 'remove',
                'id': self.person.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify person was removed
        self.chapter.refresh_from_db()
        self.assertFalse(self.chapter.people.filter(id=self.person.id).exists())
        
        # Remove location from chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'locations',
                'action': 'remove',
                'id': self.location.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify location was removed
        self.chapter.refresh_from_db()
        self.assertFalse(self.chapter.locations.filter(id=self.location.id).exists())
        
        # Remove tag from chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'tags',
                'action': 'remove',
                'id': self.tag.tag
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify tag was removed
        self.chapter.refresh_from_db()
        self.assertFalse(self.chapter.tags.filter(tag=self.tag.tag).exists())
    
    def test_chapter_notes_update(self):
        """Test updating chapter notes"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('films:update_chapter_notes', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'notes': 'Updated chapter notes'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify notes were updated
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.description, 'Updated chapter notes')
    
    def test_autocomplete_endpoints(self):
        """Test autocomplete endpoints for metadata"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test people autocomplete
        response = self.client.get(
            reverse('films:people_autocomplete') + '?q=John'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['text'], 'John Doe')
        
        # Test locations autocomplete
        response = self.client.get(
            reverse('films:locations_autocomplete') + '?q=Test'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['text'], 'Test Location')
        
        # Test tags autocomplete
        response = self.client.get(
            reverse('films:tags_autocomplete') + '?q=test'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['text'], 'test-tag')
    
    def test_authentication_required(self):
        """Test that authentication is required for editing operations"""
        # Test without authentication
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'type': 'people',
                'action': 'add',
                'value': 'Test Person'
            }),
            content_type='application/json'
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Test chapter metadata without authentication
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'type': 'people',
                'action': 'add',
                'value': 'Test Person'
            }),
            content_type='application/json'
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Test years update without authentication
        response = self.client.post(
            reverse('films:update_film_years', kwargs={'file_id': self.film.file_id}),
            data=json.dumps({
                'years': '2024'
            }),
            content_type='application/json'
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Test chapter notes without authentication
        response = self.client.post(
            reverse('films:update_chapter_notes', kwargs={'chapter_id': self.chapter.id}),
            data=json.dumps({
                'notes': 'Test notes'
            }),
            content_type='application/json'
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_get_chapter_metadata(self):
        """Test retrieving chapter metadata"""
        # Add metadata to chapter
        self.chapter.people.add(self.person)
        self.chapter.locations.add(self.location)
        self.chapter.tags.add(self.tag)
        
        response = self.client.get(
            reverse('films:get_chapter_metadata', kwargs={'chapter_id': self.chapter.id})
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['people']), 1)
        self.assertEqual(len(data['locations']), 1)
        self.assertEqual(len(data['tags']), 1)
        self.assertEqual(data['notes'], 'Test chapter description')
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test invalid JSON
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': self.film.file_id}),
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test non-existent film
        response = self.client.post(
            reverse('films:update_film_metadata', kwargs={'file_id': 'NON-EXISTENT'}),
            data=json.dumps({
                'type': 'people',
                'action': 'add',
                'value': 'Test Person'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        
        # Test non-existent chapter
        response = self.client.post(
            reverse('films:update_chapter_metadata', kwargs={'chapter_id': 9999}),
            data=json.dumps({
                'type': 'people',
                'action': 'add',
                'value': 'Test Person'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

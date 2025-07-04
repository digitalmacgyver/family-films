import json
import re
from difflib import SequenceMatcher
from django.core.management.base import BaseCommand, CommandError
from main.models import Film


class Command(BaseCommand):
    help = 'Match YouTube videos to film records using intelligent title matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--youtube-json',
            type=str,
            default='youtube_videos.json',
            help='JSON file with YouTube video data'
        )
        parser.add_argument(
            '--output-mapping',
            type=str,
            default='matched_youtube_mapping.csv',
            help='Output CSV with matched mappings'
        )
        parser.add_argument(
            '--confidence-threshold',
            type=float,
            default=0.6,
            help='Minimum confidence score for automatic matching (0.0-1.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show matches without creating output file'
        )

    def handle(self, *args, **options):
        youtube_json = options['youtube_json']
        output_mapping = options['output_mapping']
        confidence_threshold = options['confidence_threshold']
        dry_run = options['dry_run']

        try:
            # Load YouTube video data
            with open(youtube_json, 'r', encoding='utf-8') as f:
                youtube_videos = json.load(f)
            
            self.stdout.write(f'Loaded {len(youtube_videos)} YouTube videos')
            
            # Get all films
            films = Film.objects.all()
            self.stdout.write(f'Found {films.count()} films in database')
            
            # Perform matching
            matches = self.match_videos_to_films(youtube_videos, films, confidence_threshold)
            
            # Display results
            self.display_matches(matches)
            
            if not dry_run:
                # Create output CSV
                self.create_mapping_csv(matches, output_mapping)
                self.stdout.write(
                    self.style.SUCCESS(f'Created mapping file: {output_mapping}')
                )
            
        except FileNotFoundError:
            raise CommandError(f'YouTube JSON file not found: {youtube_json}')
        except Exception as e:
            raise CommandError(f'Error processing data: {e}')

    def match_videos_to_films(self, youtube_videos, films, confidence_threshold):
        """Match YouTube videos to film records using title similarity"""
        matches = {
            'high_confidence': [],    # > confidence_threshold
            'medium_confidence': [],  # 0.4 - confidence_threshold
            'low_confidence': [],     # 0.2 - 0.4
            'no_match': []           # < 0.2
        }
        
        for film in films:
            best_match = None
            best_score = 0
            
            film_title_clean = self.normalize_title(film.title)
            
            for video in youtube_videos:
                video_title_clean = self.normalize_title(video['title'])
                
                # Calculate similarity score
                score = self.calculate_similarity(film_title_clean, video_title_clean)
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        'film': film,
                        'video': video,
                        'score': score,
                        'film_title': film.title,
                        'video_title': video['title']
                    }
            
            if best_match:
                if best_score >= confidence_threshold:
                    matches['high_confidence'].append(best_match)
                elif best_score >= 0.4:
                    matches['medium_confidence'].append(best_match)
                elif best_score >= 0.2:
                    matches['low_confidence'].append(best_match)
                else:
                    matches['no_match'].append(best_match)
        
        return matches

    def normalize_title(self, title):
        """Normalize title for better matching"""
        # Convert to lowercase
        title = title.lower()
        
        # Remove common words and punctuation
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\b(and|the|with|trip|to|in|at|family|hayward|haywards)\b', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title

    def calculate_similarity(self, title1, title2):
        """Calculate similarity score between two titles"""
        # Use SequenceMatcher for basic similarity
        basic_score = SequenceMatcher(None, title1, title2).ratio()
        
        # Bonus for exact word matches
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            # Combine basic score with word overlap
            combined_score = (basic_score * 0.7) + (word_overlap * 0.3)
        else:
            combined_score = basic_score
        
        return combined_score

    def display_matches(self, matches):
        """Display matching results"""
        self.stdout.write('\n=== MATCHING RESULTS ===\n')
        
        for category, match_list in matches.items():
            if not match_list:
                continue
                
            self.stdout.write(f'\n{category.upper().replace("_", " ")} ({len(match_list)} matches):')
            self.stdout.write('-' * 60)
            
            for match in match_list[:10]:  # Show first 10 matches
                score_color = self.style.SUCCESS if match['score'] >= 0.6 else \
                             self.style.WARNING if match['score'] >= 0.4 else \
                             self.style.ERROR
                
                score_text = f"{match['score']:.3f}"
                self.stdout.write(
                    f'Score: {score_color(score_text)} | '
                    f'File: {match["film"].file_id}'
                )
                self.stdout.write(f'  Film:  {match["film_title"][:70]}')
                self.stdout.write(f'  Video: {match["video_title"][:70]}')
                self.stdout.write(f'  ID:    {match["video"]["video_id"]}')
                self.stdout.write('')
            
            if len(match_list) > 10:
                self.stdout.write(f'  ... and {len(match_list) - 10} more')

    def create_mapping_csv(self, matches, output_file):
        """Create CSV file with mappings"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'file_id',
                'film_title',
                'current_youtube_id',
                'new_youtube_id',
                'new_youtube_url',
                'video_title',
                'confidence_score',
                'confidence_level',
                'action_needed'
            ])
            
            # Write matches
            for category, match_list in matches.items():
                confidence_level = category.replace('_', ' ').title()
                
                for match in match_list:
                    film = match['film']
                    video = match['video']
                    
                    # Determine action needed
                    if match['score'] >= 0.6:
                        action = 'AUTO_APPLY'
                    elif match['score'] >= 0.4:
                        action = 'REVIEW_RECOMMENDED'
                    else:
                        action = 'MANUAL_REVIEW_REQUIRED'
                    
                    writer.writerow([
                        film.file_id,
                        film.title,
                        film.youtube_id,
                        video['video_id'],
                        video['url'],
                        video['title'],
                        f"{match['score']:.3f}",
                        confidence_level,
                        action
                    ])
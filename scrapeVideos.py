import os
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import time
from typing import List, Dict, Optional
import re
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import logging
from models import (
    NFLData, SeasonData, SeasonTypeData, WeekData, Game, GameInfo,
    Teams, Team, TeamInfo, TeamLocation, TeamGameStats,
    GameSituation, Venue, BettingOdds, Score, Timeouts, PlaysResponse,
    PlaySummary, Play
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfl_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NFLGameScraper:
    def __init__(self, email=None, password=None, api_only=False, use_database=True, db_path="nfl_data.db", skip_play_summaries=False):
        # Store credentials
        self.email = email
        self.password = password
        self.api_only = api_only
        self.skip_play_summaries = skip_play_summaries
        
        # Load bearer token - handle potential dotenv escaping issues
        self.bearer_token = self._load_bearer_token()
        self.use_database = use_database
        
        # Initialize database manager if enabled
        if self.use_database:
            self.db_manager = NFLDatabaseManager(db_path)
            logger.info(f"Database storage enabled: {db_path}")
        else:
            self.db_manager = None
            logger.info("Using JSON file storage")
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retries = Retry(total=5,
                       backoff_factor=0.1,
                       status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _load_bearer_token(self):
        """Load bearer token, handling potential dotenv escaping issues."""
        # First try normal dotenv
        token = os.getenv('BEARER_TOKEN')
        
        # If token seems wrong (too long), try direct file read
        if token and len(token) > 1700:
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('BEARER_TOKEN='):
                            # Get token without the BEARER_TOKEN= prefix and strip newline
                            token = line[13:].strip()
                            logger.info(f"Loaded bearer token directly from file (length: {len(token)})")
                            return token
            except Exception as e:
                logger.warning(f"Failed to read token from .env file: {e}")
        
        if token:
            logger.info(f"Loaded bearer token from environment (length: {len(token)})")
        return token
        
        # Initialize browser only if not in API-only mode
        if not api_only:
            # Initialize Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        
        # Define season types and weeks
        self.season_types = ['REG', 'POST']  # Regular season and postseason
        self.weeks = {
            'REG': [f'WEEK_{i}' for i in range(1, 19)],  # Weeks 1-18 for regular season
<<<<<<< HEAD
            'POST': ['1', '2', '3', '4']  # Playoff weeks
=======
            'POST': ['WC', 'DIV', 'CONF', 'SB']  # Playoff weeks
>>>>>>> 756ae13 (API stats)
        }

    def generate_game_url(self, season: int, season_type: str, week: str, game_id: str) -> str:
        """Generate the URL for a specific game."""
        return f"https://pro.nfl.com/film/plays?season={season}&seasonType={season_type}&weekSlug={week}&gameId={game_id}"

    def generate_week_url(self, season: int, season_type: str, week: str) -> str:
        """Generate the URL for a specific week."""
        return f"https://pro.nfl.com/film/plays?season={season}&seasonType={season_type}&weekSlug={week}&displayGameFilmCards=true"

    def extract_game_id(self, element) -> str:
        """Extract game ID from the data-test-id attribute."""
        test_id = element.get_attribute('data-test-id')
        if test_id and test_id.startswith('game-card-'):
            return test_id.replace('game-card-', '')
        return None

    def get_game_metadata(self, game_id: str) -> Dict:
        """Fetch additional metadata for a game from the NFL API."""
        try:
            url = f"https://pro.nfl.com/api/schedules/game?gameId={game_id}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse and return the JSON response
            metadata = response.json()
            print(f"Successfully fetched metadata for game {game_id}")
            return metadata
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching metadata for game {game_id}: {str(e)}")
            return None

    def get_standings_data(self, season: int, season_type: str) -> Optional[Dict]:
        """Fetch standings data from NFL API."""
        try:
            url = f"https://pro.nfl.com/api/schedules/standings?season={season}&seasonType={season_type}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            print(f"Successfully fetched standings data for {season} {season_type}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching standings data: {str(e)}")
            return None

    def get_live_scores(self, season: int, season_type: str, week: str) -> Optional[Dict]:
        """Fetch live scores data from NFL API."""
        try:
            week_num = week.replace('WEEK_', '') if week.startswith('WEEK_') else week
            url = f"https://pro.nfl.com/api/scores/live/games?season={season}&seasonType={season_type}&week={week_num}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            print(f"Successfully fetched live scores for {season} {season_type} Week {week_num}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching live scores: {str(e)}")
            return None

    def get_odds_data(self, season: int, season_type: str, week: str) -> Optional[Dict]:
        """Fetch odds data from NFL API."""
        try:
            week_num = week.replace('WEEK_', '') if week.startswith('WEEK_') else week
            url = f"https://pro.nfl.com/api/schedules/week/odds?season={season}&seasonType={season_type}&week={week_num}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
<<<<<<< HEAD
            print(url)
=======
>>>>>>> 756ae13 (API stats)
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            print(f"Successfully fetched odds data for {season} {season_type} Week {week_num}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching odds data: {str(e)}")
            return None

    def get_play_summary(self, game_id: str, play_id: int) -> Optional[PlaySummary]:
        """Fetch detailed summary for a specific play."""
        try:
            if not self.bearer_token:
                print("Bearer token not found. Please set BEARER_TOKEN in .env file")
                return None

            url = f"https://pro.nfl.com/api/plays/summaryPlay?gameId={game_id}&playId={play_id}"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            play_summary = PlaySummary.model_validate(data)
            return play_summary
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching play summary for play {play_id}: {str(e)}")
            return None

    def get_plays_data(self, season: int, season_type: str, week: str, game_id: str) -> Optional[PlaysResponse]:
        """Fetch plays data from NFL API."""
        try:
            if not self.bearer_token:
                logger.error("Bearer token not found. Please set BEARER_TOKEN in .env file")
                return None

            url = f"https://pro.nfl.com/api/secured/videos/filmroom/plays?season={season}&seasonType={season_type}&weekSlug={week}&gameId={game_id}"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.bearer_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            logger.info(f"Fetching plays for game {game_id}")
            logger.info(f"Request URL: {url}")
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 401:
                logger.error(f"Authentication failed (401) for plays API.")
                logger.error(f"Please ensure your BEARER_TOKEN is valid and not expired.")
                return None
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch plays: HTTP {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return None
                
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Plays API response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
            plays_response = PlaysResponse.model_validate(data)
            logger.info(f"Successfully fetched {plays_response.count} plays for game {game_id}")
            
            # Fetch summary for each play (unless skipped)
            if not self.skip_play_summaries:
                for i, play in enumerate(plays_response.plays, 1):
                    try:
                        logger.info(f"[Game {game_id}] Processing play {play.play_id} ({i}/{plays_response.count})")
                        logger.debug(f"Play details: Quarter {play.quarter}, Clock {play.game_clock}, Type {play.play_type}")
                        
                        summary = self.get_play_summary(game_id, play.play_id)
                        if summary:
                            play.summary = summary
                            logger.info(f"[Game {game_id}] Successfully processed play {play.play_id}: {summary.play.play_description[:100]}...")
                        else:
                            logger.warning(f"[Game {game_id}] No summary found for play {play.play_id}")
                        
                        time.sleep(0.1)  # Small delay between requests
                    except Exception as e:
                        logger.error(f"[Game {game_id}] Error processing play {play.play_id}: {str(e)}")
                        continue
            else:
                logger.info(f"Skipping play summaries as requested")
            
            return plays_response
            
        except Exception as e:
            logger.error(f"Error fetching plays data: {str(e)}")
            return None

    def enrich_game_data(self, game_data: Dict, standings_data: Dict, live_scores: Dict, odds_data: Dict) -> Dict:
        """Enrich game data with standings, live scores, and odds information."""
        game_id = game_data['game_info']['id']
=======
    def enrich_game_data(self, game_data: Dict, standings_data: Dict, live_scores: Dict, odds_data: Dict) -> Dict:
        """Enrich game data with standings, live scores, and odds information."""
        game_id = game_data['game_id']
>>>>>>> 756ae13 (API stats)
        
        # Enrich with standings data
        if standings_data and 'weeks' in standings_data:
            latest_week = standings_data['weeks'][-1]  # Get most recent week's standings
            for team_standing in latest_week['standings']:
                team_name = team_standing['team']['fullName']
                if team_name == game_data['home_team']['name']:
                    # Extract key standings information
                    game_data['home_team']['standings'] = {
                        'team_id': team_standing['team']['id'],
                        'logo': team_standing['team']['currentLogo'],
                        'clinched': team_standing['clinched'],
                        'conference': {
                            'rank': team_standing['conference']['rank'],
                            'record': {
                                'wins': team_standing['conference']['wins'],
                                'losses': team_standing['conference']['losses'],
                                'ties': team_standing['conference']['ties'],
                                'win_pct': team_standing['conference']['winPct']
                            }
                        },
                        'division': {
                            'rank': team_standing['division']['rank'],
                            'record': {
                                'wins': team_standing['division']['wins'],
                                'losses': team_standing['division']['losses'],
                                'ties': team_standing['division']['ties'],
                                'win_pct': team_standing['division']['winPct']
                            }
                        },
                        'overall': {
                            'games_played': team_standing['overall']['games'],
                            'record': {
                                'wins': team_standing['overall']['wins'],
                                'losses': team_standing['overall']['losses'],
                                'ties': team_standing['overall']['ties'],
                                'win_pct': team_standing['overall']['winPct']
                            },
                            'points': team_standing['overall']['points'],
                            'streak': team_standing['overall']['streak']
                        },
                        'playoff_probabilities': team_standing['playoffProbs']
                    }
                elif team_name == game_data['away_team']['name']:
                    # Same structure for away team
                    game_data['away_team']['standings'] = {
                        'team_id': team_standing['team']['id'],
                        'logo': team_standing['team']['currentLogo'],
                        'clinched': team_standing['clinched'],
                        'conference': {
                            'rank': team_standing['conference']['rank'],
                            'record': {
                                'wins': team_standing['conference']['wins'],
                                'losses': team_standing['conference']['losses'],
                                'ties': team_standing['conference']['ties'],
                                'win_pct': team_standing['conference']['winPct']
                            }
                        },
                        'division': {
                            'rank': team_standing['division']['rank'],
                            'record': {
                                'wins': team_standing['division']['wins'],
                                'losses': team_standing['division']['losses'],
                                'ties': team_standing['division']['ties'],
                                'win_pct': team_standing['division']['winPct']
                            }
                        },
                        'overall': {
                            'games_played': team_standing['overall']['games'],
                            'record': {
                                'wins': team_standing['overall']['wins'],
                                'losses': team_standing['overall']['losses'],
                                'ties': team_standing['overall']['ties'],
                                'win_pct': team_standing['overall']['winPct']
                            },
                            'points': team_standing['overall']['points'],
                            'streak': team_standing['overall']['streak']
                        },
                        'playoff_probabilities': team_standing['playoffProbs']
                    }

        # Enrich with live scores
        if live_scores and 'games' in live_scores:
            for game in live_scores['games']:
                if game.get('gameId') == game_id:
                    game_data['game_details'] = {
                        'attendance': game.get('attendance'),
                        'weather': game.get('weather'),
                        'gamebook_url': game.get('gameBookUrl'),
                        'phase': game.get('phase'),
                        'display_status': game.get('displayStatus'),
                        'game_state': game.get('gameState'),
                        'clock': game.get('clock'),
                        'quarter': game.get('quarter'),
                        'scoring': {
                            'home': game['homeTeam']['score'],
                            'away': game['awayTeam']['score']
                        },
                        'timeouts': {
                            'home': game['homeTeam']['timeouts'],
                            'away': game['awayTeam']['timeouts']
                        },
                        'possession': {
                            'home': game['homeTeam'].get('hasPossession', False),
                            'away': game['awayTeam'].get('hasPossession', False)
                        },
                        'situation': {
                            'down': game.get('down'),
                            'distance': game.get('distance'),
                            'yard_line': game.get('yardLine'),
                            'is_red_zone': game.get('isRedZone'),
                            'is_goal_to_go': game.get('isGoalToGo')
                        }
                    }
                    break

        # Enrich with odds data
        if odds_data and 'games' in odds_data:
            for game in odds_data['games']:
<<<<<<< HEAD
                # Match using team abbreviations
                home_abbr = game_data['home_team'].get('abbreviation')
                away_abbr = game_data['away_team'].get('abbreviation')
                if (game.get('homeTeamAbbr') == home_abbr and 
                    game.get('visitorTeamAbbr') == away_abbr):
                    game_odds = {
=======
                # Match using gameId or team combinations
                if (str(game.get('gameKey')) == game_id or 
                    (game.get('homeTeamAbbr') == game_data['home_team'].get('abbreviation') and 
                     game.get('visitorTeamAbbr') == game_data['away_team'].get('abbreviation'))):
                    game_data['betting'] = {
>>>>>>> 756ae13 (API stats)
                        'moneyline': game.get('moneyline', {}),
                        'spread': game.get('spread', {}),
                        'totals': game.get('totals', {}),
                        'updated_at': game.get('updatedAt')
                    }
<<<<<<< HEAD
                    print(f"Found odds for {home_abbr} vs {away_abbr}")
=======
>>>>>>> 756ae13 (API stats)
                    break

        return game_data

    def fetch_game_plays_api(self, season: int, season_type: str, week: str, game_id: str) -> List[Play]:
        """Fetch plays for a game using the API endpoint."""
        try:
            url = f"https://pro.nfl.com/api/secured/videos/filmroom/plays"
            params = {
                "season": season,
                "seasonType": season_type,
                "weekSlug": week,
                "gameId": game_id
            }
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            logger.info(f"Fetching plays for game {game_id} via API")
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response into Play objects
            if 'plays' in data:
                plays_response = PlaysResponse.model_validate(data)
                logger.info(f"Successfully fetched {plays_response.count} plays for game {game_id}")
                return plays_response.plays
            else:
                logger.warning(f"No plays found in API response for game {game_id}")
                return []
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"Authentication failed for plays API (401 Unauthorized).")
                logger.error(f"Please check that your BEARER_TOKEN in .env is valid and not expired.")
                logger.error(f"You may need to refresh your token from the NFL Pro website.")
            else:
                logger.error(f"HTTP error fetching plays for game {game_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching plays for game {game_id}: {e}")
            return []
    
    def scrape_game_plays(self, game_data: Game) -> List[Play]:
        """Fetch plays for a game, using API if available, otherwise fall back to web scraping."""
        game_id = game_data.game_info.id
        season = game_data.game_info.season
        season_type = game_data.game_info.season_type
        week = game_data.game_info.week
        
        # First try API endpoint if we have a bearer token
        if self.bearer_token:
            plays = self.fetch_game_plays_api(season, season_type, week, game_id)
            if plays:
                return plays
            logger.warning(f"Failed to fetch plays via API for game {game_id}, falling back to web scraping")
        
        # Fall back to web scraping if API fails or no bearer token
        if self.api_only:
            logger.warning(f"In API-only mode and play API failed for game {game_id}")
            return []
            
        try:
            game_url = self.generate_game_url(
                season=season,
                season_type=season_type,
                week=week,
                game_id=game_id
            )
            
            logger.info(f"Attempting to scrape plays from: {game_url}")
            self.driver.get(game_url)
            time.sleep(3)  # Wait for page load
            
            # TODO: Implement web scraping logic here
            # This would require analyzing the page structure
            logger.warning(f"Web scraping for plays not yet implemented for game {game_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error scraping plays for game {game_id}: {e}")
            return []

    def scrape_all_games(self, start_season: int = 2024, end_season: int = 2024) -> NFLData:
        """
        First fetch all game data from APIs, then scrape plays for each game.
        Returns a structured dictionary with full game information including plays.
        """
        # Only login if we're not in API-only mode and don't have a bearer token
        if not self.api_only and not self.bearer_token:
            if not self.login():
                print("Failed to login. Cannot proceed with scraping.")
                return NFLData(seasons={}, metadata={})

        # First get all game data from APIs
        print("Fetching game data from APIs...")
        all_data = self.fetch_all_api_data(start_season, end_season)
        
        # Now enhance the data with scraped plays
        print("\nStarting to scrape plays for each game...")
        
        for season in all_data.seasons:
            for season_type in all_data.seasons[season].types:
                for week in all_data.seasons[season].types[season_type].weeks:
                    week_data = all_data.seasons[season].types[season_type].weeks[week]
                    
                    for game in week_data.games:
                        try:
                            print(f"\nProcessing plays for: {game.teams.away.info.name} @ {game.teams.home.info.name}")
                            
                            # Fetch plays for this game
                            plays = self.fetch_game_plays_api(
                                season=game.game_info.season,
                                season_type=game.game_info.season_type,
                                week=game.game_info.week,
                                game_id=game.game_info.id
                            )
                            
                            # Add plays to game data
                            game.plays = plays
                            
                            # Save progress after each game
                            self.save_progress(all_data, prefix='full_game_data')
                            
                            # Small delay between games
                            time.sleep(2)
                            
                        except Exception as e:
                            print(f"Error processing game: {str(e)}")
                            continue
        
        # Save final complete dataset
        self.save_progress(all_data, prefix='full_game_data_complete')
        return all_data

<<<<<<< HEAD
    def save_progress(self, data: NFLData, prefix: str = None):
        """Save the current progress to database or JSON file."""
        if self.use_database and self.db_manager:
            # Save to database
            saved_count = 0
            for season in data.seasons.values():
                for season_type_data in season.types.values():
                    for week_data in season_type_data.weeks.values():
                        for game in week_data.games:
                            try:
                                self.db_manager.save_game(game)
                                saved_count += 1
                            except Exception as e:
                                logger.error(f"Error saving game {game.game_info.id} to database: {e}")
            logger.info(f"Saved {saved_count} games to database")
        else:
            # Fall back to JSON file storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Determine the appropriate prefix based on the mode
            if prefix is None:
                prefix = 'api_data' if self.api_only else 'nfl_game_map'
                
            # Create output directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Generate filename with timestamp
            output_file = os.path.join('data', f'{prefix}_{timestamp}.json')
            
            # Convert Pydantic model to JSON
            with open(output_file, 'w') as f:
                json.dump(data.model_dump(by_alias=True), f, indent=4)
            
            print(f"Progress saved to {output_file}")
=======
    def save_progress(self, data: Dict, prefix: str = None):
        """Save the current progress to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine the appropriate prefix based on the data type and mode
        if prefix is None:
            prefix = 'api_data' if self.api_only else 'nfl_game_map'
            
        # Create output directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Generate filename with timestamp
        output_file = os.path.join('data', f'{prefix}_{timestamp}.json')
        
        # Save the data with proper formatting
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"Progress saved to {output_file}")
>>>>>>> 756ae13 (API stats)

    def login(self):
        """Handle the NFL Pro login process."""
        try:
            # Navigate to the login page first
            self.driver.get("https://pro.nfl.com/film/plays")
            print("Navigated to main page")
            
            # Add explicit wait for page load
            time.sleep(5)  # Give the page time to fully load
            
            # Click the login button with more explicit wait and error handling
            try:
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#app > div.v-application--wrap > div:nth-child(1) > header > div > div.hidden-sm-and-down > div > div:nth-child(3) > div > button > span'))
                )
                print("Found login button")
                login_button.click()
                print("Clicked login button")
            except Exception as e:
                print(f"Failed to find or click login button: {str(e)}")
                return False

            # Enter email with explicit wait
            try:
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#email-input-field'))
                )
                email_field.clear()  # Clear any existing text
                email_field.send_keys(self.email)
                print("Entered email")
            except Exception as e:
                print(f"Failed to enter email: {str(e)}")
                return False

            # Click continue with explicit wait
            try:
                continue_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#__next > div > div > div > div > button.styles__StyledButton-sc-8qc5s2-0.eIevii'))
                )
                continue_button.click()
                print("Clicked continue")
            except Exception as e:
                print(f"Failed to click continue: {str(e)}")
                return False

            # Enter password with explicit wait
            try:
                password_field = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#password-input-field'))
                )
                password_field.clear()  # Clear any existing text
                password_field.send_keys(self.password)
                print("Entered password")
            except Exception as e:
                print(f"Failed to enter password: {str(e)}")
                return False

            # Click sign in with explicit wait
            try:
                sign_in_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#__next > div > div > div.styles__BodyWrapper-sc-1858ovt-1.dbHsLn > div > div.css-175oi2r.r-knv0ih.r-w7s2jr > button'))
                )
                sign_in_button.click()
                print("Clicked sign in")
            except Exception as e:
                print(f"Failed to click sign in: {str(e)}")
                return False

            # Wait for login to complete and page to load
            time.sleep(5)  # Increased wait time
            print("Login process completed")
            return True

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    def close(self):
        """Close the browser if it exists."""
        if not self.api_only and hasattr(self, 'driver'):
            self.driver.quit()

    def fetch_api_data(self, season: int, season_type: str, week: str, game_limit: Optional[int] = None) -> WeekData:
        """Fetch all API data for a specific week without web scraping."""
        try:
            logger.info(f"\nFetching API data for: Season {season} - {season_type} - {week}")
            
            # Fetch data from APIs
            live_scores = self.get_live_scores(season, season_type, week)
            odds_data = self.get_odds_data(season, season_type, week)
            
            # Process games data
            games = []
            if live_scores and 'games' in live_scores:
                total_games = len(live_scores['games'])
                games_to_process = live_scores['games'][:game_limit] if game_limit else live_scores['games']
                
                logger.info(f"Processing {len(games_to_process)} out of {total_games} games")
                
                for game in games_to_process:
                    try:
                        game_id = game.get('gameId')
                        if not game_id:
                            logger.warning(f"Skipping game without ID")
                            logger.warning(f"Skipping game without ID")
                            continue
                        
                        logger.info(f"Processing game {game_id}")
                        
                        logger.info(f"Processing game {game_id}")
                        
                        # Get detailed game metadata
                        game_metadata = self.get_game_metadata(game_id)
                        
                        # Get plays data
                        plays_data = self.get_plays_data(season, season_type, week, game_metadata.get('smartId'))
                        plays_list = plays_data.plays if plays_data else []
                        
                        # Get plays data
                        plays_data = self.get_plays_data(season, season_type, week, game_metadata.get('smartId'))
                        plays_list = plays_data.plays if plays_data else []
                        
                        # Find odds for this game
                        game_odds = None
                        if odds_data and 'games' in odds_data:
                            for odds in odds_data['games']:
                                # Match using team abbreviations
                                home_abbr = game_metadata.get('homeTeam', {}).get('abbr')
                                away_abbr = game_metadata.get('visitorTeam', {}).get('abbr')
                                if (odds.get('homeTeamAbbr') == home_abbr and 
                                    odds.get('visitorTeamAbbr') == away_abbr):
                                    game_odds = BettingOdds.model_validate(odds)
                                    logger.info(f"Found odds for {home_abbr} vs {away_abbr}")
                                    logger.info(f"Found odds for {home_abbr} vs {away_abbr}")
                                    break
                        
                        # Get metadata for teams
                        home_metadata = game_metadata.get('homeTeam', {}) if game_metadata else {}
                        away_metadata = game_metadata.get('visitorTeam', {}) if game_metadata else {}
                        
                        # Create team info objects
                        home_team = Team(
                            info=TeamInfo(
                                id=home_metadata.get('smartId'),
                                name=home_metadata.get('fullName'),
                                nickname=home_metadata.get('nick'),
                                logo=home_metadata.get('logo'),
                                abbreviation=home_metadata.get('abbr'),
                                location=TeamLocation(
                                    city_state=home_metadata.get('cityState'),
                                    conference=home_metadata.get('conferenceAbbr'),
                                    division=home_metadata.get('divisionAbbr')
                                )
                            ),
                            game_stats=TeamGameStats(
                                score=Score(**game.get('homeTeam', {}).get('score', {})),
                                timeouts=Timeouts(**game.get('homeTeam', {}).get('timeouts', {})),
                                possession=game.get('homeTeam', {}).get('hasPossession', False)
                            )
                        )
                        
                        away_team = Team(
                            info=TeamInfo(
                                id=away_metadata.get('smartId'),
                                name=away_metadata.get('fullName'),
                                nickname=away_metadata.get('nick'),
                                logo=away_metadata.get('logo'),
                                abbreviation=away_metadata.get('abbr'),
                                location=TeamLocation(
                                    city_state=away_metadata.get('cityState'),
                                    conference=away_metadata.get('conferenceAbbr'),
                                    division=away_metadata.get('divisionAbbr')
                                )
                            ),
                            game_stats=TeamGameStats(
                                score=Score(**game.get('awayTeam', {}).get('score', {})),
                                timeouts=Timeouts(**game.get('awayTeam', {}).get('timeouts', {})),
                                possession=game.get('awayTeam', {}).get('hasPossession', False)
                            )
                        )
                        
                        # Create game object with plays
                        # Create game object with plays
                        game_data = Game(
                            game_info=GameInfo(
                                id=game_id,
                                season=season,
                                season_type=season_type,
                                week=week,
                                status=game.get('phase'),
                                display_status=game.get('displayStatus'),
                                game_state=game.get('gameState'),
                                attendance=game.get('attendance'),
                                weather=game.get('weather'),
                                gamebook_url=game.get('gameBookUrl'),
                                date=game_metadata.get('gameDate'),
                                time=game_metadata.get('gameTimeEastern'),
                                network=game_metadata.get('networkChannel')
                            ),
                            venue=Venue.model_validate(game_metadata.get('site', {})) if game_metadata and 'site' in game_metadata else None,
                            broadcast=game.get('broadcastInfo', {}),
                            teams=Teams(home=home_team, away=away_team),
                            situation=GameSituation(
                                clock=game.get('clock'),
                                quarter=game.get('quarter'),
                                down=game.get('down'),
                                distance=game.get('distance'),
                                yard_line=game.get('yardLine'),
                                is_red_zone=game.get('isRedZone'),
                                is_goal_to_go=game.get('isGoalToGo')
                            ),
                            betting=game_odds,
                            metadata=game_metadata,
                            plays=plays_list  # Add plays to the game data
                            metadata=game_metadata,
                            plays=plays_list  # Add plays to the game data
                        )
                        
                        games.append(game_data)
                        logger.info(f"Successfully processed game {game_id}")
                        logger.info(f"Successfully processed game {game_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing game: {str(e)}")
                        logger.error(f"Error processing game: {str(e)}")
                        continue
            
            # Create week data
            week_data = WeekData(
                metadata={
=======
                for game in live_scores['games']:
                    game_id = game['gameId']
                    
                    # Get detailed game metadata
                    game_metadata = self.get_game_metadata(game_id)
                    
                    # Find odds for this game
                    game_odds = None
                    if odds_data and 'games' in odds_data:
                        for odds in odds_data['games']:
                            if (odds.get('homeTeamId') == game['homeTeam']['teamId'] and 
                                odds.get('visitorTeamId') == game['awayTeam']['teamId']):
                                game_odds = odds
                                break
                    
                    game_data = {
                        'game_info': {
                            'id': game_id,
                            'season': season,
                            'season_type': season_type,
                            'week': week,
                            'status': game['phase'],
                            'display_status': game['displayStatus'],
                            'game_state': game['gameState'],
                            'attendance': game.get('attendance'),
                            'weather': game.get('weather'),
                            'gamebook_url': game.get('gameBookUrl'),
                            'date': game.get('date'),
                            'time': game.get('time')
                        },
                        'venue': game.get('venue', {}),
                        'broadcast': game.get('broadcastInfo', {}),
                        'teams': {
                            'home': {
                                'info': {
                                    'id': game['homeTeam']['teamId'],
                                    'name': game['homeTeam']['fullName'],
                                    'logo': game['homeTeam']['currentLogo'],
                                    'abbreviation': game['homeTeam'].get('abbreviation')
                                },
                                'game_stats': {
                                    'score': game['homeTeam']['score'],
                                    'timeouts': game['homeTeam']['timeouts'],
                                    'possession': game['homeTeam'].get('hasPossession', False)
                                }
                            },
                            'away': {
                                'info': {
                                    'id': game['awayTeam']['teamId'],
                                    'name': game['awayTeam']['fullName'],
                                    'logo': game['awayTeam']['currentLogo'],
                                    'abbreviation': game['awayTeam'].get('abbreviation')
                                },
                                'game_stats': {
                                    'score': game['awayTeam']['score'],
                                    'timeouts': game['awayTeam']['timeouts'],
                                    'possession': game['awayTeam'].get('hasPossession', False)
                                }
                            }
                        },
                        'situation': {
                            'clock': game.get('clock'),
                            'quarter': game.get('quarter'),
                            'down': game.get('down'),
                            'distance': game.get('distance'),
                            'yard_line': game.get('yardLine'),
                            'is_red_zone': game.get('isRedZone'),
                            'is_goal_to_go': game.get('isGoalToGo')
                        },
                        'betting': {
                            'odds': game_odds,
                            'updated_at': game_odds.get('updatedAt') if game_odds else None
                        }
                    }
                    
                    # Add metadata from game-specific API if available
                    if game_metadata:
                        game_data['metadata'] = game_metadata
                    
                    games.append(game_data)
            
            # Create a structured response
            api_data = {
                'metadata': {
>>>>>>> 756ae13 (API stats)
                    'season': season,
                    'season_type': season_type,
                    'week': week,
                    'timestamp': datetime.now().isoformat()
                },
<<<<<<< HEAD
                games=games
            )
            
            return week_data
            
        except Exception as e:
            logger.error(f"Error fetching API data: {str(e)}")
            logger.error(f"Error fetching API data: {str(e)}")
            return WeekData(metadata={}, games=[])

    def scrape_single_game(self, game_id: str, season: int = 2024, season_type: str = 'REG', week: str = 'WEEK_1') -> Optional[Game]:
        """Scrape data for a single game by its ID."""
        try:
            logger.info(f"Scraping single game: {game_id}")
            
            # Get game metadata
            game_metadata = self.get_game_metadata(game_id)
            if not game_metadata:
                logger.error(f"Failed to fetch metadata for game {game_id}")
                return None
            
            # Extract season info from metadata if available
            if 'season' in game_metadata:
                season = game_metadata['season']
            if 'seasonType' in game_metadata:
                season_type = game_metadata['seasonType']
            if 'week' in game_metadata:
                week = game_metadata['week']
                # Convert week number to WEEK_X format if needed
                if season_type == 'REG' and isinstance(week, int):
                    week = f'WEEK_{week}'
            
            logger.info(f"Game details: Season {season}, Type {season_type}, Week {week}")
            
            # Get plays data
            smart_id = game_metadata.get('smartId', game_id)
            logger.info(f"Using game ID for plays: {smart_id} (original: {game_id})")
            plays_data = self.get_plays_data(season, season_type, week, smart_id)
            plays_list = plays_data.plays if plays_data else []
            
            # Get additional data
            live_scores = self.get_live_scores(season, season_type, week)
            odds_data = self.get_odds_data(season, season_type, week)
            
            # Find this specific game in live scores
            game_live_data = None
            if live_scores and 'games' in live_scores:
                for game in live_scores['games']:
                    if game.get('gameId') == game_id:
                        game_live_data = game
                        break
            
            # Find odds for this game
            game_odds = None
            if odds_data and 'games' in odds_data:
                home_abbr = game_metadata.get('homeTeam', {}).get('abbr')
                away_abbr = game_metadata.get('visitorTeam', {}).get('abbr')
                for odds in odds_data['games']:
                    if (odds.get('homeTeamAbbr') == home_abbr and 
                        odds.get('visitorTeamAbbr') == away_abbr):
                        game_odds = BettingOdds.model_validate(odds)
                        break
            
            # Create team objects
            home_metadata = game_metadata.get('homeTeam', {})
            away_metadata = game_metadata.get('visitorTeam', {})
            
            home_team = Team(
                info=TeamInfo(
                    id=home_metadata.get('smartId'),
                    name=home_metadata.get('fullName'),
                    nickname=home_metadata.get('nick'),
                    logo=home_metadata.get('logo'),
                    abbreviation=home_metadata.get('abbr'),
                    location=TeamLocation(
                        city_state=home_metadata.get('cityState'),
                        conference=home_metadata.get('conferenceAbbr'),
                        division=home_metadata.get('divisionAbbr')
                    )
                ),
                game_stats=TeamGameStats(
                    score=Score(**game_live_data.get('homeTeam', {}).get('score', {})) if game_live_data else Score(),
                    timeouts=Timeouts(**game_live_data.get('homeTeam', {}).get('timeouts', {})) if game_live_data else Timeouts(),
                    possession=game_live_data.get('homeTeam', {}).get('hasPossession', False) if game_live_data else False
                )
            )
            
            away_team = Team(
                info=TeamInfo(
                    id=away_metadata.get('smartId'),
                    name=away_metadata.get('fullName'),
                    nickname=away_metadata.get('nick'),
                    logo=away_metadata.get('logo'),
                    abbreviation=away_metadata.get('abbr'),
                    location=TeamLocation(
                        city_state=away_metadata.get('cityState'),
                        conference=away_metadata.get('conferenceAbbr'),
                        division=away_metadata.get('divisionAbbr')
                    )
                ),
                game_stats=TeamGameStats(
                    score=Score(**game_live_data.get('awayTeam', {}).get('score', {})) if game_live_data else Score(),
                    timeouts=Timeouts(**game_live_data.get('awayTeam', {}).get('timeouts', {})) if game_live_data else Timeouts(),
                    possession=game_live_data.get('awayTeam', {}).get('hasPossession', False) if game_live_data else False
                )
            )
            
            # Create game object
            game_data = Game(
                game_info=GameInfo(
                    id=game_id,
                    season=season,
                    season_type=season_type,
                    week=week,
                    status=game_live_data.get('phase') if game_live_data else None,
                    display_status=game_live_data.get('displayStatus') if game_live_data else None,
                    game_state=game_live_data.get('gameState') if game_live_data else None,
                    attendance=game_live_data.get('attendance') if game_live_data else None,
                    weather=game_live_data.get('weather') if game_live_data else None,
                    gamebook_url=game_live_data.get('gameBookUrl') if game_live_data else None,
                    date=game_metadata.get('gameDate'),
                    time=game_metadata.get('gameTimeEastern'),
                    network=game_metadata.get('networkChannel')
                ),
                venue=Venue.model_validate(game_metadata.get('site', {})) if 'site' in game_metadata else None,
                broadcast=game_live_data.get('broadcastInfo', {}) if game_live_data else {},
                teams=Teams(home=home_team, away=away_team),
                situation=GameSituation(
                    clock=game_live_data.get('clock') if game_live_data else None,
                    quarter=game_live_data.get('quarter') if game_live_data else None,
                    down=game_live_data.get('down') if game_live_data else None,
                    distance=game_live_data.get('distance') if game_live_data else None,
                    yard_line=game_live_data.get('yardLine') if game_live_data else None,
                    is_red_zone=game_live_data.get('isRedZone') if game_live_data else None,
                    is_goal_to_go=game_live_data.get('isGoalToGo') if game_live_data else None
                ),
                betting=game_odds,
                metadata=game_metadata,
                plays=plays_list
            )
            
            logger.info(f"Successfully scraped game {game_id} with {len(plays_list)} plays")
            return game_data
            
        except Exception as e:
            logger.error(f"Error scraping single game {game_id}: {str(e)}")
            return None

    def fetch_all_api_data(self, start_season: int = 2024, end_season: int = 2024, game_limit: Optional[int] = None) -> NFLData:
        """Fetch API data for all weeks and seasons within the specified range."""
        all_data = NFLData(
            seasons={},
            metadata={
                'last_updated': datetime.now().isoformat(),
                'start_season': start_season,
                'end_season': end_season,
                'data_type': 'api_only',
                'game_limit': game_limit
                'data_type': 'api_only',
                'game_limit': game_limit
            }
        )
        
        for season in range(start_season, end_season + 1):
            season_data = SeasonData(types={})
            
            for season_type in self.season_types:
                season_type_data = SeasonTypeData(weeks={})
                
                for week in self.weeks[season_type]:
                    try:
                        logger.info(f"\nProcessing: Season {season} - {season_type} - {week}")
                        week_data = self.fetch_api_data(season, season_type, week, game_limit)
                        logger.info(f"\nProcessing: Season {season} - {season_type} - {week}")
                        week_data = self.fetch_api_data(season, season_type, week, game_limit)
                        if week_data and week_data.games:
                            season_type_data.weeks[week] = week_data
                            
                            # Save progress after each week
                            all_data.seasons[season] = season_data
=======
                'games': games
            }
            
            return api_data
            
        except Exception as e:
            print(f"Error fetching API data: {str(e)}")
            return {}

    def fetch_all_api_data(self, start_season: int = 2024, end_season: int = 2024) -> Dict:
        """Fetch API data for all weeks and seasons within the specified range."""
        all_data = {
            'seasons': {},
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'start_season': start_season,
                'end_season': end_season,
                'data_type': 'api_only'
            }
        }
        
        for season in range(start_season, end_season + 1):
            all_data['seasons'][season] = {'types': {}}
            
            for season_type in self.season_types:
                all_data['seasons'][season]['types'][season_type] = {'weeks': {}}
                
                for week in self.weeks[season_type]:
                    try:
                        print(f"\nProcessing: Season {season} - {season_type} - {week}")
                        week_data = self.fetch_api_data(season, season_type, week)
                        if week_data:
                            all_data['seasons'][season]['types'][season_type]['weeks'][week] = week_data
                            
                            # Save progress after each week
>>>>>>> 756ae13 (API stats)
                            self.save_progress(all_data)
                            
                            # Small delay between requests
                            time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error fetching data for {season} {season_type} {week}: {str(e)}")
                        continue
                
                season_data.types[season_type] = season_type_data
            
            all_data.seasons[season] = season_data
=======
                        print(f"Error fetching data for {season} {season_type} {week}: {str(e)}")
                        continue
>>>>>>> 756ae13 (API stats)
        
        # Save final complete dataset
        self.save_progress(all_data, prefix='api_data_complete')
        return all_data

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from environment variables
    email = os.getenv('NFL_EMAIL')
    password = os.getenv('NFL_PASSWORD')
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='NFL Pro Game Data Scraper')
    parser.add_argument('--api-only', action='store_true', help='Only fetch API data without web scraping')
    parser.add_argument('--start-season', type=int, default=2024, help='Start season year')
    parser.add_argument('--end-season', type=int, default=2024, help='End season year')
    parser.add_argument('--resume-from', type=str, help='Resume from a previous JSON file')
<<<<<<< HEAD
    parser.add_argument('--week', type=str, help='Specific week to scrape (e.g., "WEEK_1" for regular season or "1" for postseason)')
    parser.add_argument('--season-type', type=str, choices=['REG', 'POST'], default='REG', help='Season type (REG or POST)')
    parser.add_argument('--test-data', type=str, help='Use test data from specified JSON file instead of making API calls')
    parser.add_argument('--game-limit', type=int, help='Limit the number of games to scrape per week')
    parser.add_argument('--no-database', action='store_true', help='Disable database storage and use JSON files only')
    parser.add_argument('--db-path', type=str, default='nfl_data.db', help='Path to SQLite database file')
    parser.add_argument('--game-id', type=str, help='Scrape a specific game by its ID')
    parser.add_argument('--skip-play-summaries', action='store_true', help='Skip fetching detailed play summaries')
    args = parser.parse_args()
    
    if not args.api_only and (not email or not password):
        logger.error("Please ensure NFL_EMAIL and NFL_PASSWORD are set in your .env file")
        logger.error("Please ensure NFL_EMAIL and NFL_PASSWORD are set in your .env file")
        return
    
    scraper = NFLGameScraper(
        email=email, 
        password=password, 
        api_only=args.api_only,
        use_database=not args.no_database,
        db_path=args.db_path,
        skip_play_summaries=args.skip_play_summaries
        db_path=args.db_path,
        skip_play_summaries=args.skip_play_summaries
    )
    
    try:
        if args.test_data:
            # Load and validate test data
            try:
                with open(args.test_data, 'r') as f:
                    test_data = json.load(f)
                    all_data = NFLData.model_validate(test_data)
                logger.info(f"Successfully loaded test data from {args.test_data}")
                
                # Save the validated data
                scraper.save_progress(all_data, prefix='test_data_validated')
                return
            except Exception as e:
                logger.error(f"Error loading test data: {str(e)}")
                return
        
        if args.game_id:
            # Scrape a single game by ID
            logger.info(f"Scraping single game: {args.game_id}")
            game_data = scraper.scrape_single_game(args.game_id)
            
            if game_data:
                # Save the game data
                if scraper.use_database and scraper.db_manager:
                    scraper.db_manager.save_game(game_data)
                    logger.info(f"Saved game {args.game_id} to database")
                else:
                    # Save as JSON
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    os.makedirs('data', exist_ok=True)
                    output_file = os.path.join('data', f'game_{args.game_id}_{timestamp}.json')
                    
                    with open(output_file, 'w') as f:
                        json.dump(game_data.model_dump(by_alias=True), f, indent=4)
                    
                    logger.info(f"Saved game data to {output_file}")
            else:
                logger.error(f"Failed to scrape game {args.game_id}")
            return
        
        if args.week:
            # Run for specific week only
            if args.api_only:
                week_data = scraper.fetch_api_data(
                    season=args.start_season,
                    season_type=args.season_type,
                    week=args.week,
                    game_limit=args.game_limit
                    week=args.week,
                    game_limit=args.game_limit
                )
                
                # Create a full NFLData structure using Pydantic models
                all_data = NFLData(
                    seasons={
                        args.start_season: SeasonData(
                            types={
                                args.season_type: SeasonTypeData(
                                    weeks={
                                        args.week: week_data
                                    }
                                )
                            }
                        )
                    },
                    metadata={
                        'last_updated': datetime.now().isoformat(),
                        'start_season': args.start_season,
                        'end_season': args.start_season,
                        'data_type': 'api_only_single_week',
                        'game_limit': args.game_limit
                        'data_type': 'api_only_single_week',
                        'game_limit': args.game_limit
                    }
                )
                
                scraper.save_progress(all_data, prefix='api_data_single_week')
                logger.info(f"Completed fetching API data for {args.season_type} {args.week}")
                logger.info(f"Completed fetching API data for {args.season_type} {args.week}")
            else:
                # TODO: Implement single week scraping with plays
                logger.warning("Single week scraping with plays not yet implemented")
                logger.warning("Single week scraping with plays not yet implemented")
        elif args.resume_from:
            # Load previous data and continue scraping
            with open(args.resume_from, 'r') as f:
                data = json.load(f)
                # Convert loaded JSON back to Pydantic model
                all_data = NFLData.model_validate(data)
            logger.info(f"Resuming from {args.resume_from}")
        elif args.api_only:
            # Fetch only API data
            all_data = scraper.fetch_all_api_data(
                start_season=args.start_season, 
                end_season=args.end_season,
                game_limit=args.game_limit
            )
            logger.info(f"Completed fetching API data")
        else:
            # Get API data and scrape plays
            all_data = scraper.scrape_all_games(start_season=args.start_season, end_season=args.end_season)
            logger.info(f"Completed creating full game data")
        
    finally:
        scraper.close()
>>>>>>> 756ae13 (API stats)

if __name__ == "__main__":
    main()
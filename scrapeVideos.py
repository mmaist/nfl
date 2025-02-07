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
from models import (
    NFLData, SeasonData, SeasonTypeData, WeekData, Game, GameInfo,
    Teams, Team, TeamInfo, TeamLocation, TeamGameStats,
    GameSituation, Venue, BettingOdds, Score, Timeouts
)

class NFLGameScraper:
    def __init__(self, email=None, password=None, api_only=False):
        # Store credentials
        self.email = email
        self.password = password
        self.api_only = api_only
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retries = Retry(total=5,
                       backoff_factor=0.1,
                       status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

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
            'POST': ['1', '2', '3', '4']  # Playoff weeks
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
            print(url)
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            print(f"Successfully fetched odds data for {season} {season_type} Week {week_num}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching odds data: {str(e)}")
            return None

    def enrich_game_data(self, game_data: Dict, standings_data: Dict, live_scores: Dict, odds_data: Dict) -> Dict:
        """Enrich game data with standings, live scores, and odds information."""
        game_id = game_data['game_info']['id']
        
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
                # Match using team abbreviations
                home_abbr = game_data['home_team'].get('abbreviation')
                away_abbr = game_data['away_team'].get('abbreviation')
                if (game.get('homeTeamAbbr') == home_abbr and 
                    game.get('visitorTeamAbbr') == away_abbr):
                    game_odds = {
                        'moneyline': game.get('moneyline', {}),
                        'spread': game.get('spread', {}),
                        'totals': game.get('totals', {}),
                        'updated_at': game.get('updatedAt')
                    }
                    print(f"Found odds for {home_abbr} vs {away_abbr}")
                    break

        return game_data

    def scrape_game_plays(self, game_data: Dict) -> List[Dict]:
        """Scrape all plays from a specific game using the game data from API."""
        try:
            game_url = self.generate_game_url(
                season=game_data['game_info']['season'],
                season_type=game_data['game_info']['season_type'],
                week=game_data['game_info']['week'],
                game_id=game_data['game_info']['id']
            )
            
            print(f"\nScraping plays from: {game_url}")
            self.driver.get(game_url)
            time.sleep(3)  # Wait for page load
            
            # TODO: Implement play scraping logic here
            # This will be implemented once we analyze the play page structure
            plays = []
            
            return plays
            
        except Exception as e:
            print(f"Error scraping plays for game {game_data['game_info']['id']}: {str(e)}")
            return []

    def scrape_all_games(self, start_season: int = 2024, end_season: int = 2024) -> Dict:
        """
        First fetch all game data from APIs, then scrape plays for each game.
        Returns a structured dictionary with full game information including plays.
        """
        if not self.login():
            print("Failed to login. Cannot proceed with scraping.")
            return {}

        # First get all game data from APIs
        print("Fetching game data from APIs...")
        all_data = self.fetch_all_api_data(start_season, end_season)
        
        # Now enhance the data with scraped plays
        print("\nStarting to scrape plays for each game...")
        
        for season in all_data['seasons']:
            for season_type in all_data['seasons'][season]['types']:
                for week in all_data['seasons'][season]['types'][season_type]['weeks']:
                    week_data = all_data['seasons'][season]['types'][season_type]['weeks'][week]
                    
                    for game in week_data['games']:
                        try:
                            print(f"\nProcessing plays for: {game['teams']['away']['team']['info']['name']} @ {game['teams']['home']['team']['info']['name']}")
                            
                            # Scrape plays for this game
                            plays = self.scrape_game_plays(game)
                            
                            # Add plays to game data
                            game['plays'] = plays
                            
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

    def save_progress(self, data: NFLData, prefix: str = None):
        """Save the current progress to a JSON file."""
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

    def fetch_api_data(self, season: int = 2024, season_type: str = 'REG', week: str = 'WEEK_1') -> WeekData:
        """Fetch all API data for a specific week without web scraping."""
        try:
            print(f"\nFetching API data for: Season {season} - {season_type} - {week}")
            
            # Fetch data from APIs
            live_scores = self.get_live_scores(season, season_type, week)
            odds_data = self.get_odds_data(season, season_type, week)
            
            # Process games data
            games = []
            if live_scores and 'games' in live_scores:
                for game in live_scores['games']:
                    try:
                        game_id = game.get('gameId')
                        if not game_id:
                            print(f"Skipping game without ID")
                            continue
                        
                        # Get detailed game metadata
                        game_metadata = self.get_game_metadata(game_id)
                        
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
                                    print(f"Found odds for {home_abbr} vs {away_abbr}")
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
                        
                        # Create game object
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
                            metadata=game_metadata
                        )
                        
                        games.append(game_data)
                        
                    except Exception as e:
                        print(f"Error processing game: {str(e)}")
                        continue
            
            # Create week data
            week_data = WeekData(
                metadata={
                    'season': season,
                    'season_type': season_type,
                    'week': week,
                    'timestamp': datetime.now().isoformat()
                },
                games=games
            )
            
            return week_data
            
        except Exception as e:
            print(f"Error fetching API data: {str(e)}")
            return WeekData(metadata={}, games=[])

    def fetch_all_api_data(self, start_season: int = 2024, end_season: int = 2024) -> NFLData:
        """Fetch API data for all weeks and seasons within the specified range."""
        all_data = NFLData(
            seasons={},
            metadata={
                'last_updated': datetime.now().isoformat(),
                'start_season': start_season,
                'end_season': end_season,
                'data_type': 'api_only'
            }
        )
        
        for season in range(start_season, end_season + 1):
            season_data = SeasonData(types={})
            
            for season_type in self.season_types:
                season_type_data = SeasonTypeData(weeks={})
                
                for week in self.weeks[season_type]:
                    try:
                        print(f"\nProcessing: Season {season} - {season_type} - {week}")
                        week_data = self.fetch_api_data(season, season_type, week)
                        if week_data and week_data.games:
                            season_type_data.weeks[week] = week_data
                            
                            # Save progress after each week
                            all_data.seasons[season] = season_data
                            self.save_progress(all_data)
                            
                            # Small delay between requests
                            time.sleep(2)
                    except Exception as e:
                        print(f"Error fetching data for {season} {season_type} {week}: {str(e)}")
                        continue
                
                season_data.types[season_type] = season_type_data
            
            all_data.seasons[season] = season_data
        
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
    parser.add_argument('--week', type=str, help='Specific week to scrape (e.g., "WEEK_1" for regular season or "1" for postseason)')
    parser.add_argument('--season-type', type=str, choices=['REG', 'POST'], default='REG', help='Season type (REG or POST)')
    args = parser.parse_args()
    
    if not args.api_only and (not email or not password):
        print("Please ensure NFL_EMAIL and NFL_PASSWORD are set in your .env file")
        return
    
    scraper = NFLGameScraper(email=email, password=password, api_only=args.api_only)
    
    try:
        if args.week:
            # Run for specific week only
            if args.api_only:
                week_data = scraper.fetch_api_data(
                    season=args.start_season,
                    season_type=args.season_type,
                    week=args.week
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
                        'data_type': 'api_only_single_week'
                    }
                )
                
                scraper.save_progress(all_data, prefix='api_data_single_week')
                print(f"Completed fetching API data for {args.season_type} {args.week}")
            else:
                # TODO: Implement single week scraping with plays
                print("Single week scraping with plays not yet implemented")
        elif args.resume_from:
            # Load previous data and continue scraping
            with open(args.resume_from, 'r') as f:
                data = json.load(f)
                # Convert loaded JSON back to Pydantic model
                all_data = NFLData.model_validate(data)
            print(f"Resuming from {args.resume_from}")
        elif args.api_only:
            # Fetch only API data
            all_data = scraper.fetch_all_api_data(start_season=args.start_season, end_season=args.end_season)
            print(f"Completed fetching API data")
        else:
            # Get API data and scrape plays
            all_data = scraper.scrape_all_games(start_season=args.start_season, end_season=args.end_season)
            print(f"Completed creating full game data")
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
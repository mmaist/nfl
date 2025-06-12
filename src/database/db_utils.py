from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .database import db, DBGame, DBPlay, DBPlayStat, DBPlayer
from ..models.models import Game, Play, PlayStat, Player, PlaySummary
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class NFLDatabaseManager:
    def __init__(self, db_path: str = "nfl_data.db"):
        self.db = db
        self.db.db_path = db_path
        self.db.connect()
        
    def save_game(self, game: Game, session: Optional[Session] = None) -> DBGame:
        """Save a game and its plays to the database"""
        if not session:
            session = self.db.get_session()
            close_session = True
        else:
            close_session = False
            
        try:
            # Check if game already exists
            db_game = session.query(DBGame).filter_by(id=game.game_info.id).first()
            
            if not db_game:
                db_game = DBGame(id=game.game_info.id)
                session.add(db_game)
            
            # Update game info
            db_game.season = game.game_info.season
            db_game.season_type = game.game_info.season_type
            db_game.week = game.game_info.week
            db_game.status = game.game_info.status
            db_game.display_status = game.game_info.display_status
            db_game.game_state = game.game_info.game_state
            db_game.attendance = game.game_info.attendance
            db_game.weather = game.game_info.weather
            
            # Parse weather data if available
            if game.game_info.weather:
                weather_data = self._parse_weather(game.game_info.weather)
                db_game.weather_temperature = weather_data.get('temperature')
                db_game.weather_wind_speed = weather_data.get('wind_speed')
                db_game.weather_wind_direction = weather_data.get('wind_direction')
                db_game.weather_precipitation = weather_data.get('precipitation')
                db_game.weather_humidity = weather_data.get('humidity')
                db_game.weather_conditions = weather_data.get('conditions')
            db_game.gamebook_url = game.game_info.gamebook_url
            db_game.date = game.game_info.date
            db_game.time = game.game_info.time
            db_game.network = game.game_info.network
            
            # Update venue info
            if game.venue:
                db_game.venue_smart_id = game.venue.smart_id
                db_game.venue_site_id = game.venue.site_id
                db_game.venue_site_full_name = game.venue.site_full_name
                db_game.venue_site_city = game.venue.site_city
                db_game.venue_site_state = game.venue.site_state
                db_game.venue_postal_code = game.venue.postal_code
                db_game.venue_roof_type = game.venue.roof_type
            
            # Update team info
            db_game.home_team_id = game.teams.home.info.id
            db_game.home_team_name = game.teams.home.info.name
            db_game.home_team_nickname = game.teams.home.info.nickname
            db_game.home_team_abbreviation = game.teams.home.info.abbreviation
            db_game.away_team_id = game.teams.away.info.id
            db_game.away_team_name = game.teams.away.info.name
            db_game.away_team_nickname = game.teams.away.info.nickname
            db_game.away_team_abbreviation = game.teams.away.info.abbreviation
            
            # Update scores
            db_game.home_score_q1 = game.teams.home.game_stats.score.q1
            db_game.home_score_q2 = game.teams.home.game_stats.score.q2
            db_game.home_score_q3 = game.teams.home.game_stats.score.q3
            db_game.home_score_q4 = game.teams.home.game_stats.score.q4
            db_game.home_score_ot = game.teams.home.game_stats.score.ot
            db_game.home_score_total = game.teams.home.game_stats.score.total
            db_game.away_score_q1 = game.teams.away.game_stats.score.q1
            db_game.away_score_q2 = game.teams.away.game_stats.score.q2
            db_game.away_score_q3 = game.teams.away.game_stats.score.q3
            db_game.away_score_q4 = game.teams.away.game_stats.score.q4
            db_game.away_score_ot = game.teams.away.game_stats.score.ot
            db_game.away_score_total = game.teams.away.game_stats.score.total
            
            # Update situation
            db_game.clock = game.situation.clock
            db_game.quarter = game.situation.quarter
            db_game.down = game.situation.down
            db_game.distance = game.situation.distance
            db_game.yard_line = game.situation.yard_line
            db_game.is_red_zone = game.situation.is_red_zone
            db_game.is_goal_to_go = game.situation.is_goal_to_go
            
            # Update betting odds
            if game.betting:
                if game.betting.moneyline:
                    db_game.moneyline_home_price = game.betting.moneyline.home_price
                    db_game.moneyline_away_price = game.betting.moneyline.away_price
                if game.betting.spread:
                    db_game.spread_home_handicap = game.betting.spread.home_handicap
                    db_game.spread_away_handicap = game.betting.spread.away_handicap
                    db_game.spread_home_price = game.betting.spread.home_price
                    db_game.spread_away_price = game.betting.spread.away_price
                if game.betting.totals:
                    db_game.totals_under_handicap = game.betting.totals.under_handicap
                    db_game.totals_over_handicap = game.betting.totals.over_handicap
                    db_game.totals_over_price = game.betting.totals.over_price
                    db_game.totals_under_price = game.betting.totals.under_price
                db_game.betting_updated_at = game.betting.updated_at
            
            # Update metadata
            db_game.metadata_json = game.metadata
            
            # Extract team stats from metadata if available
            if game.metadata and 'standings' in game.metadata:
                self._update_team_stats(db_game, game.metadata['standings'])
            
            # Calculate historical team statistics
            if game.game_info.date and game.teams.home.info.id and game.teams.away.info.id:
                try:
                    historical_stats = self._calculate_historical_team_stats(
                        game.game_info.date,
                        game.teams.home.info.id,
                        game.teams.away.info.id,
                        game.game_info.season,
                        session
                    )
                    
                    # Update historical stats in database
                    for stat_name, stat_value in historical_stats.items():
                        if hasattr(db_game, stat_name) and stat_value is not None:
                            setattr(db_game, stat_name, stat_value)
                            
                except Exception as e:
                    logger.warning(f"Failed to calculate historical team stats: {e}")
                    # Continue without historical stats rather than failing completely
            
            # Save plays
            if game.plays:
                self._save_plays(db_game, game.plays, session, game.game_info)
            
            session.commit()
            logger.info(f"Saved game {game.game_info.id} with {len(game.plays)} plays")
            
            return db_game
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving game {game.game_info.id}: {e}")
            raise
        finally:
            if close_session:
                session.close()
                
    def _save_plays(self, db_game: DBGame, plays: List[Play], session: Session, game_info=None):
        """Save plays for a game"""
        # Remove existing plays for this game
        session.query(DBPlay).filter_by(game_id=db_game.id).delete()
        
        # Collect all unique players from all plays first
        all_players = {}
        for play in plays:
            if play.summary:
                players = (play.summary.home or []) + (play.summary.away or [])
                for player in players:
                    # Use nfl_id as the unique key
                    all_players[player.nfl_id] = player
        
        # Save all unique players once
        if all_players:
            self._save_players(list(all_players.values()), session)
        
        # Now save the plays
        for play_index, play in enumerate(plays):
            db_play = DBPlay(
                game_id=db_game.id,
                play_id=play.play_id,
                sequence=play.sequence,
                quarter=play.quarter,
                down=play.down,
                yards_to_go=play.yards_to_go,
                yardline=play.yardline,
                game_clock=play.game_clock,
                play_type=play.play_type,
                play_description=play.play_description,
                possession_team_id=play.possession_team_id,
                defense_team_id=play.defense_team_id
            )
            
            # Add summary data if available
            if play.summary and play.summary.play:
                play_details = play.summary.play
                db_play.pre_snap_home_score = play_details.pre_snap_home_score
                db_play.pre_snap_visitor_score = play_details.pre_snap_visitor_score
                db_play.home_score = play_details.home_score
                db_play.visitor_score = play_details.visitor_score
                db_play.is_big_play = play_details.is_big_play
                db_play.is_end_quarter = play_details.is_end_quarter
                db_play.is_goal_to_go = play_details.is_goal_to_go
                db_play.is_no_play = play_details.is_no_play
                db_play.is_penalty = play_details.is_penalty
                db_play.is_scoring = play_details.is_scoring
                db_play.is_st_play = play_details.is_st_play
                db_play.is_change_of_possession = play_details.is_change_of_possession
                db_play.is_redzone_play = play_details.is_redzone_play
                db_play.expected_points = play_details.expected_points
                db_play.expected_points_added = play_details.expected_points_added
                db_play.pre_snap_home_team_win_probability = play_details.pre_snap_home_team_win_probability
                db_play.pre_snap_visitor_team_win_probability = play_details.pre_snap_visitor_team_win_probability
                db_play.post_play_home_team_win_probability = play_details.post_play_home_team_win_probability
                db_play.post_play_visitor_team_win_probability = play_details.post_play_visitor_team_win_probability
                db_play.home_timeouts_left = play_details.home_timeouts_left
                db_play.visitor_timeouts_left = play_details.visitor_timeouts_left
                db_play.play_state = play_details.play_state
                db_play.play_type_code = play_details.play_type_code
                db_play.yardline_number = play_details.yardline_number
                db_play.yardline_side = play_details.yardline_side
                db_play.absolute_yardline_number = play_details.absolute_yardline_number
                db_play.play_direction = play_details.play_direction
                db_play.time_of_day_utc = play_details.time_of_day_utc
                
                # Extract play details from description
                play_info = self._extract_play_details(play_details.play_description)
                db_play.offensive_formation = play_info.get('offensive_formation')
                db_play.yards_gained = play_info.get('yards_gained')
                db_play.pass_length = play_info.get('pass_length')
                db_play.pass_location = play_info.get('pass_location')
                db_play.run_direction = play_info.get('run_direction')
                
                # Analyze defensive personnel if available
                if play.summary:
                    # Determine which team is on defense
                    if play.summary.home_is_offense:
                        # Away team is on defense
                        defensive_players = play.summary.away or []
                    else:
                        # Home team is on defense
                        defensive_players = play.summary.home or []
                    
                    # Convert Player objects to dicts if needed
                    defensive_players_dict = []
                    for player in defensive_players:
                        if hasattr(player, 'dict'):
                            defensive_players_dict.append(player.dict())
                        else:
                            defensive_players_dict.append(player)
                    
                    # Analyze defensive formation and package
                    defensive_info = self._analyze_defensive_personnel(defensive_players_dict)
                    db_play.defensive_formation = defensive_info.get('defensive_formation')
                    db_play.defensive_package = defensive_info.get('defensive_package')
                    db_play.defensive_db_count = defensive_info.get('db_count')
                    db_play.defensive_lb_count = defensive_info.get('lb_count')
                    db_play.defensive_dl_count = defensive_info.get('dl_count')
                    db_play.defensive_box_count = defensive_info.get('box_count')
                
                # Calculate game context features
                db_play.score_differential = play_details.home_score - play_details.visitor_score
                
                # Calculate time remaining
                time_context = self._calculate_time_remaining(play_details.quarter, play_details.game_clock)
                db_play.time_remaining_half = time_context['time_remaining_half']
                db_play.time_remaining_game = time_context['time_remaining_game']
                db_play.is_two_minute_drill = time_context['is_two_minute_drill']
                
                # Check if must-score situation (trailing by 8+ in 4th quarter with < 5 minutes)
                if play_details.quarter == 4 and time_context['time_remaining_game'] < 300:
                    if play.possession_team_id == play.home_team_id:
                        score_diff = play_details.home_score - play_details.visitor_score
                    else:
                        score_diff = play_details.visitor_score - play_details.home_score
                    db_play.is_must_score_situation = score_diff <= -8
                
                # Extract play result metrics
                play_result = self._extract_play_result_metrics(
                    play_details.play_description,
                    play_details.play_type
                )
                
                # Pass play details
                db_play.is_complete_pass = play_result.get('is_complete_pass')
                db_play.is_touchdown_pass = play_result.get('is_touchdown_pass')
                db_play.is_interception = play_result.get('is_interception')
                db_play.pass_target = play_result.get('pass_target')
                db_play.pass_defender = play_result.get('pass_defender')
                db_play.is_sack = play_result.get('is_sack')
                db_play.sack_yards = play_result.get('sack_yards')
                db_play.quarterback_hit = play_result.get('quarterback_hit')
                db_play.quarterback_scramble = play_result.get('quarterback_scramble')
                
                # Run play details
                db_play.run_gap = play_result.get('run_gap')
                db_play.yards_after_contact = play_result.get('yards_after_contact')
                db_play.is_touchdown_run = play_result.get('is_touchdown_run')
                db_play.is_fumble = play_result.get('is_fumble')
                db_play.fumble_recovered_by = play_result.get('fumble_recovered_by')
                db_play.fumble_forced_by = play_result.get('fumble_forced_by')
                
                # Play outcome
                db_play.is_first_down = play_result.get('is_first_down')
                db_play.is_turnover = play_result.get('is_turnover')
                
                # Calculate field position gained (using yards gained if available)
                if db_play.yards_gained is not None:
                    db_play.field_position_gained = db_play.yards_gained
                
                # Penalty details
                db_play.is_penalty_on_play = play_result.get('is_penalty_on_play')
                db_play.penalty_type = play_result.get('penalty_type')
                db_play.penalty_team = play_result.get('penalty_team')
                db_play.penalty_player = play_result.get('penalty_player')
                db_play.penalty_yards = play_result.get('penalty_yards')
                db_play.penalty_declined = play_result.get('penalty_declined')
                db_play.penalty_offset = play_result.get('penalty_offset')
                db_play.penalty_no_play = play_result.get('penalty_no_play')
                
                # Special teams details
                db_play.is_field_goal = play_result.get('is_field_goal')
                db_play.field_goal_distance = play_result.get('field_goal_distance')
                db_play.field_goal_result = play_result.get('field_goal_result')
                db_play.is_punt = play_result.get('is_punt')
                db_play.punt_distance = play_result.get('punt_distance')
                db_play.punt_return_yards = play_result.get('punt_return_yards')
                db_play.is_kickoff = play_result.get('is_kickoff')
                db_play.kickoff_return_yards = play_result.get('kickoff_return_yards')
                db_play.is_touchback = play_result.get('is_touchback')
                
                # Calculate advanced game context features
                game_context = self._calculate_game_context_features(plays, play_index, play, game_info)
                
                # Drive context
                db_play.drive_number = game_context.get('drive_number')
                db_play.drive_play_number = game_context.get('drive_play_number')
                db_play.drive_start_yardline = game_context.get('drive_start_yardline')
                db_play.drive_time_of_possession = game_context.get('drive_time_of_possession')
                db_play.drive_plays_so_far = game_context.get('drive_plays_so_far')
                
                # Game script features
                db_play.is_winning_team = game_context.get('is_winning_team')
                db_play.is_losing_team = game_context.get('is_losing_team')
                db_play.is_comeback_situation = game_context.get('is_comeback_situation')
                db_play.is_blowout_situation = game_context.get('is_blowout_situation')
                db_play.game_competitive_index = game_context.get('game_competitive_index')
                
                # Momentum indicators
                db_play.possessing_team_last_score = game_context.get('possessing_team_last_score')
                db_play.opposing_team_last_score = game_context.get('opposing_team_last_score')
                db_play.possessing_team_turnovers = game_context.get('possessing_team_turnovers')
                db_play.opposing_team_turnovers = game_context.get('opposing_team_turnovers')
                db_play.turnover_margin = game_context.get('turnover_margin')
                
                # Timeout context
                db_play.possessing_team_timeouts = game_context.get('possessing_team_timeouts')
                db_play.opposing_team_timeouts = game_context.get('opposing_team_timeouts')
                db_play.timeout_advantage = game_context.get('timeout_advantage')
                
                # Weather context
                db_play.weather_impact_score = game_context.get('weather_impact_score')
                db_play.is_indoor_game = game_context.get('is_indoor_game')
                
                # Field position context
                db_play.field_position_category = game_context.get('field_position_category')
                db_play.yards_from_own_endzone = game_context.get('yards_from_own_endzone')
                db_play.yards_from_opponent_endzone = game_context.get('yards_from_opponent_endzone')
                
                # Save play stats
                if play_details.play_stats:
                    stats_data = []
                    for stat in play_details.play_stats:
                        stats_data.append({
                            'club_code': stat.club_code,
                            'player_name': stat.player_name,
                            'stat_id': stat.stat_id,
                            'yards': stat.yards,
                            'gsis_id': stat.gsis_id
                        })
                    db_play.play_stats_json = stats_data
                
                # Save personnel data
                if play.summary.home:
                    db_play.home_personnel_json = [p.dict() for p in play.summary.home]
                if play.summary.away:
                    db_play.away_personnel_json = [p.dict() for p in play.summary.away]
            
            session.add(db_play)
            
    def _save_players(self, players: List[Player], session: Session):
        """Save or update player information"""
        # Get all player IDs we need to process
        player_ids = [player.nfl_id for player in players]
        
        # Fetch existing players in bulk
        existing_players = session.query(DBPlayer).filter(
            DBPlayer.nfl_id.in_(player_ids)
        ).all()
        existing_player_ids = {p.nfl_id for p in existing_players}
        
        # Update existing players
        for db_player in existing_players:
            # Find the corresponding player data
            for player in players:
                if player.nfl_id == db_player.nfl_id:
                    # Update fields that might change
                    db_player.team_id = player.team_id
                    db_player.uniform_number = player.uniform_number
                    db_player.position = player.position
                    db_player.position_group = player.position_group
                    break
        
        # Add new players
        new_players = []
        for player in players:
            if player.nfl_id not in existing_player_ids:
                db_player = DBPlayer(
                    nfl_id=player.nfl_id,
                    gsis_id=player.gsis_id,
                    first_name=player.first_name,
                    last_name=player.last_name,
                    player_name=player.player_name,
                    position=player.position,
                    position_group=player.position_group,
                    uniform_number=player.uniform_number,
                    team_id=player.team_id
                )
                new_players.append(db_player)
        
        # Bulk add new players
        if new_players:
            session.bulk_save_objects(new_players)
                
    def get_games(self, season: Optional[int] = None, week: Optional[str] = None, 
                  team_id: Optional[str] = None) -> List[DBGame]:
        """Query games from the database"""
        session = self.db.get_session()
        try:
            query = session.query(DBGame)
            
            if season:
                query = query.filter(DBGame.season == season)
            if week:
                query = query.filter(DBGame.week == week)
            if team_id:
                query = query.filter(or_(
                    DBGame.home_team_id == team_id,
                    DBGame.away_team_id == team_id
                ))
                
            return query.all()
        finally:
            session.close()
            
    def get_plays(self, game_id: Optional[str] = None, play_type: Optional[str] = None,
                  down: Optional[int] = None, quarter: Optional[int] = None) -> List[DBPlay]:
        """Query plays from the database"""
        session = self.db.get_session()
        try:
            query = session.query(DBPlay)
            
            if game_id:
                query = query.filter(DBPlay.game_id == game_id)
            if play_type:
                query = query.filter(DBPlay.play_type == play_type)
            if down:
                query = query.filter(DBPlay.down == down)
            if quarter:
                query = query.filter(DBPlay.quarter == quarter)
                
            return query.all()
        finally:
            session.close()
            
    def get_play_stats(self, game_id: str) -> Dict[str, Any]:
        """Get aggregated play statistics for a game"""
        session = self.db.get_session()
        try:
            plays = session.query(DBPlay).filter_by(game_id=game_id).all()
            
            stats = {
                'total_plays': len(plays),
                'scoring_plays': sum(1 for p in plays if p.is_scoring),
                'penalties': sum(1 for p in plays if p.is_penalty),
                'turnovers': sum(1 for p in plays if p.is_change_of_possession),
                'red_zone_plays': sum(1 for p in plays if p.is_redzone_play),
                'play_types': {},
                'downs': {1: 0, 2: 0, 3: 0, 4: 0}
            }
            
            for play in plays:
                # Count play types
                if play.play_type:
                    stats['play_types'][play.play_type] = stats['play_types'].get(play.play_type, 0) + 1
                
                # Count downs
                if play.down and play.down in stats['downs']:
                    stats['downs'][play.down] += 1
                    
            return stats
        finally:
            session.close()
            
    def close(self):
        """Close database connection"""
        self.db.close()
    
    def _parse_weather(self, weather_str: str) -> Dict[str, Any]:
        """Parse weather string into structured data"""
        result = {
            'temperature': None,
            'wind_speed': None,
            'wind_direction': None,
            'precipitation': None,
            'humidity': None,
            'conditions': None
        }
        
        if not weather_str:
            return result
            
        weather_lower = weather_str.lower()
        
        # Extract temperature
        temp_match = re.search(r'(\d+)\s*°?f?', weather_lower)
        if temp_match:
            result['temperature'] = float(temp_match.group(1))
        
        # Extract wind speed and direction
        wind_match = re.search(r'wind[:\s]+([nesw]+)?\s*@?\s*(\d+)\s*mph', weather_lower)
        if wind_match:
            if wind_match.group(1):
                result['wind_direction'] = wind_match.group(1).upper()
            result['wind_speed'] = float(wind_match.group(2))
        
        # Extract precipitation
        if 'rain' in weather_lower:
            result['precipitation'] = 'rain'
        elif 'snow' in weather_lower:
            result['precipitation'] = 'snow'
        elif 'clear' in weather_lower:
            result['precipitation'] = 'clear'
        
        # Extract humidity
        humidity_match = re.search(r'humidity[:\s]+(\d+)%?', weather_lower)
        if humidity_match:
            result['humidity'] = float(humidity_match.group(1))
        
        # Set conditions
        if 'dome' in weather_lower or 'indoor' in weather_lower:
            result['conditions'] = 'indoor'
        elif 'cloudy' in weather_lower:
            result['conditions'] = 'cloudy'
        elif 'clear' in weather_lower:
            result['conditions'] = 'clear'
        elif 'overcast' in weather_lower:
            result['conditions'] = 'overcast'
        
        return result
    
    def _extract_play_details(self, description: str) -> Dict[str, Any]:
        """Extract play details from description"""
        result = {
            'offensive_formation': None,
            'defensive_formation': None,
            'yards_gained': None,
            'pass_length': None,
            'pass_location': None,
            'run_direction': None
        }
        
        if not description:
            return result
            
        desc_lower = description.lower()
        
        # Extract offensive formation with more patterns
        offensive_formations = {
            'shotgun': ['shotgun', '(shotgun)'],
            'i-formation': ['i-formation', 'i formation', '(i-form)'],
            'singleback': ['singleback', 'single back', '(singleback)'],
            'pistol': ['pistol', '(pistol)'],
            'wildcat': ['wildcat', '(wildcat)'],
            'empty': ['empty', '(empty)', 'empty backfield'],
            'under-center': ['under center', '(under center)'],
            'ace': ['ace formation', '(ace)'],
            'strong': ['strong formation', '(strong)'],
            'weak': ['weak formation', '(weak)'],
            'jumbo': ['jumbo', '(jumbo)'],
            'goal-line': ['goal line', 'goal-line', '(goal line)']
        }
        
        for formation, patterns in offensive_formations.items():
            for pattern in patterns:
                if pattern in desc_lower:
                    result['offensive_formation'] = formation
                    break
            if result['offensive_formation']:
                break
        
        # Extract yards gained
        yards_match = re.search(r'for\s+(-?\d+)\s+yard', desc_lower)
        if yards_match:
            result['yards_gained'] = int(yards_match.group(1))
        else:
            # Check for no gain
            if 'no gain' in desc_lower:
                result['yards_gained'] = 0
        
        # For pass plays
        if 'pass' in desc_lower:
            # Pass length
            if 'short' in desc_lower:
                result['pass_length'] = 'short'
            elif 'deep' in desc_lower:
                result['pass_length'] = 'deep'
            else:
                result['pass_length'] = 'medium'
            
            # Pass location
            if 'left' in desc_lower:
                result['pass_location'] = 'left'
            elif 'right' in desc_lower:
                result['pass_location'] = 'right'
            elif 'middle' in desc_lower:
                result['pass_location'] = 'middle'
        
        # For run plays
        if 'rush' in desc_lower or 'run' in desc_lower:
            if 'left end' in desc_lower or 'left tackle' in desc_lower or 'left guard' in desc_lower:
                result['run_direction'] = 'left'
            elif 'right end' in desc_lower or 'right tackle' in desc_lower or 'right guard' in desc_lower:
                result['run_direction'] = 'right'
            elif 'middle' in desc_lower or 'center' in desc_lower:
                result['run_direction'] = 'middle'
        
        return result
    
    def _calculate_time_remaining(self, quarter: int, game_clock: str) -> Dict[str, Any]:
        """Calculate time remaining in half and game"""
        result = {
            'time_remaining_half': None,
            'time_remaining_game': None,
            'is_two_minute_drill': False
        }
        
        if not game_clock or not quarter:
            return result
        
        # Parse game clock (MM:SS)
        try:
            parts = game_clock.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            clock_seconds = minutes * 60 + seconds
        except:
            return result
        
        # Calculate time remaining in half
        if quarter in [1, 3]:
            result['time_remaining_half'] = clock_seconds + 900  # Plus 15 minutes for Q2/Q4
        else:
            result['time_remaining_half'] = clock_seconds
        
        # Calculate time remaining in game
        if quarter == 1:
            result['time_remaining_game'] = clock_seconds + 2700  # Plus 45 minutes
        elif quarter == 2:
            result['time_remaining_game'] = clock_seconds + 1800  # Plus 30 minutes
        elif quarter == 3:
            result['time_remaining_game'] = clock_seconds + 900   # Plus 15 minutes
        else:
            result['time_remaining_game'] = clock_seconds
        
        # Check for two-minute drill
        result['is_two_minute_drill'] = result['time_remaining_half'] <= 120
        
        return result
    
    def _update_team_stats(self, db_game: DBGame, standings_data: Dict[str, Any]):
        """Update team statistics from standings data"""
        # Check if standings data has the expected structure
        if not standings_data or 'weeks' not in standings_data:
            return
            
        # Get the latest week's standings - ensure weeks list is not empty
        weeks_list = standings_data.get('weeks', [])
        if not weeks_list:
            return
            
        latest_week = weeks_list[-1]
        if not latest_week or 'standings' not in latest_week:
            return
            
        for team_standing in latest_week['standings']:
            team_data = team_standing.get('team', {})
            team_name = team_data.get('fullName', '')
            
            # Match by team name
            if team_name == db_game.home_team_name:
                # Update home team stats
                overall = team_standing.get('overall', {})
                db_game.home_team_wins = overall.get('wins', 0)
                db_game.home_team_losses = overall.get('losses', 0)
                
                # Extract win streak from streak data
                streak = overall.get('streak', {})
                if streak:
                    # Handle both old string format and new object format
                    if isinstance(streak, str):
                        # Old format: "W3" or "L2"
                        if streak and len(streak) > 0:
                            if streak[0] == 'W':
                                db_game.home_team_win_streak = int(streak[1:]) if len(streak) > 1 else 0
                            else:
                                db_game.home_team_win_streak = -int(streak[1:]) if len(streak) > 1 else 0
                    elif isinstance(streak, dict):
                        # New format: {"type": "W", "length": 3}
                        streak_type = streak.get('type', '')
                        streak_length = streak.get('length', 0)
                        if streak_type == 'W':
                            db_game.home_team_win_streak = streak_length
                        else:
                            db_game.home_team_win_streak = -streak_length
                
                # For now, set ranks to None as we'd need additional data
                # These could be calculated from conference/division standings
                db_game.home_team_offensive_rank = None
                db_game.home_team_defensive_rank = None
                
            elif team_name == db_game.away_team_name:
                # Update away team stats
                overall = team_standing.get('overall', {})
                db_game.away_team_wins = overall.get('wins', 0)
                db_game.away_team_losses = overall.get('losses', 0)
                
                # Extract win streak from streak data
                streak = overall.get('streak', {})
                if streak:
                    # Handle both old string format and new object format
                    if isinstance(streak, str):
                        # Old format: "W3" or "L2"
                        if streak and len(streak) > 0:
                            if streak[0] == 'W':
                                db_game.away_team_win_streak = int(streak[1:]) if len(streak) > 1 else 0
                            else:
                                db_game.away_team_win_streak = -int(streak[1:]) if len(streak) > 1 else 0
                    elif isinstance(streak, dict):
                        # New format: {"type": "W", "length": 3}
                        streak_type = streak.get('type', '')
                        streak_length = streak.get('length', 0)
                        if streak_type == 'W':
                            db_game.away_team_win_streak = streak_length
                        else:
                            db_game.away_team_win_streak = -streak_length
                
                # For now, set ranks to None
                db_game.away_team_offensive_rank = None
                db_game.away_team_defensive_rank = None
    
    def _analyze_defensive_personnel(self, defensive_players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze defensive personnel to determine formation and package"""
        result = {
            'defensive_formation': None,
            'defensive_package': None,
            'db_count': 0,
            'lb_count': 0,
            'dl_count': 0,
            'box_count': 0
        }
        
        if not defensive_players:
            return result
        
        # Count position groups
        position_counts = {'DB': 0, 'LB': 0, 'DL': 0}
        positions = []
        
        for player in defensive_players:
            pos_group = player.get('positionGroup', '')
            position = player.get('position', '')
            
            if pos_group in position_counts:
                position_counts[pos_group] += 1
            positions.append(position)
        
        result['db_count'] = position_counts['DB']
        result['lb_count'] = position_counts['LB']
        result['dl_count'] = position_counts['DL']
        
        # Determine defensive package based on DB count
        if result['db_count'] >= 6:
            result['defensive_package'] = 'dime'
        elif result['db_count'] == 5:
            result['defensive_package'] = 'nickel'
        elif result['db_count'] == 4:
            result['defensive_package'] = 'base'
        elif result['db_count'] <= 3:
            result['defensive_package'] = 'heavy'
        
        # Infer formation based on personnel
        if result['dl_count'] == 4:
            if result['lb_count'] == 3:
                result['defensive_formation'] = '4-3'
            elif result['lb_count'] == 2:
                result['defensive_formation'] = '4-2-5'
            elif result['lb_count'] == 1:
                result['defensive_formation'] = '4-1-6'
        elif result['dl_count'] == 3:
            if result['lb_count'] == 4:
                result['defensive_formation'] = '3-4'
            elif result['lb_count'] == 3:
                result['defensive_formation'] = '3-3-5'
            elif result['lb_count'] == 2:
                result['defensive_formation'] = '3-2-6'
        elif result['dl_count'] == 2:
            if result['lb_count'] == 4:
                result['defensive_formation'] = '2-4-5'
        elif result['dl_count'] == 5:
            result['defensive_formation'] = '5-2'
        elif result['dl_count'] == 6:
            result['defensive_formation'] = '6-1'
        
        # Calculate box count (DL + LB + SS in the box)
        result['box_count'] = result['dl_count'] + result['lb_count']
        
        # Add 1 to box count if there's a SS (strong safety) in the personnel
        for pos in positions:
            if pos == 'SS':
                result['box_count'] += 1
                break
        
        return result
    
    def _extract_play_result_metrics(self, description: str, play_type: str) -> Dict[str, Any]:
        """Extract detailed play result metrics from description"""
        result = {
            # Pass play details
            'is_complete_pass': None,
            'is_touchdown_pass': None,
            'is_interception': None,
            'pass_target': None,
            'pass_defender': None,
            'is_sack': None,
            'sack_yards': None,
            'quarterback_hit': None,
            'quarterback_scramble': None,
            
            # Run play details
            'run_gap': None,
            'yards_after_contact': None,
            'is_touchdown_run': None,
            'is_fumble': None,
            'fumble_recovered_by': None,
            'fumble_forced_by': None,
            
            # Play outcome
            'is_first_down': None,
            'is_turnover': None,
            'field_position_gained': None,
            
            # Penalty details
            'is_penalty_on_play': None,
            'penalty_type': None,
            'penalty_team': None,
            'penalty_player': None,
            'penalty_yards': None,
            'penalty_declined': None,
            'penalty_offset': None,
            'penalty_no_play': None,
            
            # Special teams details
            'is_field_goal': None,
            'field_goal_distance': None,
            'field_goal_result': None,
            'is_punt': None,
            'punt_distance': None,
            'punt_return_yards': None,
            'is_kickoff': None,
            'kickoff_return_yards': None,
            'is_touchback': None
        }
        
        if not description:
            return result
            
        desc_lower = description.lower()
        
        # Check for touchdown
        if 'touchdown' in desc_lower:
            if 'pass' in play_type.lower():
                result['is_touchdown_pass'] = True
            elif 'rush' in play_type.lower() or 'run' in play_type.lower():
                result['is_touchdown_run'] = True
        
        # Pass play analysis
        if 'pass' in desc_lower:
            # Check completion status
            if 'incomplete' in desc_lower:
                result['is_complete_pass'] = False
            elif 'complete' in desc_lower or ('for' in desc_lower and 'yard' in desc_lower):
                result['is_complete_pass'] = True
            
            # Check for interception
            if 'intercepted' in desc_lower:
                result['is_interception'] = True
                result['is_turnover'] = True
                result['is_complete_pass'] = False
            
            # Extract pass target
            target_match = re.search(r'to\s+([A-Z]\.[A-Za-z\-]+)', description)
            if target_match:
                result['pass_target'] = target_match.group(1)
            
            # Extract defender
            defender_match = re.search(r'\(([A-Z]\.[A-Za-z\-]+(?:,\s*[A-Z]\.[A-Za-z\-]+)*)\)', description)
            if defender_match and 'pass' in desc_lower:
                result['pass_defender'] = defender_match.group(1)
            
            # Check for scramble
            if 'scramble' in desc_lower:
                result['quarterback_scramble'] = True
        
        # Check for sack
        if 'sacked' in desc_lower:
            result['is_sack'] = True
            sack_match = re.search(r'for\s+(-?\d+)\s+yard', desc_lower)
            if sack_match:
                result['sack_yards'] = abs(int(sack_match.group(1)))
        
        # Run play analysis
        if ('rush' in play_type.lower() or 'run' in desc_lower) and 'pass' not in desc_lower:
            # Extract run gap
            gaps = {
                'left end': ['left end', 'swept left'],
                'left tackle': ['left tackle'],
                'left guard': ['left guard'],
                'middle': ['up the middle', 'middle'],
                'right guard': ['right guard'],
                'right tackle': ['right tackle'],
                'right end': ['right end', 'swept right']
            }
            
            for gap, patterns in gaps.items():
                for pattern in patterns:
                    if pattern in desc_lower:
                        result['run_gap'] = gap
                        break
                if result['run_gap']:
                    break
        
        # Check for fumble
        if 'fumble' in desc_lower:
            result['is_fumble'] = True
            
            # Check who recovered
            recovered_match = re.search(r'recovered by\s+([A-Z]{2,3})-([A-Z]\.[A-Za-z\-]+)', description, re.IGNORECASE)
            if recovered_match:
                result['fumble_recovered_by'] = f"{recovered_match.group(1)}-{recovered_match.group(2)}"
            
            # Check who forced
            forced_match = re.search(r'\(([A-Z]\.[A-Za-z\-]+)\)', description)
            if forced_match and 'fumble' in desc_lower:
                result['fumble_forced_by'] = forced_match.group(1)
            
            # Determine if it's a turnover
            if recovered_match and play_type:
                # This is simplified - would need team info to be accurate
                result['is_turnover'] = True
        
        # Check for first down
        if 'first down' in desc_lower or '1st down' in desc_lower:
            result['is_first_down'] = True
        
        # Penalty analysis
        if 'penalty' in desc_lower:
            result['is_penalty_on_play'] = True
            
            # Extract penalty type
            penalty_types = ['holding', 'false start', 'offside', 'delay of game', 'illegal formation',
                           'pass interference', 'roughing the passer', 'unnecessary roughness',
                           'facemask', 'illegal contact', 'illegal use of hands', 'encroachment']
            
            for ptype in penalty_types:
                if ptype in desc_lower:
                    result['penalty_type'] = ptype.title()
                    break
            
            # Extract penalty yards
            penalty_yards_match = re.search(r'(\d+)\s+yard', desc_lower)
            if penalty_yards_match and 'penalty' in desc_lower:
                result['penalty_yards'] = int(penalty_yards_match.group(1))
            
            # Extract penalized team and player
            penalty_match = re.search(r'penalty on\s+([A-Z]{2,3})-([A-Z]\.[A-Za-z\-]+)', description, re.IGNORECASE)
            if penalty_match:
                result['penalty_team'] = penalty_match.group(1)
                result['penalty_player'] = penalty_match.group(2)
            
            # Check if declined or offset
            if 'declined' in desc_lower:
                result['penalty_declined'] = True
            if 'offsetting' in desc_lower:
                result['penalty_offset'] = True
            if 'no play' in desc_lower:
                result['penalty_no_play'] = True
        
        # Special teams analysis
        if 'field goal' in desc_lower:
            result['is_field_goal'] = True
            
            # Extract distance
            fg_match = re.search(r'(\d+)\s+yard\s+field\s+goal', desc_lower)
            if fg_match:
                result['field_goal_distance'] = int(fg_match.group(1))
            
            # Extract result
            if 'good' in desc_lower:
                result['field_goal_result'] = 'GOOD'
            elif 'no good' in desc_lower:
                result['field_goal_result'] = 'NO GOOD'
            elif 'blocked' in desc_lower:
                result['field_goal_result'] = 'BLOCKED'
        
        elif 'punt' in desc_lower and 'punts' in desc_lower:
            result['is_punt'] = True
            
            # Extract punt distance
            punt_match = re.search(r'punts\s+(\d+)\s+yard', desc_lower)
            if punt_match:
                result['punt_distance'] = int(punt_match.group(1))
            
            # Extract return yards
            return_match = re.search(r'for\s+(\d+)\s+yard', desc_lower)
            if return_match and 'return' not in desc_lower:
                result['punt_return_yards'] = int(return_match.group(1))
        
        elif 'kickoff' in desc_lower:
            result['is_kickoff'] = True
            
            # Extract return yards
            return_match = re.search(r'for\s+(\d+)\s+yard', desc_lower)
            if return_match:
                result['kickoff_return_yards'] = int(return_match.group(1))
            
            # Check for touchback
            if 'touchback' in desc_lower:
                result['is_touchback'] = True
        
        return result
    
    def _calculate_game_context_features(self, game_plays: List, current_play_index: int, 
                                       current_play, game_info) -> Dict[str, Any]:
        """Calculate advanced game context features for a play"""
        result = {
            # Drive context
            'drive_number': None,
            'drive_play_number': None,
            'drive_start_yardline': None,
            'drive_time_of_possession': None,
            'drive_plays_so_far': None,
            
            # Game script features
            'is_winning_team': None,
            'is_losing_team': None,
            'is_comeback_situation': None,
            'is_blowout_situation': None,
            'game_competitive_index': None,
            
            # Momentum indicators
            'possessing_team_last_score': None,
            'opposing_team_last_score': None,
            'possessing_team_turnovers': None,
            'opposing_team_turnovers': None,
            'turnover_margin': None,
            
            # Timeout context
            'possessing_team_timeouts': None,
            'opposing_team_timeouts': None,
            'timeout_advantage': None,
            
            # Weather context
            'weather_impact_score': None,
            'is_indoor_game': None,
            
            # Field position context
            'field_position_category': None,
            'yards_from_own_endzone': None,
            'yards_from_opponent_endzone': None
        }
        
        if not current_play or not hasattr(current_play, 'summary') or not current_play.summary:
            return result
        
        play_details = current_play.summary.play
        if not play_details:
            return result
        
        # Calculate drive context
        drive_info = self._calculate_drive_context(game_plays, current_play_index, current_play)
        result.update(drive_info)
        
        # Calculate game script features
        game_script = self._calculate_game_script_features(play_details, current_play)
        result.update(game_script)
        
        # Calculate momentum indicators
        momentum = self._calculate_momentum_indicators(game_plays, current_play_index, current_play)
        result.update(momentum)
        
        # Calculate timeout context
        timeout_context = self._calculate_timeout_context(play_details, current_play)
        result.update(timeout_context)
        
        # Calculate weather impact
        weather_impact = self._calculate_weather_impact(game_info)
        result.update(weather_impact)
        
        # Calculate field position context
        field_position = self._calculate_field_position_context(play_details)
        result.update(field_position)
        
        return result
    
    def _calculate_drive_context(self, game_plays: List, current_play_index: int, current_play) -> Dict[str, Any]:
        """Calculate drive-level context"""
        result = {
            'drive_number': 1,
            'drive_play_number': 1,
            'drive_start_yardline': None,
            'drive_time_of_possession': None,
            'drive_plays_so_far': 1
        }
        
        if current_play_index == 0:
            return result
        
        # Count possession changes to determine drive number
        drive_count = 1
        plays_in_current_drive = 1
        current_possession_team = current_play.possession_team_id
        drive_start_time = None
        
        # Look backwards to find start of current drive
        for i in range(current_play_index - 1, -1, -1):
            prev_play = game_plays[i]
            if hasattr(prev_play, 'possession_team_id'):
                if prev_play.possession_team_id != current_possession_team:
                    # Found start of current drive
                    break
                else:
                    plays_in_current_drive += 1
                    # Get the first play's yardline as drive start
                    if hasattr(prev_play, 'summary') and prev_play.summary and prev_play.summary.play:
                        result['drive_start_yardline'] = prev_play.summary.play.absolute_yardline_number
                        drive_start_time = prev_play.summary.play.time_of_day_utc
        
        # Count total drives by counting possession changes
        for i in range(current_play_index):
            if i > 0:
                curr_team = game_plays[i].possession_team_id if hasattr(game_plays[i], 'possession_team_id') else None
                prev_team = game_plays[i-1].possession_team_id if hasattr(game_plays[i-1], 'possession_team_id') else None
                if curr_team != prev_team and curr_team and prev_team:
                    drive_count += 1
        
        result['drive_number'] = drive_count
        result['drive_play_number'] = plays_in_current_drive
        result['drive_plays_so_far'] = plays_in_current_drive
        
        # Calculate time of possession for current drive
        if drive_start_time and hasattr(current_play, 'summary') and current_play.summary and current_play.summary.play:
            try:
                from datetime import datetime
                start_time = datetime.fromisoformat(drive_start_time.replace('Z', '+00:00'))
                current_time = datetime.fromisoformat(current_play.summary.play.time_of_day_utc.replace('Z', '+00:00'))
                result['drive_time_of_possession'] = int((start_time - current_time).total_seconds())
            except:
                pass
        
        return result
    
    def _calculate_game_script_features(self, play_details, current_play) -> Dict[str, Any]:
        """Calculate game script features (winning/losing scenarios)"""
        result = {
            'is_winning_team': None,
            'is_losing_team': None,
            'is_comeback_situation': None,
            'is_blowout_situation': None,
            'game_competitive_index': None
        }
        
        # Determine if possession team is home or away
        possession_team_is_home = current_play.possession_team_id == current_play.home_team_id
        
        if possession_team_is_home:
            possession_score = play_details.home_score
            opponent_score = play_details.visitor_score
        else:
            possession_score = play_details.visitor_score
            opponent_score = play_details.home_score
        
        score_diff = possession_score - opponent_score
        
        # Basic winning/losing status
        result['is_winning_team'] = score_diff > 0
        result['is_losing_team'] = score_diff < 0
        
        # Comeback situation: down by 10+ in 4th quarter
        if play_details.quarter >= 4 and score_diff <= -10:
            result['is_comeback_situation'] = True
        else:
            result['is_comeback_situation'] = False
        
        # Blowout situation: up/down by 21+ points
        result['is_blowout_situation'] = abs(score_diff) >= 21
        
        # Game competitive index (0 = blowout, 1 = very competitive)
        # Based on score differential and time remaining
        time_factor = min(play_details.quarter / 4.0, 1.0)  # More weight to later quarters
        score_factor = max(0, 1 - (abs(score_diff) / 28.0))  # 28 points = 4 TDs
        result['game_competitive_index'] = (score_factor * 0.7) + (time_factor * 0.3)
        
        return result
    
    def _calculate_momentum_indicators(self, game_plays: List, current_play_index: int, current_play) -> Dict[str, Any]:
        """Calculate momentum indicators"""
        result = {
            'possessing_team_last_score': 0,
            'opposing_team_last_score': 0,
            'possessing_team_turnovers': 0,
            'opposing_team_turnovers': 0,
            'turnover_margin': 0
        }
        
        current_possession_team = current_play.possession_team_id
        plays_since_possession_score = 0
        plays_since_opponent_score = 0
        possession_turnovers = 0
        opponent_turnovers = 0
        
        # Look through previous plays
        for i in range(current_play_index - 1, -1, -1):
            play = game_plays[i]
            if not hasattr(play, 'summary') or not play.summary or not play.summary.play:
                continue
                
            play_details = play.summary.play
            play_possession_team = play.possession_team_id
            
            # Check for scoring plays
            if play_details.is_scoring:
                if play_possession_team == current_possession_team:
                    if plays_since_possession_score == 0:  # First scoring play we found
                        result['possessing_team_last_score'] = i
                    plays_since_possession_score += 1
                else:
                    if plays_since_opponent_score == 0:  # First scoring play we found
                        result['opposing_team_last_score'] = i
                    plays_since_opponent_score += 1
            
            # Count turnovers
            if play_details.is_change_of_possession:
                # The team that had possession when turnover occurred
                if play_possession_team == current_possession_team:
                    possession_turnovers += 1
                else:
                    opponent_turnovers += 1
        
        result['possessing_team_turnovers'] = possession_turnovers
        result['opposing_team_turnovers'] = opponent_turnovers
        result['turnover_margin'] = opponent_turnovers - possession_turnovers  # Positive is good
        
        return result
    
    def _calculate_timeout_context(self, play_details, current_play) -> Dict[str, Any]:
        """Calculate timeout management context"""
        result = {
            'possessing_team_timeouts': None,
            'opposing_team_timeouts': None,
            'timeout_advantage': None
        }
        
        # Determine if possession team is home or away
        possession_team_is_home = current_play.possession_team_id == current_play.home_team_id
        
        if possession_team_is_home:
            possession_timeouts = play_details.home_timeouts_left
            opponent_timeouts = play_details.visitor_timeouts_left
        else:
            possession_timeouts = play_details.visitor_timeouts_left
            opponent_timeouts = play_details.home_timeouts_left
        
        result['possessing_team_timeouts'] = possession_timeouts
        result['opposing_team_timeouts'] = opponent_timeouts
        result['timeout_advantage'] = possession_timeouts - opponent_timeouts
        
        return result
    
    def _calculate_weather_impact(self, game_info) -> Dict[str, Any]:
        """Calculate weather impact on play calling"""
        result = {
            'weather_impact_score': 0.0,
            'is_indoor_game': None
        }
        
        if not game_info:
            return result
        
        # Check if indoor game
        if hasattr(game_info, 'venue') and game_info.venue:
            roof_type = getattr(game_info.venue, 'roof_type', None)
            result['is_indoor_game'] = roof_type in ['DOME', 'RETRACTABLE_CLOSED', 'INDOOR']
            
            if result['is_indoor_game']:
                result['weather_impact_score'] = 0.0
                return result
        
        # Parse weather conditions for impact
        weather = getattr(game_info, 'weather', None)
        if not weather:
            return result
        
        weather_lower = weather.lower()
        impact_score = 0.0
        
        # Wind impact
        if 'wind' in weather_lower:
            # Extract wind speed if available
            wind_match = re.search(r'(\d+)\s*mph', weather_lower)
            if wind_match:
                wind_speed = int(wind_match.group(1))
                if wind_speed > 20:
                    impact_score += 0.4
                elif wind_speed > 15:
                    impact_score += 0.3
                elif wind_speed > 10:
                    impact_score += 0.2
                else:
                    impact_score += 0.1
        
        # Precipitation impact
        if any(condition in weather_lower for condition in ['rain', 'snow', 'sleet']):
            impact_score += 0.3
        
        # Temperature impact
        temp_match = re.search(r'(\d+)\s*°?f?', weather_lower)
        if temp_match:
            temp = int(temp_match.group(1))
            if temp < 32:  # Freezing
                impact_score += 0.2
            elif temp < 40:  # Very cold
                impact_score += 0.1
            elif temp > 90:  # Very hot
                impact_score += 0.1
        
        result['weather_impact_score'] = min(impact_score, 1.0)
        return result
    
    def _calculate_field_position_context(self, play_details) -> Dict[str, Any]:
        """Calculate field position context"""
        result = {
            'field_position_category': None,
            'yards_from_own_endzone': None,
            'yards_from_opponent_endzone': None
        }
        
        if not hasattr(play_details, 'absolute_yardline_number'):
            return result
        
        yardline = play_details.absolute_yardline_number
        
        result['yards_from_own_endzone'] = yardline
        result['yards_from_opponent_endzone'] = 100 - yardline
        
        # Categorize field position
        if yardline <= 20:
            result['field_position_category'] = 'own_territory'
        elif yardline <= 40:
            result['field_position_category'] = 'own_territory'
        elif yardline <= 60:
            result['field_position_category'] = 'midfield'
        elif yardline <= 80:
            result['field_position_category'] = 'opponent_territory'
        else:
            result['field_position_category'] = 'red_zone'
        
        return result
    
    def _calculate_historical_team_stats(self, game_date: str, home_team_id: str, away_team_id: str, 
                                       season: int, session) -> Dict[str, Any]:
        """Calculate historical team statistics from previous games"""
        result = {}
        
        # Calculate stats for both teams
        home_stats = self._calculate_team_stats(home_team_id, game_date, season, True, session)
        away_stats = self._calculate_team_stats(away_team_id, game_date, season, False, session)
        
        # Add home team stats with prefix
        for key, value in home_stats.items():
            result[f'home_team_{key}'] = value
        
        # Add away team stats with prefix
        for key, value in away_stats.items():
            result[f'away_team_{key}'] = value
        
        # Calculate head-to-head stats
        h2h_stats = self._calculate_head_to_head_stats(home_team_id, away_team_id, game_date, session)
        result.update(h2h_stats)
        
        return result
    
    def _calculate_team_stats(self, team_id: str, game_date: str, season: int, is_home: bool, session) -> Dict[str, Any]:
        """Calculate comprehensive stats for a single team"""
        from sqlalchemy import or_, and_, func
        
        result = {
            'points_per_game': 0.0,
            'yards_per_game': 0.0,
            'pass_yards_per_game': 0.0,
            'rush_yards_per_game': 0.0,
            'third_down_pct': 0.0,
            'red_zone_pct': 0.0,
            'turnover_rate': 0.0,
            'time_of_possession': 0.0,
            'points_allowed_per_game': 0.0,
            'yards_allowed_per_game': 0.0,
            'pass_yards_allowed_per_game': 0.0,
            'rush_yards_allowed_per_game': 0.0,
            'third_down_def_pct': 0.0,
            'red_zone_def_pct': 0.0,
            'takeaway_rate': 0.0,
            'sacks_per_game': 0.0,
            'last3_wins': 0,
            'last3_points_per_game': 0.0,
            'last3_points_allowed': 0.0,
            'last5_wins': 0,
            'last5_points_per_game': 0.0,
            'last5_points_allowed': 0.0
        }
        
        # Get games before current game date for this team
        team_games = session.query(DBGame).filter(
            and_(
                or_(DBGame.home_team_id == team_id, DBGame.away_team_id == team_id),
                DBGame.season == season,
                DBGame.date < game_date  # Only games before current game
            )
        ).order_by(DBGame.date.desc()).all()
        
        if not team_games:
            return result
        
        # Calculate season-long stats
        total_points = 0
        total_points_allowed = 0
        games_count = len(team_games)
        
        # For more detailed stats, we need play-level data
        total_yards = 0
        total_pass_yards = 0
        total_rush_yards = 0
        total_yards_allowed = 0
        total_pass_yards_allowed = 0
        total_rush_yards_allowed = 0
        total_third_down_attempts = 0
        total_third_down_conversions = 0
        total_third_down_def_attempts = 0
        total_third_down_def_stops = 0
        total_red_zone_attempts = 0
        total_red_zone_tds = 0
        total_red_zone_def_attempts = 0
        total_red_zone_def_stops = 0
        total_turnovers_committed = 0
        total_turnovers_forced = 0
        total_sacks_allowed = 0
        total_sacks_forced = 0
        
        for game in team_games:
            # Determine if team was home or away
            team_was_home = game.home_team_id == team_id
            
            # Get points scored and allowed
            if team_was_home:
                points_scored = game.home_score_total
                points_allowed = game.away_score_total
            else:
                points_scored = game.away_score_total
                points_allowed = game.home_score_total
            
            total_points += points_scored
            total_points_allowed += points_allowed
            
            # Get play-level stats for this game
            plays = session.query(DBPlay).filter(DBPlay.game_id == game.id).all()
            
            for play in plays:
                # Skip if no play details
                if not play.yards_gained and play.yards_gained != 0:
                    continue
                
                # Determine if this team had possession
                team_had_possession = play.possession_team_id == team_id
                
                if team_had_possession:
                    # Offensive stats
                    if play.yards_gained is not None:
                        total_yards += play.yards_gained
                        
                        if 'pass' in (play.play_type or ''):
                            total_pass_yards += max(0, play.yards_gained)
                        elif 'rush' in (play.play_type or ''):
                            total_rush_yards += max(0, play.yards_gained)
                    
                    # Third down stats
                    if play.down == 3:
                        total_third_down_attempts += 1
                        if play.is_first_down:
                            total_third_down_conversions += 1
                    
                    # Red zone stats
                    if play.is_redzone_play:
                        total_red_zone_attempts += 1
                        if play.is_touchdown_pass or play.is_touchdown_run:
                            total_red_zone_tds += 1
                    
                    # Turnover stats (committed)
                    if play.is_turnover:
                        total_turnovers_committed += 1
                    
                    # Sacks allowed
                    if play.is_sack:
                        total_sacks_allowed += 1
                
                else:
                    # Defensive stats
                    if play.yards_gained is not None:
                        total_yards_allowed += play.yards_gained
                        
                        if 'pass' in (play.play_type or ''):
                            total_pass_yards_allowed += max(0, play.yards_gained)
                        elif 'rush' in (play.play_type or ''):
                            total_rush_yards_allowed += max(0, play.yards_gained)
                    
                    # Third down defense
                    if play.down == 3:
                        total_third_down_def_attempts += 1
                        if not play.is_first_down:
                            total_third_down_def_stops += 1
                    
                    # Red zone defense
                    if play.is_redzone_play:
                        total_red_zone_def_attempts += 1
                        if not (play.is_touchdown_pass or play.is_touchdown_run):
                            total_red_zone_def_stops += 1
                    
                    # Turnovers forced
                    if play.is_turnover:
                        total_turnovers_forced += 1
                    
                    # Sacks forced
                    if play.is_sack:
                        total_sacks_forced += 1
        
        # Calculate averages
        if games_count > 0:
            result['points_per_game'] = total_points / games_count
            result['points_allowed_per_game'] = total_points_allowed / games_count
            result['yards_per_game'] = total_yards / games_count
            result['pass_yards_per_game'] = total_pass_yards / games_count
            result['rush_yards_per_game'] = total_rush_yards / games_count
            result['yards_allowed_per_game'] = total_yards_allowed / games_count
            result['pass_yards_allowed_per_game'] = total_pass_yards_allowed / games_count
            result['rush_yards_allowed_per_game'] = total_rush_yards_allowed / games_count
            result['sacks_per_game'] = total_sacks_forced / games_count
            
            # Calculate percentages
            if total_third_down_attempts > 0:
                result['third_down_pct'] = (total_third_down_conversions / total_third_down_attempts) * 100
            
            if total_third_down_def_attempts > 0:
                result['third_down_def_pct'] = (total_third_down_def_stops / total_third_down_def_attempts) * 100
            
            if total_red_zone_attempts > 0:
                result['red_zone_pct'] = (total_red_zone_tds / total_red_zone_attempts) * 100
            
            if total_red_zone_def_attempts > 0:
                result['red_zone_def_pct'] = (total_red_zone_def_stops / total_red_zone_def_attempts) * 100
            
            # Calculate turnover rates (per game)
            result['turnover_rate'] = total_turnovers_committed / games_count
            result['takeaway_rate'] = total_turnovers_forced / games_count
        
        # Calculate recent form (last 3 games)
        if len(team_games) >= 3:
            recent_3_games = team_games[:3]
            wins_3 = 0
            points_3 = 0
            points_allowed_3 = 0
            
            for game in recent_3_games:
                team_was_home = game.home_team_id == team_id
                if team_was_home:
                    points_scored = game.home_score_total
                    points_allowed = game.away_score_total
                    won = game.home_score_total > game.away_score_total
                else:
                    points_scored = game.away_score_total
                    points_allowed = game.home_score_total
                    won = game.away_score_total > game.home_score_total
                
                if won:
                    wins_3 += 1
                points_3 += points_scored
                points_allowed_3 += points_allowed
            
            result['last3_wins'] = wins_3
            result['last3_points_per_game'] = points_3 / 3
            result['last3_points_allowed'] = points_allowed_3 / 3
        
        # Calculate recent form (last 5 games)
        if len(team_games) >= 5:
            recent_5_games = team_games[:5]
            wins_5 = 0
            points_5 = 0
            points_allowed_5 = 0
            
            for game in recent_5_games:
                team_was_home = game.home_team_id == team_id
                if team_was_home:
                    points_scored = game.home_score_total
                    points_allowed = game.away_score_total
                    won = game.home_score_total > game.away_score_total
                else:
                    points_scored = game.away_score_total
                    points_allowed = game.home_score_total
                    won = game.away_score_total > game.home_score_total
                
                if won:
                    wins_5 += 1
                points_5 += points_scored
                points_allowed_5 += points_allowed
            
            result['last5_wins'] = wins_5
            result['last5_points_per_game'] = points_5 / 5
            result['last5_points_allowed'] = points_allowed_5 / 5
        
        return result
    
    def _calculate_head_to_head_stats(self, home_team_id: str, away_team_id: str, game_date: str, session) -> Dict[str, Any]:
        """Calculate head-to-head statistics between two teams"""
        from sqlalchemy import or_, and_
        
        result = {
            'head_to_head_home_wins': 0,
            'head_to_head_away_wins': 0,
            'head_to_head_avg_total_points': 0.0
        }
        
        # Get recent head-to-head games (last 5 years)
        h2h_games = session.query(DBGame).filter(
            and_(
                or_(
                    and_(DBGame.home_team_id == home_team_id, DBGame.away_team_id == away_team_id),
                    and_(DBGame.home_team_id == away_team_id, DBGame.away_team_id == home_team_id)
                ),
                DBGame.date < game_date  # Only games before current game
            )
        ).order_by(DBGame.date.desc()).limit(10).all()  # Last 10 H2H games
        
        if not h2h_games:
            return result
        
        home_wins = 0
        away_wins = 0
        total_points = 0
        
        for game in h2h_games:
            game_total_points = game.home_score_total + game.away_score_total
            total_points += game_total_points
            
            # Determine winner from perspective of current matchup
            if game.home_team_id == home_team_id:
                # Same matchup (home team was home)
                if game.home_score_total > game.away_score_total:
                    home_wins += 1
                else:
                    away_wins += 1
            else:
                # Reverse matchup (current home team was away)
                if game.away_score_total > game.home_score_total:
                    home_wins += 1
                else:
                    away_wins += 1
        
        result['head_to_head_home_wins'] = home_wins
        result['head_to_head_away_wins'] = away_wins
        result['head_to_head_avg_total_points'] = total_points / len(h2h_games)
        
        return result
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import db, DBGame, DBPlay, DBPlayStat, DBPlayer
from models import Game, Play, PlayStat, Player, PlaySummary
import logging

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
            
            # Save plays
            if game.plays:
                self._save_plays(db_game, game.plays, session)
            
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
                
    def _save_plays(self, db_game: DBGame, plays: List[Play], session: Session):
        """Save plays for a game"""
        # Remove existing plays for this game
        session.query(DBPlay).filter_by(game_id=db_game.id).delete()
        
        for play in plays:
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
                    
                # Save players
                self._save_players(play.summary.home + play.summary.away, session)
            
            session.add(db_play)
            
    def _save_players(self, players: List[Player], session: Session):
        """Save or update player information"""
        for player in players:
            db_player = session.query(DBPlayer).filter_by(nfl_id=player.nfl_id).first()
            if not db_player:
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
                session.add(db_player)
            else:
                # Update existing player info
                db_player.team_id = player.team_id
                db_player.uniform_number = player.uniform_number
                db_player.position = player.position
                
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
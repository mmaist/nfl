#!/usr/bin/env python3
"""Analyze team performance statistics from the database."""

import argparse
import sys
import os
from sqlalchemy import create_engine, func, and_, or_, desc
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.database import DBGame, DBPlay

def analyze_team_stats(db_path: str = "nfl_data.db", team_id: str = None):
    """Analyze team performance statistics in the database."""
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    if team_id:
        print(f"\n=== Team Performance Analysis for {team_id} in {db_path} ===\n")
    else:
        print(f"\n=== League-Wide Team Performance Analysis for {db_path} ===\n")
    
    # 1. Overall Team Performance Rankings
    print("1. Team Performance Rankings:")
    
    if team_id:
        # Focus on specific team
        team_games = session.query(DBGame).filter(
            or_(DBGame.home_team_id == team_id, DBGame.away_team_id == team_id)
        ).all()
        
        if not team_games:
            print(f"  No games found for team: {team_id}")
            session.close()
            return
        
        # Calculate team-specific stats
        total_games = len(team_games)
        wins = 0
        total_points_scored = 0
        total_points_allowed = 0
        
        for game in team_games:
            is_home = game.home_team_id == team_id
            if is_home:
                points_scored = game.home_score_total
                points_allowed = game.away_score_total
                won = game.home_score_total > game.away_score_total
            else:
                points_scored = game.away_score_total
                points_allowed = game.home_score_total
                won = game.away_score_total > game.home_score_total
            
            if won:
                wins += 1
            total_points_scored += points_scored
            total_points_allowed += points_allowed
        
        win_pct = (wins / total_games * 100) if total_games > 0 else 0
        avg_points_scored = total_points_scored / total_games if total_games > 0 else 0
        avg_points_allowed = total_points_allowed / total_games if total_games > 0 else 0
        
        print(f"  {team_id} Season Stats:")
        print(f"    Record: {wins}-{total_games - wins} ({win_pct:.1f}%)")
        print(f"    Points Per Game: {avg_points_scored:.1f}")
        print(f"    Points Allowed Per Game: {avg_points_allowed:.1f}")
        print(f"    Point Differential: {avg_points_scored - avg_points_allowed:+.1f}")
        
    else:
        # League-wide analysis
        team_stats = session.query(
            DBGame.home_team_id.label('team_id'),
            func.avg(DBGame.home_team_points_per_game).label('avg_ppg'),
            func.avg(DBGame.home_team_points_allowed_per_game).label('avg_pag'),
            func.avg(DBGame.home_team_yards_per_game).label('avg_ypg'),
            func.avg(DBGame.home_team_yards_allowed_per_game).label('avg_yag')
        ).filter(
            DBGame.home_team_points_per_game.isnot(None)
        ).group_by(
            DBGame.home_team_id
        ).order_by(
            desc(func.avg(DBGame.home_team_points_per_game))
        ).limit(10).all()
        
        print("  Top 10 Offenses (Points Per Game):")
        for i, (team, ppg, pag, ypg, yag) in enumerate(team_stats, 1):
            print(f"    {i:2d}. {team}: {ppg:.1f} PPG, {ypg:.0f} YPG")
        
        # Top defenses
        def_stats = session.query(
            DBGame.home_team_id.label('team_id'),
            func.avg(DBGame.home_team_points_allowed_per_game).label('avg_pag'),
            func.avg(DBGame.home_team_yards_allowed_per_game).label('avg_yag')
        ).filter(
            DBGame.home_team_points_allowed_per_game.isnot(None)
        ).group_by(
            DBGame.home_team_id
        ).order_by(
            func.avg(DBGame.home_team_points_allowed_per_game)
        ).limit(10).all()
        
        print("\n  Top 10 Defenses (Points Allowed Per Game):")
        for i, (team, pag, yag) in enumerate(def_stats, 1):
            print(f"    {i:2d}. {team}: {pag:.1f} PAG, {yag:.0f} YAG")
    
    # 2. Offensive Efficiency Analysis
    print(f"\n2. Offensive Efficiency Analysis:")
    
    if team_id:
        # Get latest game for team stats
        latest_game = session.query(DBGame).filter(
            or_(DBGame.home_team_id == team_id, DBGame.away_team_id == team_id)
        ).order_by(desc(DBGame.date)).first()
        
        if latest_game:
            is_home = latest_game.home_team_id == team_id
            prefix = 'home_team_' if is_home else 'away_team_'
            
            stats = {
                'points_per_game': getattr(latest_game, f'{prefix}points_per_game'),
                'yards_per_game': getattr(latest_game, f'{prefix}yards_per_game'),
                'pass_yards_per_game': getattr(latest_game, f'{prefix}pass_yards_per_game'),
                'rush_yards_per_game': getattr(latest_game, f'{prefix}rush_yards_per_game'),
                'third_down_pct': getattr(latest_game, f'{prefix}third_down_pct'),
                'red_zone_pct': getattr(latest_game, f'{prefix}red_zone_pct'),
                'turnover_rate': getattr(latest_game, f'{prefix}turnover_rate')
            }
            
            print(f"  {team_id} Offensive Stats:")
            for stat_name, value in stats.items():
                if value is not None:
                    if 'pct' in stat_name:
                        print(f"    {stat_name.replace('_', ' ').title()}: {value:.1f}%")
                    elif 'rate' in stat_name:
                        print(f"    {stat_name.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"    {stat_name.replace('_', ' ').title()}: {value:.1f}")
    
    # 3. Defensive Performance Analysis
    print(f"\n3. Defensive Performance Analysis:")
    
    if team_id:
        if latest_game:
            def_stats = {
                'points_allowed_per_game': getattr(latest_game, f'{prefix}points_allowed_per_game'),
                'yards_allowed_per_game': getattr(latest_game, f'{prefix}yards_allowed_per_game'),
                'pass_yards_allowed_per_game': getattr(latest_game, f'{prefix}pass_yards_allowed_per_game'),
                'rush_yards_allowed_per_game': getattr(latest_game, f'{prefix}rush_yards_allowed_per_game'),
                'third_down_def_pct': getattr(latest_game, f'{prefix}third_down_def_pct'),
                'red_zone_def_pct': getattr(latest_game, f'{prefix}red_zone_def_pct'),
                'takeaway_rate': getattr(latest_game, f'{prefix}takeaway_rate'),
                'sacks_per_game': getattr(latest_game, f'{prefix}sacks_per_game')
            }
            
            print(f"  {team_id} Defensive Stats:")
            for stat_name, value in def_stats.items():
                if value is not None:
                    if 'pct' in stat_name:
                        print(f"    {stat_name.replace('_', ' ').title()}: {value:.1f}%")
                    elif 'rate' in stat_name:
                        print(f"    {stat_name.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"    {stat_name.replace('_', ' ').title()}: {value:.1f}")
    
    # 4. Recent Form Analysis
    print(f"\n4. Recent Form Analysis:")
    
    if team_id:
        if latest_game:
            recent_stats = {
                'last3_wins': getattr(latest_game, f'{prefix}last3_wins'),
                'last3_points_per_game': getattr(latest_game, f'{prefix}last3_points_per_game'),
                'last3_points_allowed': getattr(latest_game, f'{prefix}last3_points_allowed'),
                'last5_wins': getattr(latest_game, f'{prefix}last5_wins'),
                'last5_points_per_game': getattr(latest_game, f'{prefix}last5_points_per_game'),
                'last5_points_allowed': getattr(latest_game, f'{prefix}last5_points_allowed')
            }
            
            print(f"  {team_id} Recent Form:")
            l3_wins = recent_stats['last3_wins'] or 0
            l5_wins = recent_stats['last5_wins'] or 0
            print(f"    Last 3 Games: {l3_wins}-{3-l3_wins} record")
            if recent_stats['last3_points_per_game']:
                print(f"    Last 3 PPG: {recent_stats['last3_points_per_game']:.1f}")
                print(f"    Last 3 PAG: {recent_stats['last3_points_allowed']:.1f}")
            
            print(f"    Last 5 Games: {l5_wins}-{5-l5_wins} record")
            if recent_stats['last5_points_per_game']:
                print(f"    Last 5 PPG: {recent_stats['last5_points_per_game']:.1f}")
                print(f"    Last 5 PAG: {recent_stats['last5_points_allowed']:.1f}")
    
    # 5. Head-to-Head Analysis
    print(f"\n5. Head-to-Head Analysis:")
    
    if team_id:
        # Find recent opponents
        recent_matchups = session.query(DBGame).filter(
            or_(DBGame.home_team_id == team_id, DBGame.away_team_id == team_id)
        ).order_by(desc(DBGame.date)).limit(5).all()
        
        print(f"  {team_id} Recent Matchups:")
        for game in recent_matchups:
            opponent = game.away_team_id if game.home_team_id == team_id else game.home_team_id
            h2h_home_wins = game.head_to_head_home_wins or 0
            h2h_away_wins = game.head_to_head_away_wins or 0
            h2h_avg_points = game.head_to_head_avg_total_points or 0
            
            if h2h_home_wins > 0 or h2h_away_wins > 0:
                if game.home_team_id == team_id:
                    record = f"{h2h_home_wins}-{h2h_away_wins}"
                else:
                    record = f"{h2h_away_wins}-{h2h_home_wins}"
                print(f"    vs {opponent}: H2H {record}, Avg Total Points: {h2h_avg_points:.1f}")
    
    # 6. Performance Trends
    print(f"\n6. Performance Trends:")
    
    if team_id:
        # Get games in chronological order
        team_games_chrono = session.query(DBGame).filter(
            or_(DBGame.home_team_id == team_id, DBGame.away_team_id == team_id)
        ).order_by(DBGame.date).all()
        
        if len(team_games_chrono) >= 3:
            # Calculate trend over last few games
            recent_3 = team_games_chrono[-3:]
            points_trend = []
            
            for game in recent_3:
                is_home = game.home_team_id == team_id
                points = game.home_score_total if is_home else game.away_score_total
                points_trend.append(points)
            
            print(f"  {team_id} Last 3 Games Point Trend:")
            for i, points in enumerate(points_trend, 1):
                print(f"    Game -{3-i}: {points} points")
            
            # Simple trend analysis
            if len(points_trend) >= 2:
                if points_trend[-1] > points_trend[0]:
                    trend = "↗ Improving"
                elif points_trend[-1] < points_trend[0]:
                    trend = "↘ Declining"
                else:
                    trend = "→ Stable"
                print(f"    Trend: {trend}")
    
    # 7. League Comparisons
    if team_id:
        print(f"\n7. League Position Estimates:")
        
        if latest_game:
            # Compare against league averages
            league_avg_ppg = session.query(
                func.avg(DBGame.home_team_points_per_game)
            ).filter(
                DBGame.home_team_points_per_game.isnot(None)
            ).scalar()
            
            league_avg_pag = session.query(
                func.avg(DBGame.home_team_points_allowed_per_game)
            ).filter(
                DBGame.home_team_points_allowed_per_game.isnot(None)
            ).scalar()
            
            team_ppg = getattr(latest_game, f'{prefix}points_per_game') or 0
            team_pag = getattr(latest_game, f'{prefix}points_allowed_per_game') or 0
            
            if league_avg_ppg and league_avg_pag:
                print(f"  {team_id} vs League Average:")
                print(f"    PPG: {team_ppg:.1f} (League: {league_avg_ppg:.1f}) {'+' if team_ppg > league_avg_ppg else ''}{team_ppg - league_avg_ppg:.1f}")
                print(f"    PAG: {team_pag:.1f} (League: {league_avg_pag:.1f}) {'+' if team_pag > league_avg_pag else ''}{team_pag - league_avg_pag:.1f}")
    
    # 8. Statistical Correlations
    if not team_id:
        print(f"\n8. League-Wide Statistical Insights:")
        
        # Win correlation with various stats
        correlations = session.query(
            func.corr(DBGame.home_team_wins, DBGame.home_team_points_per_game).label('wins_ppg_corr'),
            func.corr(DBGame.home_team_wins, DBGame.home_team_points_allowed_per_game).label('wins_pag_corr'),
            func.corr(DBGame.home_team_wins, DBGame.home_team_turnover_rate).label('wins_to_corr')
        ).filter(
            and_(
                DBGame.home_team_wins.isnot(None),
                DBGame.home_team_points_per_game.isnot(None),
                DBGame.home_team_points_allowed_per_game.isnot(None)
            )
        ).first()
        
        if correlations and any(correlations):
            print("  Win Correlations:")
            if correlations.wins_ppg_corr:
                print(f"    Wins vs Points Per Game: {correlations.wins_ppg_corr:.3f}")
            if correlations.wins_pag_corr:
                print(f"    Wins vs Points Allowed: {correlations.wins_pag_corr:.3f}")
            if correlations.wins_to_corr:
                print(f"    Wins vs Turnover Rate: {correlations.wins_to_corr:.3f}")
    
    session.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze team performance statistics in NFL database')
    parser.add_argument('--db-path', default='nfl_data.db',
                        help='Path to the SQLite database file')
    parser.add_argument('--team-id', type=str,
                        help='Specific team ID to analyze (e.g., "LAR", "KC")')
    
    args = parser.parse_args()
    analyze_team_stats(args.db_path, args.team_id)

if __name__ == "__main__":
    main()
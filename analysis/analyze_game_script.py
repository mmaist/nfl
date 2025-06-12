#!/usr/bin/env python3
"""Analyze game script and context features from the database."""

import argparse
import sys
import os
from sqlalchemy import create_engine, func, and_, or_, case
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt
import pandas as pd

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.database import DBGame, DBPlay

def analyze_game_script(db_path: str = "nfl_data.db"):
    """Analyze game script and context features in the database."""
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"\n=== Game Script & Context Analysis for {db_path} ===\n")
    
    # 1. Drive Analysis
    print("1. Drive Statistics:")
    
    # Average drive length
    drive_stats = session.query(
        func.avg(DBPlay.drive_plays_so_far).label('avg_plays_per_drive'),
        func.max(DBPlay.drive_plays_so_far).label('longest_drive'),
        func.min(DBPlay.drive_plays_so_far).label('shortest_drive')
    ).filter(
        DBPlay.drive_plays_so_far.isnot(None)
    ).first()
    
    if drive_stats:
        print(f"  Average Plays per Drive: {drive_stats.avg_plays_per_drive:.1f}")
        print(f"  Longest Drive: {drive_stats.longest_drive} plays")
        print(f"  Shortest Drive: {drive_stats.shortest_drive} play(s)")
    
    # Drive success by starting field position
    print("\n  Drive Success by Starting Field Position:")
    drive_success = session.query(
        case(
            [(DBPlay.drive_start_yardline <= 20, 'Own 20 or worse'),
             (DBPlay.drive_start_yardline <= 50, 'Own 21-50'),
             (DBPlay.drive_start_yardline <= 80, 'Opponent 50-21'),
             (DBPlay.drive_start_yardline > 80, 'Red Zone Start')],
            else_='Unknown'
        ).label('field_position'),
        func.count(DBPlay.id).label('total_drives'),
        func.sum(
            case([(or_(DBPlay.is_touchdown_pass == True, 
                      DBPlay.is_touchdown_run == True,
                      DBPlay.is_field_goal == True), 1)], else_=0)
        ).label('scoring_drives')
    ).filter(
        DBPlay.drive_play_number == 1,  # First play of drive
        DBPlay.drive_start_yardline.isnot(None)
    ).group_by(
        case(
            [(DBPlay.drive_start_yardline <= 20, 'Own 20 or worse'),
             (DBPlay.drive_start_yardline <= 50, 'Own 21-50'),
             (DBPlay.drive_start_yardline <= 80, 'Opponent 50-21'),
             (DBPlay.drive_start_yardline > 80, 'Red Zone Start')],
            else_='Unknown'
        )
    ).all()
    
    for field_pos, total, scoring in drive_success:
        success_rate = (scoring / total * 100) if total > 0 else 0
        print(f"    {field_pos}: {scoring}/{total} ({success_rate:.1f}%)")
    
    # 2. Game Script Analysis
    print("\n2. Game Script Analysis:")
    
    # Win probability in different scenarios
    scenarios = [
        ('Winning by 1-7', and_(DBPlay.is_winning_team == True, DBPlay.score_differential.between(1, 7))),
        ('Winning by 8-14', and_(DBPlay.is_winning_team == True, DBPlay.score_differential.between(8, 14))),
        ('Winning by 15+', and_(DBPlay.is_winning_team == True, DBPlay.score_differential >= 15)),
        ('Losing by 1-7', and_(DBPlay.is_losing_team == True, DBPlay.score_differential.between(-7, -1))),
        ('Losing by 8-14', and_(DBPlay.is_losing_team == True, DBPlay.score_differential.between(-14, -8))),
        ('Losing by 15+', and_(DBPlay.is_losing_team == True, DBPlay.score_differential <= -15))
    ]
    
    for scenario_name, condition in scenarios:
        play_count = session.query(func.count(DBPlay.id)).filter(condition).scalar()
        
        # Rush percentage in this scenario
        rush_count = session.query(func.count(DBPlay.id)).filter(
            and_(condition, DBPlay.play_type.like('%rush%'))
        ).scalar()
        
        rush_pct = (rush_count / play_count * 100) if play_count > 0 else 0
        print(f"  {scenario_name}: {play_count} plays, {rush_pct:.1f}% rush")
    
    # 3. Comeback Situations
    print("\n3. Comeback Situation Analysis:")
    
    comeback_plays = session.query(func.count(DBPlay.id)).filter(
        DBPlay.is_comeback_situation == True
    ).scalar()
    
    comeback_success = session.query(func.count(DBPlay.id)).filter(
        and_(DBPlay.is_comeback_situation == True,
             or_(DBPlay.is_touchdown_pass == True,
                 DBPlay.is_touchdown_run == True))
    ).scalar()
    
    print(f"  Total Comeback Situation Plays: {comeback_plays}")
    print(f"  Touchdown Plays in Comeback: {comeback_success}")
    
    if comeback_plays > 0:
        success_rate = comeback_success / comeback_plays * 100
        print(f"  Comeback TD Rate: {success_rate:.1f}%")
    
    # 4. Blowout Analysis
    print("\n4. Blowout Game Analysis:")
    
    blowout_plays = session.query(func.count(DBPlay.id)).filter(
        DBPlay.is_blowout_situation == True
    ).scalar()
    
    blowout_rush = session.query(func.count(DBPlay.id)).filter(
        and_(DBPlay.is_blowout_situation == True,
             DBPlay.play_type.like('%rush%'))
    ).scalar()
    
    print(f"  Total Blowout Plays: {blowout_plays}")
    if blowout_plays > 0:
        rush_pct = blowout_rush / blowout_plays * 100
        print(f"  Rush Percentage in Blowouts: {rush_pct:.1f}%")
    
    # 5. Momentum Analysis
    print("\n5. Momentum Indicators:")
    
    # Turnover margin impact
    turnover_scenarios = [
        ('Turnover Advantage (+2 or more)', DBPlay.turnover_margin >= 2),
        ('Even Turnovers (0 to +1)', DBPlay.turnover_margin.between(0, 1)),
        ('Turnover Disadvantage (-2 or worse)', DBPlay.turnover_margin <= -2)
    ]
    
    for scenario_name, condition in turnover_scenarios:
        play_count = session.query(func.count(DBPlay.id)).filter(
            and_(condition, DBPlay.turnover_margin.isnot(None))
        ).scalar()
        
        scoring_plays = session.query(func.count(DBPlay.id)).filter(
            and_(condition,
                 DBPlay.turnover_margin.isnot(None),
                 or_(DBPlay.is_touchdown_pass == True,
                     DBPlay.is_touchdown_run == True,
                     DBPlay.is_field_goal == True))
        ).scalar()
        
        if play_count > 0:
            scoring_rate = scoring_plays / play_count * 100
            print(f"  {scenario_name}: {play_count} plays, {scoring_rate:.2f}% scoring rate")
    
    # 6. Two-Minute Drill Analysis
    print("\n6. Two-Minute Drill Analysis:")
    
    two_min_plays = session.query(func.count(DBPlay.id)).filter(
        DBPlay.is_two_minute_drill == True
    ).scalar()
    
    two_min_pass = session.query(func.count(DBPlay.id)).filter(
        and_(DBPlay.is_two_minute_drill == True,
             DBPlay.play_type.like('%pass%'))
    ).scalar()
    
    two_min_complete = session.query(func.count(DBPlay.id)).filter(
        and_(DBPlay.is_two_minute_drill == True,
             DBPlay.is_complete_pass == True)
    ).scalar()
    
    print(f"  Total Two-Minute Drill Plays: {two_min_plays}")
    if two_min_plays > 0:
        pass_pct = two_min_pass / two_min_plays * 100
        print(f"  Pass Percentage: {pass_pct:.1f}%")
        
        if two_min_pass > 0:
            completion_pct = two_min_complete / two_min_pass * 100
            print(f"  Pass Completion Rate: {completion_pct:.1f}%")
    
    # 7. Timeout Management
    print("\n7. Timeout Management:")
    
    timeout_scenarios = [
        ('Timeout Advantage (+2 or more)', DBPlay.timeout_advantage >= 2),
        ('Even Timeouts (0 to +1)', DBPlay.timeout_advantage.between(0, 1)),
        ('Timeout Disadvantage (-2 or worse)', DBPlay.timeout_advantage <= -2)
    ]
    
    for scenario_name, condition in timeout_scenarios:
        play_count = session.query(func.count(DBPlay.id)).filter(
            and_(condition, DBPlay.timeout_advantage.isnot(None))
        ).scalar()
        
        print(f"  {scenario_name}: {play_count} plays")
    
    # 8. Weather Impact
    print("\n8. Weather Impact Analysis:")
    
    weather_conditions = [
        ('Indoor Games', DBPlay.is_indoor_game == True),
        ('High Weather Impact (>0.5)', DBPlay.weather_impact_score > 0.5),
        ('Moderate Weather Impact (0.2-0.5)', DBPlay.weather_impact_score.between(0.2, 0.5)),
        ('Low Weather Impact (<0.2)', DBPlay.weather_impact_score < 0.2)
    ]
    
    for condition_name, condition in weather_conditions:
        play_count = session.query(func.count(DBPlay.id)).filter(condition).scalar()
        
        if play_count > 0:
            pass_plays = session.query(func.count(DBPlay.id)).filter(
                and_(condition, DBPlay.play_type.like('%pass%'))
            ).scalar()
            
            pass_pct = pass_plays / play_count * 100 if play_count > 0 else 0
            print(f"  {condition_name}: {play_count} plays, {pass_pct:.1f}% pass")
    
    # 9. Field Position Analysis
    print("\n9. Field Position Impact:")
    
    field_positions = [
        ('Own Territory', DBPlay.field_position_category == 'own_territory'),
        ('Midfield', DBPlay.field_position_category == 'midfield'),
        ('Opponent Territory', DBPlay.field_position_category == 'opponent_territory'),
        ('Red Zone', DBPlay.field_position_category == 'red_zone')
    ]
    
    for pos_name, condition in field_positions:
        play_count = session.query(func.count(DBPlay.id)).filter(condition).scalar()
        
        if play_count > 0:
            pass_plays = session.query(func.count(DBPlay.id)).filter(
                and_(condition, DBPlay.play_type.like('%pass%'))
            ).scalar()
            
            scoring_plays = session.query(func.count(DBPlay.id)).filter(
                and_(condition,
                     or_(DBPlay.is_touchdown_pass == True,
                         DBPlay.is_touchdown_run == True))
            ).scalar()
            
            pass_pct = pass_plays / play_count * 100
            scoring_pct = scoring_plays / play_count * 100
            
            print(f"  {pos_name}: {play_count} plays, {pass_pct:.1f}% pass, {scoring_pct:.1f}% TD")
    
    # 10. Competitive Game Index
    print("\n10. Game Competitiveness:")
    
    competitive_ranges = [
        ('Very Competitive (>0.8)', DBPlay.game_competitive_index > 0.8),
        ('Competitive (0.6-0.8)', DBPlay.game_competitive_index.between(0.6, 0.8)),
        ('Somewhat Competitive (0.4-0.6)', DBPlay.game_competitive_index.between(0.4, 0.6)),
        ('Not Competitive (<0.4)', DBPlay.game_competitive_index < 0.4)
    ]
    
    for comp_name, condition in competitive_ranges:
        play_count = session.query(func.count(DBPlay.id)).filter(
            and_(condition, DBPlay.game_competitive_index.isnot(None))
        ).scalar()
        
        if play_count > 0:
            avg_score_diff = session.query(func.avg(func.abs(DBPlay.score_differential))).filter(
                and_(condition, DBPlay.game_competitive_index.isnot(None))
            ).scalar()
            
            print(f"  {comp_name}: {play_count} plays, avg score diff: {avg_score_diff:.1f}")
    
    session.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze game script and context features in NFL database')
    parser.add_argument('--db-path', default='nfl_data.db',
                        help='Path to the SQLite database file')
    
    args = parser.parse_args()
    analyze_game_script(args.db_path)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Analyze play result metrics from the database."""

import argparse
import sys
import os
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.database import DBGame, DBPlay

def analyze_play_results(db_path: str = "nfl_data.db"):
    """Analyze play result metrics in the database."""
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"\n=== Play Result Analysis for {db_path} ===\n")
    
    # 1. Pass Play Analysis
    print("1. Pass Play Completion Rate:")
    pass_stats = session.query(
        func.count(DBPlay.id).label('total_passes'),
        func.sum(DBPlay.is_complete_pass.cast(type_=int)).label('completions')
    ).filter(
        DBPlay.is_complete_pass.isnot(None)
    ).first()
    
    if pass_stats.total_passes > 0:
        completion_rate = (pass_stats.completions / pass_stats.total_passes * 100)
        print(f"  Total Passes: {pass_stats.total_passes}")
        print(f"  Completions: {pass_stats.completions}")
        print(f"  Completion Rate: {completion_rate:.1f}%")
    
    # 2. Pass Targets Analysis
    print("\n2. Top Pass Targets:")
    targets = session.query(
        DBPlay.pass_target,
        func.count(DBPlay.id).label('targets'),
        func.sum(DBPlay.is_complete_pass.cast(type_=int)).label('catches')
    ).filter(
        DBPlay.pass_target.isnot(None)
    ).group_by(
        DBPlay.pass_target
    ).order_by(
        func.count(DBPlay.id).desc()
    ).limit(10).all()
    
    for target, target_count, catches in targets:
        catch_rate = (catches / target_count * 100) if target_count > 0 else 0
        print(f"  {target}: {target_count} targets, {catches} catches ({catch_rate:.1f}%)")
    
    # 3. Sack Analysis
    print("\n3. Sack Analysis:")
    sack_stats = session.query(
        func.count(DBPlay.id).label('total_sacks'),
        func.avg(DBPlay.sack_yards).label('avg_sack_yards')
    ).filter(
        DBPlay.is_sack == True
    ).first()
    
    print(f"  Total Sacks: {sack_stats.total_sacks}")
    if sack_stats.avg_sack_yards:
        print(f"  Average Sack Yards: {sack_stats.avg_sack_yards:.1f}")
    
    # 4. Turnover Analysis
    print("\n4. Turnover Analysis:")
    turnovers = session.query(
        func.count(DBPlay.id).label('total_turnovers')
    ).filter(
        DBPlay.is_turnover == True
    ).first()
    
    interceptions = session.query(
        func.count(DBPlay.id).label('total_ints')
    ).filter(
        DBPlay.is_interception == True
    ).first()
    
    fumbles = session.query(
        func.count(DBPlay.id).label('total_fumbles')
    ).filter(
        DBPlay.is_fumble == True
    ).first()
    
    print(f"  Total Turnovers: {turnovers.total_turnovers}")
    print(f"  Interceptions: {interceptions.total_ints}")
    print(f"  Fumbles: {fumbles.total_fumbles}")
    
    # 5. Run Gap Analysis
    print("\n5. Run Gap Distribution:")
    run_gaps = session.query(
        DBPlay.run_gap,
        func.count(DBPlay.id).label('count'),
        func.avg(DBPlay.yards_gained).label('avg_yards')
    ).filter(
        DBPlay.run_gap.isnot(None)
    ).group_by(
        DBPlay.run_gap
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    for gap, count, avg_yards in run_gaps:
        avg_str = f"{avg_yards:.1f}" if avg_yards else "N/A"
        print(f"  {gap}: {count} runs, {avg_str} avg yards")
    
    # 6. Touchdown Analysis
    print("\n6. Touchdown Analysis:")
    td_passes = session.query(
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.is_touchdown_pass == True
    ).first()
    
    td_runs = session.query(
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.is_touchdown_run == True
    ).first()
    
    print(f"  Touchdown Passes: {td_passes.count}")
    print(f"  Touchdown Runs: {td_runs.count}")
    
    # 7. Penalty Analysis
    print("\n7. Penalty Analysis:")
    penalty_types = session.query(
        DBPlay.penalty_type,
        func.count(DBPlay.id).label('count'),
        func.avg(DBPlay.penalty_yards).label('avg_yards')
    ).filter(
        DBPlay.penalty_type.isnot(None)
    ).group_by(
        DBPlay.penalty_type
    ).order_by(
        func.count(DBPlay.id).desc()
    ).limit(10).all()
    
    for ptype, count, avg_yards in penalty_types:
        avg_str = f"{avg_yards:.1f}" if avg_yards else "N/A"
        print(f"  {ptype}: {count} penalties, {avg_str} avg yards")
    
    # 8. Special Teams Analysis
    print("\n8. Special Teams Analysis:")
    
    # Field Goals
    fg_stats = session.query(
        DBPlay.field_goal_result,
        func.count(DBPlay.id).label('count'),
        func.avg(DBPlay.field_goal_distance).label('avg_distance')
    ).filter(
        DBPlay.is_field_goal == True
    ).group_by(
        DBPlay.field_goal_result
    ).all()
    
    print("\n  Field Goal Results:")
    for result, count, avg_dist in fg_stats:
        avg_str = f"{avg_dist:.1f}" if avg_dist else "N/A"
        print(f"    {result}: {count} attempts, {avg_str} avg distance")
    
    # Punts
    punt_stats = session.query(
        func.count(DBPlay.id).label('total_punts'),
        func.avg(DBPlay.punt_distance).label('avg_distance')
    ).filter(
        DBPlay.is_punt == True
    ).first()
    
    print(f"\n  Punting:")
    print(f"    Total Punts: {punt_stats.total_punts}")
    if punt_stats.avg_distance:
        print(f"    Average Distance: {punt_stats.avg_distance:.1f} yards")
    
    # 9. Situational Analysis
    print("\n9. Third Down Conversion Analysis:")
    
    # Third down attempts
    third_down_attempts = session.query(
        func.count(DBPlay.id).label('attempts')
    ).filter(
        DBPlay.down == 3
    ).first()
    
    # Third down conversions (first downs)
    third_down_conversions = session.query(
        func.count(DBPlay.id).label('conversions')
    ).filter(
        and_(DBPlay.down == 3, DBPlay.is_first_down == True)
    ).first()
    
    if third_down_attempts.attempts > 0:
        conversion_rate = (third_down_conversions.conversions / third_down_attempts.attempts * 100)
        print(f"  Third Down Attempts: {third_down_attempts.attempts}")
        print(f"  Third Down Conversions: {third_down_conversions.conversions}")
        print(f"  Conversion Rate: {conversion_rate:.1f}%")
    
    # 10. Red Zone Analysis
    print("\n10. Red Zone Efficiency:")
    
    rz_attempts = session.query(
        func.count(DBPlay.id).label('attempts')
    ).filter(
        DBPlay.is_redzone_play == True
    ).first()
    
    rz_touchdowns = session.query(
        func.count(DBPlay.id).label('tds')
    ).filter(
        and_(DBPlay.is_redzone_play == True, 
             or_(DBPlay.is_touchdown_pass == True, DBPlay.is_touchdown_run == True))
    ).first()
    
    if rz_attempts.attempts > 0:
        td_rate = (rz_touchdowns.tds / rz_attempts.attempts * 100)
        print(f"  Red Zone Attempts: {rz_attempts.attempts}")
        print(f"  Red Zone Touchdowns: {rz_touchdowns.tds}")
        print(f"  TD Rate: {td_rate:.1f}%")
    
    session.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze play result metrics in NFL database')
    parser.add_argument('--db-path', default='nfl_data.db',
                        help='Path to the SQLite database file')
    
    args = parser.parse_args()
    analyze_play_results(args.db_path)

if __name__ == "__main__":
    main()
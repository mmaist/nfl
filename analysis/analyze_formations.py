#!/usr/bin/env python3
"""Analyze offensive and defensive formation tendencies from the database."""

import argparse
import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from collections import defaultdict
import pandas as pd

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.database import DBGame, DBPlay

def analyze_formations(db_path: str = "nfl_data.db"):
    """Analyze formation tendencies in the database."""
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"\n=== Formation Analysis for {db_path} ===\n")
    
    # 1. Offensive Formation Distribution
    print("1. Offensive Formation Distribution:")
    off_formations = session.query(
        DBPlay.offensive_formation,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.offensive_formation.isnot(None)
    ).group_by(
        DBPlay.offensive_formation
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    total_off_plays = sum(f.count for f in off_formations)
    for formation, count in off_formations:
        pct = (count / total_off_plays * 100) if total_off_plays > 0 else 0
        print(f"  {formation}: {count} ({pct:.1f}%)")
    
    # 2. Defensive Package Distribution
    print("\n2. Defensive Package Distribution:")
    def_packages = session.query(
        DBPlay.defensive_package,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.defensive_package.isnot(None)
    ).group_by(
        DBPlay.defensive_package
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    total_def_plays = sum(p.count for p in def_packages)
    for package, count in def_packages:
        pct = (count / total_def_plays * 100) if total_def_plays > 0 else 0
        print(f"  {package}: {count} ({pct:.1f}%)")
    
    # 3. Defensive Formation Distribution
    print("\n3. Defensive Formation Distribution:")
    def_formations = session.query(
        DBPlay.defensive_formation,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.defensive_formation.isnot(None)
    ).group_by(
        DBPlay.defensive_formation
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    for formation, count in def_formations:
        print(f"  {formation}: {count}")
    
    # 4. Box Count Distribution
    print("\n4. Defensive Box Count Distribution:")
    box_counts = session.query(
        DBPlay.defensive_box_count,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.defensive_box_count.isnot(None)
    ).group_by(
        DBPlay.defensive_box_count
    ).order_by(
        DBPlay.defensive_box_count
    ).all()
    
    for box_count, count in box_counts:
        print(f"  {box_count} in the box: {count}")
    
    # 5. Formation by Down
    print("\n5. Offensive Formation by Down:")
    for down in [1, 2, 3, 4]:
        print(f"\n  {down}st/nd/rd/th Down:")
        down_formations = session.query(
            DBPlay.offensive_formation,
            func.count(DBPlay.id).label('count')
        ).filter(
            DBPlay.down == down,
            DBPlay.offensive_formation.isnot(None)
        ).group_by(
            DBPlay.offensive_formation
        ).order_by(
            func.count(DBPlay.id).desc()
        ).limit(3).all()
        
        for formation, count in down_formations:
            print(f"    {formation}: {count}")
    
    # 6. Defensive Package by Down and Distance
    print("\n6. Defensive Package by Down and Distance:")
    
    # 3rd and long (7+ yards)
    third_long = session.query(
        DBPlay.defensive_package,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.down == 3,
        DBPlay.yards_to_go >= 7,
        DBPlay.defensive_package.isnot(None)
    ).group_by(
        DBPlay.defensive_package
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    print("\n  3rd and Long (7+ yards):")
    for package, count in third_long:
        print(f"    {package}: {count}")
    
    # 3rd and short (3 or less)
    third_short = session.query(
        DBPlay.defensive_package,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.down == 3,
        DBPlay.yards_to_go <= 3,
        DBPlay.defensive_package.isnot(None)
    ).group_by(
        DBPlay.defensive_package
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    print("\n  3rd and Short (3 or less yards):")
    for package, count in third_short:
        print(f"    {package}: {count}")
    
    # 7. Red Zone Tendencies
    print("\n7. Red Zone Formation Tendencies:")
    
    # Offensive formations in red zone
    rz_off = session.query(
        DBPlay.offensive_formation,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.is_redzone_play == True,
        DBPlay.offensive_formation.isnot(None)
    ).group_by(
        DBPlay.offensive_formation
    ).order_by(
        func.count(DBPlay.id).desc()
    ).limit(5).all()
    
    print("\n  Offensive Formations in Red Zone:")
    for formation, count in rz_off:
        print(f"    {formation}: {count}")
    
    # Defensive packages in red zone
    rz_def = session.query(
        DBPlay.defensive_package,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.is_redzone_play == True,
        DBPlay.defensive_package.isnot(None)
    ).group_by(
        DBPlay.defensive_package
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    print("\n  Defensive Packages in Red Zone:")
    for package, count in rz_def:
        print(f"    {package}: {count}")
    
    # 8. Two-Minute Drill Tendencies
    print("\n8. Two-Minute Drill Tendencies:")
    
    two_min_off = session.query(
        DBPlay.offensive_formation,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.is_two_minute_drill == True,
        DBPlay.offensive_formation.isnot(None)
    ).group_by(
        DBPlay.offensive_formation
    ).order_by(
        func.count(DBPlay.id).desc()
    ).limit(3).all()
    
    print("\n  Top Offensive Formations:")
    for formation, count in two_min_off:
        print(f"    {formation}: {count}")
    
    two_min_def = session.query(
        DBPlay.defensive_package,
        func.count(DBPlay.id).label('count')
    ).filter(
        DBPlay.is_two_minute_drill == True,
        DBPlay.defensive_package.isnot(None)
    ).group_by(
        DBPlay.defensive_package
    ).order_by(
        func.count(DBPlay.id).desc()
    ).all()
    
    print("\n  Defensive Packages:")
    for package, count in two_min_def:
        print(f"    {package}: {count}")
    
    session.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze formation tendencies in NFL database')
    parser.add_argument('--db-path', default='nfl_data.db',
                        help='Path to the SQLite database file')
    
    args = parser.parse_args()
    analyze_formations(args.db_path)

if __name__ == "__main__":
    main()
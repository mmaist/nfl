#!/usr/bin/env python3
"""Quick script to check if play stats are being saved"""

from db_utils import NFLDatabaseManager
from database import DBPlay
import json

# Connect to database
db = NFLDatabaseManager("nfl_data.db")
session = db.db.get_session()

# Get a sample play with stats
play = session.query(DBPlay).filter(
    DBPlay.play_stats_json != None
).first()

if play:
    print(f"Play ID: {play.play_id}")
    print(f"Description: {play.play_description[:100]}...")
    if play.play_stats_json:
        print(f"Number of stats: {len(play.play_stats_json)}")
        print(f"Stats JSON: {json.dumps(play.play_stats_json, indent=2)}")
else:
    print("No plays with stats found")

# Also check total counts
total_plays = session.query(DBPlay).count()
plays_with_stats = session.query(DBPlay).filter(
    DBPlay.play_stats_json != None
).count()

print(f"\nTotal plays: {total_plays}")
print(f"Plays with stats: {plays_with_stats}")

session.close()
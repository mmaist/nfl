#!/usr/bin/env python3
"""Debug script to check if play stats are in the API response"""

import json
import os
from dotenv import load_dotenv
from scrapeVideos import NFLGameScraper

load_dotenv()

# Create scraper
scraper = NFLGameScraper(api_only=True, skip_play_summaries=False)

# Get one play summary to check structure
game_id = "7d4019ca-1312-11ef-afd1-646009f18b2e"
play_id = 1398  # First play from the game

print(f"Fetching play summary for game {game_id}, play {play_id}")
summary = scraper.get_play_summary(game_id, play_id)

if summary and summary.play:
    print(f"\nPlay description: {summary.play.play_description[:100]}...")
    
    if hasattr(summary.play, 'play_stats') and summary.play.play_stats:
        print(f"Number of play stats: {len(summary.play.play_stats)}")
        for stat in summary.play.play_stats[:3]:  # Show first 3 stats
            print(f"  - {stat.player_name}: stat_id={stat.stat_id}, yards={stat.yards}")
    else:
        print("No play_stats found in the response")
        
    # Save full response for inspection
    with open('debug_play_summary.json', 'w') as f:
        json.dump(summary.model_dump(by_alias=True), f, indent=2)
    print("\nFull response saved to debug_play_summary.json")
else:
    print("Failed to fetch play summary")
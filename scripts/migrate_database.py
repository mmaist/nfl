#!/usr/bin/env python3
"""
Database Migration Script for NFL Data Scraper

This script migrates an existing SQLite database to add new columns that were added
to the DBGame, DBPlay, and DBPlayer models during recent feature enhancements.

The script is idempotent - it can be run multiple times safely as it checks for
existing columns before attempting to add them.

Usage:
    python scripts/migrate_database.py [--db-path path/to/database.db] [--dry-run]
"""

import sqlite3
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class DatabaseMigrator:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.conn = None
        
    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            print(f"✓ Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"✗ Error connecting to database: {e}")
            sys.exit(1)
            
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def get_existing_columns(self, table_name: str) -> List[str]:
        """Get list of existing columns for a table"""
        cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return columns
        
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        existing_columns = self.get_existing_columns(table_name)
        return column_name in existing_columns
        
    def add_column(self, table_name: str, column_name: str, column_type: str, default_value: Any = None):
        """Add a column to a table if it doesn't exist"""
        if self.column_exists(table_name, column_name):
            print(f"  ⚠ Column '{column_name}' already exists in '{table_name}' - skipping")
            return False
            
        # Construct ALTER TABLE statement
        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            if isinstance(default_value, str):
                alter_sql += f" DEFAULT '{default_value}'"
            elif isinstance(default_value, bool):
                alter_sql += f" DEFAULT {1 if default_value else 0}"
            else:
                alter_sql += f" DEFAULT {default_value}"
                
        if self.dry_run:
            print(f"  [DRY RUN] Would execute: {alter_sql}")
            return True
        else:
            try:
                self.conn.execute(alter_sql)
                self.conn.commit()
                print(f"  ✓ Added column '{column_name}' to '{table_name}'")
                return True
            except sqlite3.Error as e:
                print(f"  ✗ Error adding column '{column_name}' to '{table_name}': {e}")
                return False
                
    def migrate_games_table(self):
        """Migrate the games table with new columns"""
        print("\n🔄 Migrating 'games' table...")
        
        # Weather data columns
        weather_columns = [
            ("weather_temperature", "FLOAT"),
            ("weather_wind_speed", "FLOAT"),
            ("weather_wind_direction", "VARCHAR"),
            ("weather_precipitation", "VARCHAR"),
            ("weather_humidity", "FLOAT"),
            ("weather_conditions", "VARCHAR"),
        ]
        
        # Team statistics columns
        team_stat_columns = [
            ("home_team_wins", "INTEGER"),
            ("home_team_losses", "INTEGER"),
            ("home_team_win_streak", "INTEGER"),
            ("home_team_offensive_rank", "INTEGER"),
            ("home_team_defensive_rank", "INTEGER"),
            ("away_team_wins", "INTEGER"),
            ("away_team_losses", "INTEGER"),
            ("away_team_win_streak", "INTEGER"),
            ("away_team_offensive_rank", "INTEGER"),
            ("away_team_defensive_rank", "INTEGER"),
        ]
        
        # Home team offensive stats
        home_offense_columns = [
            ("home_team_points_per_game", "FLOAT"),
            ("home_team_yards_per_game", "FLOAT"),
            ("home_team_pass_yards_per_game", "FLOAT"),
            ("home_team_rush_yards_per_game", "FLOAT"),
            ("home_team_third_down_pct", "FLOAT"),
            ("home_team_red_zone_pct", "FLOAT"),
            ("home_team_turnover_rate", "FLOAT"),
            ("home_team_time_of_possession", "FLOAT"),
        ]
        
        # Home team defensive stats
        home_defense_columns = [
            ("home_team_points_allowed_per_game", "FLOAT"),
            ("home_team_yards_allowed_per_game", "FLOAT"),
            ("home_team_pass_yards_allowed_per_game", "FLOAT"),
            ("home_team_rush_yards_allowed_per_game", "FLOAT"),
            ("home_team_third_down_def_pct", "FLOAT"),
            ("home_team_red_zone_def_pct", "FLOAT"),
            ("home_team_takeaway_rate", "FLOAT"),
            ("home_team_sacks_per_game", "FLOAT"),
        ]
        
        # Away team offensive stats
        away_offense_columns = [
            ("away_team_points_per_game", "FLOAT"),
            ("away_team_yards_per_game", "FLOAT"),
            ("away_team_pass_yards_per_game", "FLOAT"),
            ("away_team_rush_yards_per_game", "FLOAT"),
            ("away_team_third_down_pct", "FLOAT"),
            ("away_team_red_zone_pct", "FLOAT"),
            ("away_team_turnover_rate", "FLOAT"),
            ("away_team_time_of_possession", "FLOAT"),
        ]
        
        # Away team defensive stats
        away_defense_columns = [
            ("away_team_points_allowed_per_game", "FLOAT"),
            ("away_team_yards_allowed_per_game", "FLOAT"),
            ("away_team_pass_yards_allowed_per_game", "FLOAT"),
            ("away_team_rush_yards_allowed_per_game", "FLOAT"),
            ("away_team_third_down_def_pct", "FLOAT"),
            ("away_team_red_zone_def_pct", "FLOAT"),
            ("away_team_takeaway_rate", "FLOAT"),
            ("away_team_sacks_per_game", "FLOAT"),
        ]
        
        # Recent form columns (last 3 games)
        last3_columns = [
            ("home_team_last3_wins", "INTEGER"),
            ("home_team_last3_points_per_game", "FLOAT"),
            ("home_team_last3_points_allowed", "FLOAT"),
            ("away_team_last3_wins", "INTEGER"),
            ("away_team_last3_points_per_game", "FLOAT"),
            ("away_team_last3_points_allowed", "FLOAT"),
        ]
        
        # Recent form columns (last 5 games)
        last5_columns = [
            ("home_team_last5_wins", "INTEGER"),
            ("home_team_last5_points_per_game", "FLOAT"),
            ("home_team_last5_points_allowed", "FLOAT"),
            ("away_team_last5_wins", "INTEGER"),
            ("away_team_last5_points_per_game", "FLOAT"),
            ("away_team_last5_points_allowed", "FLOAT"),
        ]
        
        # Head-to-head stats
        h2h_columns = [
            ("head_to_head_home_wins", "INTEGER"),
            ("head_to_head_away_wins", "INTEGER"),
            ("head_to_head_avg_total_points", "FLOAT"),
        ]
        
        # Combine all columns
        all_columns = (weather_columns + team_stat_columns + home_offense_columns + 
                      home_defense_columns + away_offense_columns + away_defense_columns +
                      last3_columns + last5_columns + h2h_columns)
        
        added_count = 0
        for column_name, column_type in all_columns:
            if self.add_column("games", column_name, column_type):
                added_count += 1
                
        print(f"✓ Games table migration complete: {added_count} columns added")
        
    def migrate_plays_table(self):
        """Migrate the plays table with new columns"""
        print("\n🔄 Migrating 'plays' table...")
        
        # Formation and play details
        formation_columns = [
            ("offensive_formation", "VARCHAR"),
            ("defensive_formation", "VARCHAR"),
            ("yards_gained", "INTEGER"),
            ("pass_length", "VARCHAR"),
            ("pass_location", "VARCHAR"),
            ("run_direction", "VARCHAR"),
        ]
        
        # Defensive personnel details
        defensive_personnel_columns = [
            ("defensive_package", "VARCHAR"),
            ("defensive_db_count", "INTEGER"),
            ("defensive_lb_count", "INTEGER"),
            ("defensive_dl_count", "INTEGER"),
            ("defensive_box_count", "INTEGER"),
        ]
        
        # Game context features
        game_context_columns = [
            ("score_differential", "INTEGER"),
            ("time_remaining_half", "INTEGER"),
            ("time_remaining_game", "INTEGER"),
            ("is_two_minute_drill", "BOOLEAN", False),
            ("is_must_score_situation", "BOOLEAN", False),
        ]
        
        # Drive context
        drive_context_columns = [
            ("drive_number", "INTEGER"),
            ("drive_play_number", "INTEGER"),
            ("drive_start_yardline", "INTEGER"),
            ("drive_time_of_possession", "INTEGER"),
            ("drive_plays_so_far", "INTEGER"),
        ]
        
        # Game script features
        game_script_columns = [
            ("is_winning_team", "BOOLEAN"),
            ("is_losing_team", "BOOLEAN"),
            ("is_comeback_situation", "BOOLEAN"),
            ("is_blowout_situation", "BOOLEAN"),
            ("game_competitive_index", "FLOAT"),
        ]
        
        # Momentum indicators
        momentum_columns = [
            ("possessing_team_last_score", "INTEGER"),
            ("opposing_team_last_score", "INTEGER"),
            ("possessing_team_turnovers", "INTEGER"),
            ("opposing_team_turnovers", "INTEGER"),
            ("turnover_margin", "INTEGER"),
        ]
        
        # Timeout context
        timeout_columns = [
            ("possessing_team_timeouts", "INTEGER"),
            ("opposing_team_timeouts", "INTEGER"),
            ("timeout_advantage", "INTEGER"),
        ]
        
        # Weather and field position context
        context_columns = [
            ("weather_impact_score", "FLOAT"),
            ("is_indoor_game", "BOOLEAN"),
            ("field_position_category", "VARCHAR"),
            ("yards_from_own_endzone", "INTEGER"),
            ("yards_from_opponent_endzone", "INTEGER"),
        ]
        
        # Pass play details
        pass_columns = [
            ("is_complete_pass", "BOOLEAN"),
            ("is_touchdown_pass", "BOOLEAN"),
            ("is_interception", "BOOLEAN"),
            ("pass_target", "VARCHAR"),
            ("pass_defender", "VARCHAR"),
            ("is_sack", "BOOLEAN"),
            ("sack_yards", "INTEGER"),
            ("quarterback_hit", "BOOLEAN"),
            ("quarterback_scramble", "BOOLEAN"),
        ]
        
        # Run play details
        run_columns = [
            ("run_gap", "VARCHAR"),
            ("yards_after_contact", "INTEGER"),
            ("is_touchdown_run", "BOOLEAN"),
            ("is_fumble", "BOOLEAN"),
            ("fumble_recovered_by", "VARCHAR"),
            ("fumble_forced_by", "VARCHAR"),
        ]
        
        # Play outcome
        outcome_columns = [
            ("is_first_down", "BOOLEAN"),
            ("is_turnover", "BOOLEAN"),
            ("field_position_gained", "INTEGER"),
        ]
        
        # Penalty details
        penalty_columns = [
            ("is_penalty_on_play", "BOOLEAN"),
            ("penalty_type", "VARCHAR"),
            ("penalty_team", "VARCHAR"),
            ("penalty_player", "VARCHAR"),
            ("penalty_yards", "INTEGER"),
            ("penalty_declined", "BOOLEAN"),
            ("penalty_offset", "BOOLEAN"),
            ("penalty_no_play", "BOOLEAN"),
        ]
        
        # Special teams details
        special_teams_columns = [
            ("is_field_goal", "BOOLEAN"),
            ("field_goal_distance", "INTEGER"),
            ("field_goal_result", "VARCHAR"),
            ("is_punt", "BOOLEAN"),
            ("punt_distance", "INTEGER"),
            ("punt_return_yards", "INTEGER"),
            ("is_kickoff", "BOOLEAN"),
            ("kickoff_return_yards", "INTEGER"),
            ("is_touchback", "BOOLEAN"),
        ]
        
        # Combine all columns
        all_columns = (formation_columns + defensive_personnel_columns + game_context_columns +
                      drive_context_columns + game_script_columns + momentum_columns +
                      timeout_columns + context_columns + pass_columns + run_columns +
                      outcome_columns + penalty_columns + special_teams_columns)
        
        added_count = 0
        for column_data in all_columns:
            column_name = column_data[0]
            column_type = column_data[1]
            default_value = column_data[2] if len(column_data) > 2 else None
            
            if self.add_column("plays", column_name, column_type, default_value):
                added_count += 1
                
        print(f"✓ Plays table migration complete: {added_count} columns added")
        
    def migrate_players_table(self):
        """Migrate the players table (no new columns needed based on current model)"""
        print("\n🔄 Checking 'players' table...")
        print("✓ Players table is up to date - no migration needed")
        
    def migrate_play_stats_table(self):
        """Migrate the play_stats table (no new columns needed based on current model)"""
        print("\n🔄 Checking 'play_stats' table...")
        print("✓ Play stats table is up to date - no migration needed")
        
    def show_table_summary(self):
        """Show summary of current table schemas"""
        print("\n📊 Current Table Summary:")
        
        tables = ["games", "plays", "players", "play_stats"]
        for table in tables:
            try:
                columns = self.get_existing_columns(table)
                print(f"  {table}: {len(columns)} columns")
            except sqlite3.Error:
                print(f"  {table}: Table not found")
                
    def run_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting NFL Database Migration")
        print(f"Database: {self.db_path}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Connect to database
        self.connect()
        
        # Show current state
        self.show_table_summary()
        
        # Run migrations
        try:
            self.migrate_games_table()
            self.migrate_plays_table()
            self.migrate_players_table()
            self.migrate_play_stats_table()
            
            # Show final state
            print(f"\n{'🔍 Final state (DRY RUN)' if self.dry_run else '✅ Migration completed successfully!'}")
            self.show_table_summary()
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            if not self.dry_run:
                print("⚠️  Database may be in an inconsistent state")
            sys.exit(1)
        finally:
            self.close()

def main():
    parser = argparse.ArgumentParser(
        description="Migrate NFL SQLite database to add new columns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_database.py                    # Use default database path
  python scripts/migrate_database.py --db-path custom.db # Use custom database
  python scripts/migrate_database.py --dry-run          # Preview changes without applying
        """
    )
    
    parser.add_argument(
        "--db-path",
        default="nfl_data.db", 
        help="Path to SQLite database file (default: nfl_data.db)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes"
    )
    
    args = parser.parse_args()
    
    # Check if database file exists
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"❌ Database file not found: {args.db_path}")
        print("Make sure you're running from the correct directory or specify the correct path.")
        sys.exit(1)
        
    # Run migration
    migrator = DatabaseMigrator(str(db_path), args.dry_run)
    migrator.run_migration()

if __name__ == "__main__":
    main()
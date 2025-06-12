# NFL Data Scraper

This project scrapes comprehensive NFL play-by-play data from the NFL Pro API and website, storing it in a SQLite database for machine learning and analysis.

## Features

- ✅ Fetch game schedules, scores, and metadata from public NFL APIs
- ✅ Retrieve detailed play-by-play data with advanced statistics
- ✅ Store data in SQLite database with proper schema
- ✅ Support for both API-only mode and web scraping
- ✅ Query utilities for data analysis
- ✅ Migration tool for existing JSON data

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd nfl

# Install dependencies using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Project Structure

The project has been reorganized for better maintainability:

```
nfl/
├── src/                    # Core source code
│   ├── scraper/           # Main scraping functionality
│   ├── database/          # Database models and utilities
│   ├── models/            # Pydantic data models
│   └── utils/             # Utility functions
├── analysis/              # Data analysis scripts
├── scripts/               # Utility and development scripts
├── tests/                 # Test files
├── data/                  # Data storage
├── docs/                  # Documentation
└── main.py               # Main entry point
```

See [docs/STRUCTURE.md](docs/STRUCTURE.md) for detailed structure documentation.

## Configuration

Create a `.env` file in the project root with the following:

```bash
# For web scraping mode (optional)
NFL_EMAIL=your-nfl-pro-email@example.com
NFL_PASSWORD=your-nfl-pro-password

# For API play data (required for play-by-play)
BEARER_TOKEN=your-bearer-token
```

### Getting the Bearer Token

**Important**: The bearer token is required to fetch play-by-play data from the NFL Pro API.

1. Log into https://pro.nfl.com
2. Open browser developer tools (F12)
3. Go to Network tab
4. Navigate to any game's play data
5. Look for API calls to `/api/secured/videos/filmroom/plays`
6. Copy the Bearer token from the Authorization header
7. Add it to your `.env` file

**Note**: Bearer tokens expire periodically. If you get 401 errors, you'll need to get a fresh token.

## Usage

### Basic Scraping

```bash
# Scrape current week with database storage (default)
python main.py --api-only

# Scrape specific season/week
python main.py --api-only --season 2024 --week 10

# Scrape a specific game
python main.py --game-id 2024010101

# Use test data for development
python main.py --test-data

# Specify custom database path
python main.py --api-only --db-path my_nfl_data.db
```

### Data Analysis

```bash
# Analyze team performance (league-wide)
python analysis/analyze_team_stats.py

# Analyze specific team
python analysis/analyze_team_stats.py --team-id KC

# Analyze game script and context features
python analysis/analyze_game_script.py

# Analyze play result metrics
python analysis/analyze_play_results.py

# Analyze formation tendencies
python analysis/analyze_formations.py
```

### Querying the Database

```bash
# Show database summary
python scripts/query_db.py

# List games for a season
python scripts/query_db.py --games --season 2024

# Get plays for a specific game
python scripts/query_db.py --plays --game-id 2024010101

# Show game statistics
python scripts/query_db.py --stats --game-id 2024010101
```

### Development Scripts

```bash
# Test new field implementation
python scripts/test_new_fields.py

# Migrate JSON data to database
python scripts/migrate_json_to_db.py

# Debug play statistics
python scripts/debug_play_stats.py
```

## Database Schema

The SQLite database includes:

- **games** - Game information, scores, venue, teams
- **plays** - Play-by-play data with descriptions and statistics
- **play_stats** - Individual player statistics per play
- **players** - Player information and positions

## Project Analysis & Development Plan

Based on analysis of the current implementation, here's a prioritized development plan:

### Immediate Priorities (Fix Core Functionality)

1. **Fix Login Flow** - The Selenium authentication is extremely fragile with hardcoded CSS selectors. Replace with:
   - ID/name-based selectors
   - Explicit waits instead of sleep()
   - Fallback strategies for element location
   - Consider using NFL's mobile API if available

2. **Implement Database Storage** - ✅ COMPLETED
   - SQLite database with SQLAlchemy ORM
   - Efficient schema matching Pydantic models
   - Query utilities and migration tools

3. **Research & Implement Video Scraping** - The core missing feature:
   - Investigate NFL Game Pass API for video URLs
   - Check if play clips are available through the filmroom API
   - Consider youtube-dl for NFL's YouTube content
   - Implement video metadata extraction and storage

### Secondary Priorities (Optimize & Scale)

4. **Optimize API Performance**:
   - Batch play summary requests
   - Implement response caching with Redis/disk cache
   - Add connection pooling for concurrent requests

5. **Improve Data Organization**:
   - Implement the folder structure from README
   - Add data validation and deduplication
   - Create indexes for efficient retrieval

### Nice-to-Have Features

6. **Add Robustness**:
   - Resume capability for long scraping sessions
   - Better error handling and retry logic
   - Progress tracking and reporting

### Recommended Approach

1. Fix login selectors using browser developer tools
2. ✅ Implement proper database with schema
3. Add API endpoint documentation
4. Investigate video URL patterns
5. Create video download pipeline

The code is well-structured with good use of Pydantic models and type hints. The main gaps are the fragile web scraping selectors and missing video functionality.

## Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_scraper.py -v
```

## Contributing

Please ensure all tests pass and code is properly formatted before submitting PRs:

```bash
# Format code
ruff format .

# Check linting
ruff check .
```

# Data We Have Access To But Aren't Saving

  1. Weather Data (Partially saved)

  - We save weather as a string in game_info, but the API might provide structured weather data
  - Should parse and save: temperature, wind speed/direction, precipitation, humidity
  - Critical for play prediction as it affects play calling

  2. Play Formation Details

  - The play_description contains formation info (e.g., "Shotgun", "I-Formation") but it's buried in text
  - Should extract and save as structured field: offensive_formation, defensive_formation

  3. Play Result Metrics

  - We have expected_points_added but missing other outcomes from play descriptions:
    - yards_gained (currently must be parsed from description)
    - pass_length (short/medium/deep)
    - run_direction (left/middle/right)
    - pass_location (left/middle/right)

  4. Game Context Features

  - Score differential (home_score - away_score) at time of play
  - Time remaining in half/game
  - Whether team is in 2-minute drill
  - Whether it's a must-score situation

  5. Historical Team Stats (from standings data)

  - We fetch standings but don't attach them to games
  - Should save: recent win/loss streak, offensive/defensive rankings

  Data Not Available Through Current APIs But Would Be Valuable

  1. Defensive Personnel & Formations

  - We only get offensive personnel from play.summary.home/away
  - Need: defensive package (nickel, dime, base), number of DBs, box count

  2. Pre-Snap Motion & Shifts

  - Motion can indicate play type
  - Shift tendencies by team/situation

  3. Individual Player Stats/Tendencies

  - QB completion % by down/distance
  - RB yards per carry in similar situations
  - WR target share in red zone

  4. Coaching Tendencies

  - Play-calling tendencies by OC/DC
  - Aggressiveness index (4th down decisions, 2-pt conversions)

  5. Real-time Injury Status

  - Active/inactive players
  - Players playing through injuries

  6. Advanced Tracking Data

  - Player positioning at snap
  - Route combinations
  - Defensive alignment (Cover 2, Cover 3, etc.)

  Recommendations for Model Training

  Immediate improvements (data we can extract/calculate):
  1. Parse formations from play descriptions
  2. Calculate score differential for each play
  3. Extract play outcome details (yards, direction, etc.)
  4. Add "game script" features (leading/trailing, time pressure)
  5. Create derived features like "red zone efficiency" from existing data

  Code changes needed:
  # Add to Play model:
  offensive_formation: Optional[str]  # Parsed from description
  yards_gained: Optional[int]  # Parsed from description
  score_differential: int  # Calculated
  time_remaining_half: int  # Calculated
  is_two_minute_warning: bool  # Calculated
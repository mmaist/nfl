# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an NFL game data scraper designed to collect comprehensive play-by-play data for training machine learning models that predict next plays during NFL games. The scraper gathers detailed game situations, play outcomes, and contextual information from the NFL Pro API and website to build a dataset suitable for fine-tuning predictive models.

## Essential Commands

### Development Setup
```bash
# Install dependencies using uv (preferred)
uv pip install -e .

# Or using pip
pip install -e .

# Install test dependencies
pip install -r requirements-test.txt
```

### Running the Scraper
```bash
# Basic usage - scrape current week
python main.py --api-only

# Scrape specific season/week
python main.py --season 2024 --week 10

# Scrape a specific game
python main.py --game-id 2024010101

# Test with sample data
python main.py --test-data
```

### Testing
```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_scraper.py

# Run with verbose output
pytest -v
```

### Linting and Type Checking
```bash
# Format code with ruff
ruff format .

# Check linting
ruff check .

# Type checking (if mypy is configured)
mypy .
```

## Architecture Overview

### Core Components

1. **src/scraper/scraper.py** - Main scraper implementation
   - `NFLGameScraper` class handles all scraping logic
   - Supports both API-only and full scraping modes
   - Uses Selenium for authenticated play data access
   - Implements retry logic and error handling

2. **src/models/models.py** - Pydantic data models
   - Hierarchical structure: NFLData → SeasonData → WeekData → Game → Play
   - Comprehensive models for all NFL data types
   - Built-in validation and serialization

3. **src/database/** - Database components
   - `database.py`: SQLAlchemy models (DBGame, DBPlay, DBPlayer)
   - `db_utils.py`: NFLDatabaseManager for database operations

4. **Environment Configuration**
   - Requires `.env` file with:
     - `NFL_EMAIL` and `NFL_PASSWORD` for web scraping
     - `BEARER_TOKEN` for API authentication
   - Credentials are loaded via python-dotenv

### Data Flow

1. Scraper fetches game schedules from NFL API
2. For each game, retrieves:
   - Live scores and game status
   - Betting odds
   - Play-by-play data (via API or web scraping)
   - Detailed play statistics
3. Data is validated through Pydantic models
4. Saved to SQLite database via NFLDatabaseManager
5. Optional JSON export to `data/` directory

### Key API Endpoints

- Game schedules: `/prod/nfl/gamesAsync/{season}/{week}`
- Live scores: `/prod/experience-fragments/live-scores-v2`
- Betting odds: `/prod/nfl/betting/gameOdds/{gameId}`
- Play data: Requires authenticated access via Selenium

## ML-Relevant Data Points

For play prediction, the scraper captures critical features including:

- **Game Context**: Score, quarter, time remaining, timeouts
- **Field Position**: Yard line, distance to goal, field side
- **Down & Distance**: Current down, yards to go
- **Personnel**: Offensive/defensive formations (when available)
- **Previous Plays**: Full play history with outcomes
- **Game Situation**: Two-minute warning, red zone, etc.
- **Team Stats**: Win probability, scoring trends
- **Weather/Venue**: Stadium type, conditions (when available)

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

### Analysis Tools

The project includes comprehensive analysis tools:

- **analyze_team_stats.py**: Team performance analysis with historical statistics
- **analyze_game_script.py**: Game context and situational analysis
- **analyze_play_results.py**: Play outcome metrics and success rates
- **analyze_formations.py**: Formation tendencies and personnel analysis

### Development Scripts

- **test_new_fields.py**: Test and validate new database fields
- **migrate_json_to_db.py**: Migrate existing JSON data to SQLite
- **query_db.py**: Database query and export utilities
- **debug_play_stats.py**: Debug play-level statistics

## Important Notes

- The scraper handles rate limiting and retries automatically
- Web scraping mode requires valid NFL.com credentials
- Test data is available in `test_data/test_game.json` for development
- The project uses uv for dependency management (see uv.lock)
- Database storage is now the default, with comprehensive schema
- Data includes 100+ fields optimized for ML feature extraction
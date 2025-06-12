# Project Structure

This document describes the reorganized structure of the NFL Data Scraper project.

## Directory Structure

```
nfl/
├── src/                    # Core source code
│   ├── scraper/           # Main scraping functionality
│   │   ├── __init__.py
│   │   └── scraper.py     # Main NFLGameScraper class
│   ├── database/          # Database models and utilities
│   │   ├── __init__.py
│   │   ├── database.py    # SQLAlchemy models (DBGame, DBPlay, etc.)
│   │   └── db_utils.py    # Database operations and utilities
│   ├── models/            # Pydantic data models
│   │   ├── __init__.py
│   │   └── models.py      # Data validation models
│   └── utils/             # Utility functions
│       └── __init__.py
├── analysis/              # Data analysis scripts
│   ├── __init__.py
│   ├── analyze_formations.py     # Formation analysis
│   ├── analyze_game_script.py    # Game context analysis
│   ├── analyze_play_results.py   # Play outcome analysis
│   └── analyze_team_stats.py     # Team performance analysis
├── scripts/               # Utility and development scripts
│   ├── check_all_play_stats.py
│   ├── check_play_stats.py
│   ├── debug_play_stats.py
│   ├── migrate_json_to_db.py
│   ├── query_db.py
│   ├── test_api_debug.py
│   ├── test_new_fields.py
│   └── test_play_metrics.py
├── tests/                 # Test files
│   ├── conftest.py
│   ├── data/
│   ├── test_data_processing.py
│   ├── test_models.py
│   └── test_scraper.py
├── data/                  # Data storage
│   └── *.json            # Scraped data files
├── docs/                  # Documentation
│   └── STRUCTURE.md      # This file
├── main.py               # Main entry point
├── README.md             # Main README
├── CLAUDE.md             # Claude instructions
└── pyproject.toml        # Project configuration
```

## Usage

### Main Scraper
```bash
# Run the main scraper
python main.py --api-only --season 2024 --week 10

# Scrape a specific game
python main.py --game-id 2024010101

# Use test data
python main.py --test-data
```

### Analysis Scripts
```bash
# Analyze team performance
python analysis/analyze_team_stats.py --team-id KC

# Analyze game script features
python analysis/analyze_game_script.py

# Analyze play results
python analysis/analyze_play_results.py

# Analyze formations
python analysis/analyze_formations.py
```

### Utility Scripts
```bash
# Query database
python scripts/query_db.py --list-games

# Test new fields
python scripts/test_new_fields.py

# Migrate JSON to database
python scripts/migrate_json_to_db.py
```

## Module Structure

### src/scraper/
- **scraper.py**: Main `NFLGameScraper` class with all scraping functionality

### src/database/
- **database.py**: SQLAlchemy models (`DBGame`, `DBPlay`, `DBPlayer`, etc.)
- **db_utils.py**: `NFLDatabaseManager` class for database operations

### src/models/
- **models.py**: Pydantic models for data validation (`Game`, `Play`, etc.)

### analysis/
- Scripts for analyzing the collected data
- Each script can be run independently
- All scripts accept `--db-path` parameter

### scripts/
- Development and utility scripts
- Testing and debugging tools
- Database migration utilities

## Import Patterns

### From analysis/ or scripts/:
```python
# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from src
from src.database.database import DBGame, DBPlay
from src.database.db_utils import NFLDatabaseManager
```

### Within src/ modules:
```python
# Relative imports
from .database import db, DBGame, DBPlay
from ..models.models import Game, Play
```

## Benefits of New Structure

1. **Cleaner separation of concerns**: Core code, analysis, utilities, and tests are separated
2. **Better maintainability**: Related functionality is grouped together
3. **Easier testing**: Clear module boundaries make testing easier
4. **Scalability**: Easy to add new analysis scripts or utilities
5. **Professional structure**: Follows Python package best practices
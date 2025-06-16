# NFL Data Scraper

A comprehensive NFL play-by-play data scraper designed for machine learning model training. Collects detailed game situations, play outcomes, and contextual information from the NFL Pro API to build datasets suitable for predicting next plays during NFL games.

## ✨ Features

- 🏈 **Complete Game Data**: Schedules, scores, venue, weather, and team information
- 📊 **Detailed Play Statistics**: 100+ fields per play including formations, personnel, and outcomes  
- 🗄️ **SQLite Database**: Efficient storage with proper schema and query utilities
- ⚡ **Parallel Processing**: Multi-threaded scraping for fast data collection
- 🔄 **Production Ready**: Automated scraping for entire seasons with progress tracking
- 📈 **Analysis Tools**: Built-in scripts for team performance and play tendency analysis

## 🚀 Quick Start

### Installation

```bash
# Clone and install dependencies
git clone <repo-url>
cd nfl
uv pip install -e .  # or pip install -e .
```

### Configuration

Create a `.env` file:
```bash
# Required for play-by-play data
BEARER_TOKEN=your-bearer-token

# Optional for web scraping
NFL_EMAIL=your-email@example.com  
NFL_PASSWORD=your-password
```

**Getting Bearer Token**: Login to [pro.nfl.com](https://pro.nfl.com), open developer tools (F12), navigate to any game's play data, and copy the Bearer token from API calls to `/api/secured/videos/filmroom/plays`.

### Basic Usage

```bash
# Scrape current week
python main.py --api-only

# Scrape specific season/week  
python main.py --season 2024 --week 10

# Production scraping (entire seasons)
python tools/production_scraper.py --seasons 2024 --season-types REG POST
```

## 📁 Repository Structure

```
nfl/
├── 🏈 main.py                  # Main entry point for single-game scraping
├── 📂 src/                     # Core source code
│   ├── scraper/               # NFL API scraping logic
│   ├── database/              # SQLite models and utilities  
│   ├── models/                # Pydantic data validation
│   └── utils/                 # Shared utilities
├── 🛠️ tools/                   # Production scraping tools
│   ├── production_scraper.py  # Multi-season parallel scraper
│   ├── parallel_scraper.py    # Core parallel processing
│   ├── check_progress.sh      # Monitor scraping progress
│   └── monitor_progress.py    # Progress monitoring script
├── 📊 analysis/                # Data analysis scripts
│   ├── analyze_team_stats.py  # Team performance analysis
│   ├── analyze_game_script.py # Game context analysis
│   ├── analyze_play_results.py# Play outcome metrics
│   └── analyze_formations.py  # Formation tendencies
├── 🔧 scripts/                 # Utility and development scripts
├── 💾 databases/               # SQLite database files
├── 📈 output/                  # Logs and analysis results
├── 🧪 examples/                # Example usage scripts
└── 📚 docs/                    # Documentation
```

## 🏗️ Production Scraping

For large-scale data collection across multiple seasons:

### Run Production Scraper

```bash
# Scrape multiple seasons with parallel processing
python tools/production_scraper.py --seasons 2022 2023 2024 --season-types REG POST --workers 6

# Monitor progress
./tools/check_progress.sh

# Check if scraping is complete
ps aux | grep production_scraper
```

### Expected Data Volume

- **Per Season**: ~272 games (17 weeks × 16 games + postseason)
- **Per Game**: ~150 plays with detailed statistics
- **Total Dataset**: 40,000+ plays per season with 100+ features each

### Database Output

Each season creates a separate database:
- `databases/nfl_2024_complete.db` 
- `databases/nfl_2023_complete.db`
- `databases/nfl_2022_complete.db`

## 📊 Data Analysis

### Built-in Analysis Tools

```bash
# Team performance analysis
python analysis/analyze_team_stats.py --team-id KC

# Game context and situational analysis  
python analysis/analyze_game_script.py

# Play outcome metrics and success rates
python analysis/analyze_play_results.py

# Formation tendencies and personnel analysis
python analysis/analyze_formations.py
```

### Database Queries

```bash
# Database summary and statistics
python scripts/query_db.py

# Games for specific season
python scripts/query_db.py --games --season 2024

# Plays for specific game
python scripts/query_db.py --plays --game-id 2024010101
```

## 🗄️ Database Schema

### Core Tables

- **games**: Game metadata, scores, venue, weather, teams
- **plays**: Play-by-play data with descriptions and 100+ statistical fields
- **play_stats**: Individual player statistics per play  
- **players**: Player information and positions

### Key Fields for ML

**Game Context**:
- Score differential, quarter, time remaining
- Field position, down & distance
- Weather conditions, venue type

**Play Details**:
- Formation types (offense/defense)
- Personnel packages  
- Play outcomes and success metrics
- Expected points added (EPA)

**Team Information**:
- Recent performance trends
- Historical matchup data
- Coaching tendencies

## 🧪 Development & Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run tests with coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_scraper.py -v
```

### Code Quality

```bash
# Format code
ruff format .

# Check linting  
ruff check .

# Type checking (if mypy configured)
mypy .
```

## 📈 ML-Ready Features

### Contextual Data Points

- **Game Situation**: Score, time, field position, down & distance
- **Personnel**: Offensive/defensive formations and packages
- **Historical Context**: Team performance, recent trends, head-to-head records
- **Environmental**: Weather, venue, crowd noise factors
- **Coaching**: Play-calling tendencies, situational preferences

### Feature Engineering

The scraper captures raw data optimized for ML feature extraction:
- 100+ statistical fields per play
- Hierarchical game context (season → week → game → play)
- Comprehensive team and player metadata
- Time-series data for trend analysis

## 🔧 Troubleshooting

### Common Issues

**Bearer Token Expired**: 401 errors indicate expired token - get fresh token from browser developer tools

**Rate Limiting**: If requests fail, the scraper implements automatic retry logic with exponential backoff

**Postseason Games**: Some postseason games may return 0 plays due to API limitations

**Memory Usage**: For large scraping operations, monitor system memory - each worker process uses ~80MB

### Getting Help

- Check logs in `output/` directory for detailed error information
- Use `./tools/check_progress.sh` to monitor active scraping
- Review database contents with query scripts in `scripts/`

## 🎯 Use Cases

- **Play Prediction Models**: Train ML models to predict next play calls
- **Game Strategy Analysis**: Analyze team tendencies and situational preferences  
- **Performance Analytics**: Evaluate player and team efficiency metrics
- **Historical Research**: Study evolution of NFL strategy and rule changes
- **Fantasy Sports**: Build predictive models for player performance

## 📄 License

This project is for educational and research purposes. Please respect NFL data usage policies and terms of service.
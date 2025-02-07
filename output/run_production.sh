#!/bin/bash

# Production NFL Scraper Runner
# Scrapes 2022, 2023, and 2024 seasons (REG + POST)

echo "Starting NFL Production Scrape at $(date)"
echo "This will scrape approximately:"
echo "- 3 seasons (2022, 2023, 2024)"
echo "- ~54 weeks of regular season (18 weeks × 3)"
echo "- ~12 weeks of postseason (4 weeks × 3)"
echo "- ~850+ games total"
echo ""

# Create log directory
mkdir -p logs

# Set log file with timestamp
LOG_FILE="logs/production_scrape_$(date +%Y%m%d_%H%M%S).log"

# Run the scraper
echo "Running scraper... Check progress in: $LOG_FILE"
echo ""

# Start the scraper with nohup for background execution
python production_scraper.py \
    --seasons 2022 2023 2024 \
    --season-types REG POST \
    --workers 8 \
    --db-path nfl_production.db \
    --log-file "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE"

echo ""
echo "Scrape completed at $(date)"
echo "Full log available at: $LOG_FILE"
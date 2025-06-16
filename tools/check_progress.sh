#!/bin/bash

echo "=== NFL Scraper Progress Check ==="
echo "Date: $(date)"
echo

# Check running processes
RUNNING=$(ps aux | grep production_scraper | grep -v grep | wc -l)
echo "Running scrapers: $RUNNING"

if [ $RUNNING -gt 0 ]; then
    echo "Active processes:"
    ps aux | grep production_scraper | grep -v grep | awk '{print $2, $11, $12, $13, $14, $15, $16}'
fi

echo
echo "=== Latest Progress ==="

for year in 2022 2023 2024; do
    echo "--- $year ---"
    if [ -f "output/production_${year}_output.log" ]; then
        tail -3 "output/production_${year}_output.log" | grep -E "(Week|Processing|Scraping games)" | tail -1
    else
        echo "Log not found"
    fi
done

echo
echo "=== Database Counts ==="

for year in 2022 2023 2024; do
    echo "--- $year ---"
    if [ -f "databases/nfl_${year}_complete.db" ]; then
        games=$(echo 'SELECT COUNT(*) FROM games;' | sqlite3 "databases/nfl_${year}_complete.db" 2>/dev/null || echo "0")
        plays=$(echo 'SELECT COUNT(*) FROM plays;' | sqlite3 "databases/nfl_${year}_complete.db" 2>/dev/null || echo "0")
        echo "Games: $games, Plays: $plays"
    else
        echo "Database not found"
    fi
done

echo
echo "=== Completion Status ==="
if [ $RUNNING -eq 0 ]; then
    echo "✅ All scrapers completed!"
else
    echo "⏳ Still running..."
fi
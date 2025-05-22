# NFL Data Scraper

This project is a Python script that scrapes NFL data from the NFL API and saves it to a JSON file.

## Installation

## Project Analysis & Development Plan

Based on analysis of the current implementation, here's a prioritized development plan:

### Immediate Priorities (Fix Core Functionality)

1. **Fix Login Flow** - The Selenium authentication is extremely fragile with hardcoded CSS selectors. Replace with:
   - ID/name-based selectors
   - Explicit waits instead of sleep()
   - Fallback strategies for element location
   - Consider using NFL's mobile API if available

2. **Implement Database Storage** - Move from JSON files to a proper database:
   - SQLite for simplicity or PostgreSQL for production
   - Use SQLAlchemy for ORM
   - Design schema matching your Pydantic models
   - Enable efficient queries and data deduplication

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

Start with fixing the login flow since it blocks web scraping functionality. Then implement database storage to handle the growing data volume efficiently. Finally, tackle video scraping which is the main missing piece for your ML training data.

The project is well-structured with good models and API integration. The main gaps are in the web scraping implementation and actual video collection.

## Todo

- [x] Add Auth Token Handling (Bearer token implemented)
- [ ] Order Play data
- [ ] Scrape Video Data
- [ ] Organize Data into folders
- [ ] Fix janky login flow - replace brittle CSS selectors
- [ ] Implement database storage (PostgreSQL/SQLite)
- [ ] Research NFL video sources and implement actual video scraping
- [ ] Optimize API calls - batch play summaries
- [ ] Add caching mechanism for API responses
- [ ] Implement resume capability for interrupted sessions
- [ ] Complete web scraping implementation (scrape_game_plays method)
```
.
├── Data
│   ├── Season
│   │   ├── 2024
│   │   │   ├── REG
│   │   │   │   ├── WEEK_1
│   │   │   │   │   ├── Game_1
│   │   │   │   │   │   ├── Plays
│   │   │   │   │   │   │   ├── Play_1
│   │   │   │   │   │   │   ├── Play_2
│   │   │   │   │   │   │   └── ...
│   │   │   │   │   ├── Game_2
│   │   │   │   │   └── ...
│   │   │   │   ├── WEEK_2
│   │   │   │   │   ├── Game_1
│   │   │   │   │   ├── Game_2
│   │   │   │   │   └── ...
│   │   │   │   └── ...
│   │   │   ├── POST
│   │   │   │   ├── WEEK_1
│   │   │   │   ├── WEEK_2
│   │   │   │   └── ...
│   │   └── ...
```
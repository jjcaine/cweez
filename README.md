# NCAA Basketball Data Scraper

This project scrapes NCAA basketball data from the API-Basketball service and stores it in a MongoDB database.

## Features

- Fetches NCAA leagues, teams, and players
- Stores data in MongoDB collections
- Handles API rate limiting
- Provides comprehensive logging
- Supports incremental updates

## Setup

### Prerequisites

- Python 3.8+
- MongoDB (running in Docker via docker-compose)
- API-Basketball API key
- uv package manager (recommended)

### Installation

1. Clone the repository
2. Install dependencies using uv:

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using traditional pip
pip install -r requirements.txt
```

3. Start MongoDB using Docker Compose:

```bash
docker-compose up -d
```

### API Key Configuration

There are three ways to configure your API key:

1. **Environment Variable (Recommended)**:

   ```bash
   export BASKETBALL_API_KEY='your_api_key_here'
   ```

2. **Edit the Script**:
   Open `data_scraper.py` and update the default API key:

   ```python
   API_KEY = os.environ.get("BASKETBALL_API_KEY", "YOUR_NEW_API_KEY_HERE")
   ```

3. **Runtime Parameter**:
   Uncomment and modify this line in the script:
   ```python
   # api_key = "your_new_api_key_here"
   ```

### Rate Limiting

The API has rate limits (10 requests per minute on the free tier). The scraper includes:

- Automatic waiting when rate limits are hit
- Configurable delays between requests
- Option to limit the number of teams processed for testing

## Usage

Run the scraper:

```bash
python data_scraper.py
```

For testing with a limited dataset:

```python
# Modify data_scraper.py
scraper.scrape_all_ncaa_data(seasons=recent_seasons, max_teams_per_league=5)
```

## Data Structure

The scraper creates the following collections in MongoDB:

- **leagues**: NCAA basketball leagues
- **teams**: Teams participating in NCAA leagues
- **players**: Players on NCAA teams
- **seasons**: Available seasons

## Monitoring

The scraper logs all activity to both the console and a `scraper.log` file. Check these logs for progress and any errors.

## MongoDB Management

You can access the MongoDB Express interface at http://localhost:8081 to view and manage the data.

Login credentials:

- Username: admin
- Password: password

## License

MIT

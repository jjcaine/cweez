import requests
import pymongo
import time
import logging
import os
from datetime import datetime
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("basketball_scraper")

# API Configuration
BASE_URL = "https://v1.basketball.api-sports.io"
# Get API key from environment variable or use default
API_KEY = os.environ.get("BASKETBALL_API_KEY", "YOUR_NEW_API_KEY_HERE")
HEADERS = {
    'x-rapidapi-host': "v1.basketball.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# MongoDB Configuration
MONGO_URI = "mongodb://admin:password@localhost:27017/"
DB_NAME = "basketball_db"

class BasketballScraper:
    def __init__(self, api_key=None):
        # Connect to MongoDB
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        
        # Create collections if they don't exist
        self.leagues_collection = self.db["leagues"]
        self.teams_collection = self.db["teams"]
        self.players_collection = self.db["players"]
        self.seasons_collection = self.db["seasons"]
        
        # Create indexes for faster queries
        self.teams_collection.create_index([("team_id", pymongo.ASCENDING)], unique=True)
        self.players_collection.create_index([("player_id", pymongo.ASCENDING)], unique=True)
        self.leagues_collection.create_index([("league_id", pymongo.ASCENDING)], unique=True)
        
        # Allow API key override
        self.api_key = api_key or API_KEY
        self.headers = {
            'x-rapidapi-host': "v1.basketball.api-sports.io",
            'x-rapidapi-key': self.api_key
        }
        
        logger.info("Connected to MongoDB")
    
    def _make_api_request(self, endpoint, params=None):
        """Make a request to the API with rate limiting and error handling"""
        url = f"{BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Check for rate limiting headers
            remaining = int(response.headers.get('x-ratelimit-requests-remaining', 1))
            logger.info(f"API calls remaining: {remaining}")
            
            if remaining < 5:
                logger.warning(f"API rate limit almost reached. Remaining: {remaining}")
            
            # If rate limited, wait for reset
            if response.status_code == 429:
                reset_time = int(response.headers.get('x-ratelimit-requests-reset', 60))
                logger.warning(f"Rate limit exceeded. Waiting for {reset_time} seconds")
                time.sleep(reset_time)
                return self._make_api_request(endpoint, params)
            
            # Handle other errors
            if response.status_code != 200:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            # Check for API errors
            if data.get("errors") and len(data["errors"]) > 0:
                logger.error(f"API returned errors: {data['errors']}")
                return None
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(1.5)  # Increased delay to better handle rate limits
            
            return data
        
        except Exception as e:
            logger.error(f"Exception during API request: {str(e)}")
            return None
    
    def fetch_ncaa_leagues(self):
        """Fetch all NCAA leagues"""
        logger.info("Fetching NCAA leagues")
        
        params = {
            'name': 'NCAA'
        }
        
        data = self._make_api_request("leagues", params)
        
        if not data or "response" not in data:
            logger.error("Failed to fetch NCAA leagues")
            return []
        
        leagues = []
        for league in data["response"]:
            league_id = league.get("id")
            league_data = {
                "league_id": league_id,
                "name": league.get("name"),
                "type": league.get("type"),
                "country": league.get("country", {}).get("name"),
                "country_code": league.get("country", {}).get("code"),
                "logo": league.get("logo"),
                "seasons": league.get("seasons", []),
                "updated_at": datetime.now()
            }
            
            # Insert or update league in database
            self.leagues_collection.update_one(
                {"league_id": league_id},
                {"$set": league_data},
                upsert=True
            )
            
            leagues.append(league_data)
            logger.info(f"Processed league: {league.get('name')}")
        
        logger.info(f"Fetched {len(leagues)} NCAA leagues")
        return leagues
    
    def fetch_seasons(self):
        """Fetch all available seasons"""
        logger.info("Fetching available seasons")
        
        data = self._make_api_request("seasons")
        
        if not data or "response" not in data:
            logger.error("Failed to fetch seasons")
            return []
        
        seasons = []
        for season in data["response"]:
            season_data = {
                "season": season,
                "updated_at": datetime.now()
            }
            
            # Insert or update season in database
            self.seasons_collection.update_one(
                {"season": season},
                {"$set": season_data},
                upsert=True
            )
            
            seasons.append(season)
        
        logger.info(f"Fetched {len(seasons)} seasons")
        return seasons
    
    def fetch_teams_by_league(self, league_id, season):
        """Fetch all teams for a specific league and season"""
        logger.info(f"Fetching teams for league {league_id}, season {season}")
        
        params = {
            'league': league_id,
            'season': season
        }
        
        data = self._make_api_request("teams", params)
        
        if not data or "response" not in data:
            logger.error(f"Failed to fetch teams for league {league_id}, season {season}")
            return []
        
        teams = []
        for team in data["response"]:
            team_id = team.get("id")
            team_data = {
                "team_id": team_id,
                "name": team.get("name"),
                "logo": team.get("logo"),
                "national": team.get("national", False),
                "country": team.get("country", {}).get("name"),
                "country_code": team.get("country", {}).get("code"),
                "leagues": [{
                    "league_id": league_id,
                    "season": season
                }],
                "updated_at": datetime.now()
            }
            
            # Insert or update team in database
            existing_team = self.teams_collection.find_one({"team_id": team_id})
            
            if existing_team:
                # Check if this league/season combination already exists
                league_exists = False
                for league in existing_team.get("leagues", []):
                    if league.get("league_id") == league_id and league.get("season") == season:
                        league_exists = True
                        break
                
                if not league_exists:
                    # Add this league/season to the team's leagues
                    self.teams_collection.update_one(
                        {"team_id": team_id},
                        {
                            "$push": {"leagues": {"league_id": league_id, "season": season}},
                            "$set": {"updated_at": datetime.now()}
                        }
                    )
            else:
                # Insert new team
                self.teams_collection.insert_one(team_data)
            
            teams.append(team_data)
        
        logger.info(f"Fetched {len(teams)} teams for league {league_id}, season {season}")
        return teams
    
    def fetch_players_by_team(self, team_id, season):
        """Fetch all players for a specific team and season"""
        logger.info(f"Fetching players for team {team_id}, season {season}")
        
        params = {
            'team': team_id,
            'season': season
        }
        
        data = self._make_api_request("players", params)
        
        if not data or "response" not in data:
            logger.error(f"Failed to fetch players for team {team_id}, season {season}")
            return []
        
        players = []
        for player in data["response"]:
            player_id = player.get("id")
            player_data = {
                "player_id": player_id,
                "first_name": player.get("firstname"),
                "last_name": player.get("lastname"),
                "birth": {
                    "date": player.get("birth", {}).get("date"),
                    "country": player.get("birth", {}).get("country"),
                    "place": player.get("birth", {}).get("place")
                },
                "height": player.get("height", {}).get("meters"),
                "weight": player.get("weight", {}).get("kilograms"),
                "photo": player.get("photo"),
                "teams": [{
                    "team_id": team_id,
                    "season": season,
                    "jersey": player.get("leagues", {}).get(str(season), {}).get("jersey"),
                    "active": player.get("leagues", {}).get(str(season), {}).get("active")
                }],
                "updated_at": datetime.now()
            }
            
            # Insert or update player in database
            existing_player = self.players_collection.find_one({"player_id": player_id})
            
            if existing_player:
                # Check if this team/season combination already exists
                team_exists = False
                for team in existing_player.get("teams", []):
                    if team.get("team_id") == team_id and team.get("season") == season:
                        team_exists = True
                        break
                
                if not team_exists:
                    # Add this team/season to the player's teams
                    self.players_collection.update_one(
                        {"player_id": player_id},
                        {
                            "$push": {"teams": {
                                "team_id": team_id,
                                "season": season,
                                "jersey": player.get("leagues", {}).get(str(season), {}).get("jersey"),
                                "active": player.get("leagues", {}).get(str(season), {}).get("active")
                            }},
                            "$set": {"updated_at": datetime.now()}
                        }
                    )
            else:
                # Insert new player
                self.players_collection.insert_one(player_data)
            
            players.append(player_data)
        
        logger.info(f"Fetched {len(players)} players for team {team_id}, season {season}")
        return players
    
    def scrape_all_ncaa_data(self, seasons=None, max_teams_per_league=None):
        """Scrape all NCAA data - leagues, teams, and players"""
        logger.info("Starting full NCAA data scrape")
        
        # Fetch all seasons if not provided
        if not seasons:
            all_seasons = self.fetch_seasons()
            # Use the most recent 3 seasons
            seasons = sorted(all_seasons, reverse=True)[:3]
        
        # Fetch all NCAA leagues
        leagues = self.fetch_ncaa_leagues()
        
        # Process each league and season
        for league in leagues:
            league_id = league["league_id"]
            league_name = league["name"]
            
            for season in seasons:
                logger.info(f"Processing {league_name} for season {season}")
                
                # Fetch teams for this league and season
                teams = self.fetch_teams_by_league(league_id, season)
                
                # Limit number of teams if specified (useful for testing)
                if max_teams_per_league and len(teams) > max_teams_per_league:
                    logger.info(f"Limiting to {max_teams_per_league} teams for testing")
                    teams = teams[:max_teams_per_league]
                
                # Fetch players for each team
                for team in tqdm(teams, desc=f"Fetching players for {league_name} teams"):
                    team_id = team["team_id"]
                    self.fetch_players_by_team(team_id, season)
                    
                    # Add a longer delay between team requests to avoid rate limits
                    time.sleep(2)
                
                logger.info(f"Completed processing {league_name} for season {season}")
        
        logger.info("Completed full NCAA data scrape")

if __name__ == "__main__":
    # You can provide your API key directly here if needed
    api_key = os.environ.get("BASKETBALL_API_KEY")
    
    if not api_key:
        print("Warning: No API key found in environment variables.")
        print("Please set the BASKETBALL_API_KEY environment variable or update the API_KEY in the script.")
        print("Example: export BASKETBALL_API_KEY='your_api_key_here'")
        
        # Uncomment and update the line below to hardcode your API key
        # api_key = "your_new_api_key_here"
    
    scraper = BasketballScraper(api_key=api_key)
    
    # Use the most recent 2 seasons
    recent_seasons = ["2023-2024", "2022-2023"]
    
    try:
        # For testing, limit to 3 teams per league to avoid hitting API rate limits
        scraper.scrape_all_ncaa_data(seasons=recent_seasons, max_teams_per_league=3)
        
        # For production, use the full scrape
        # scraper.scrape_all_ncaa_data(seasons=recent_seasons)
        logger.info("Data scraping completed successfully")
    except Exception as e:
        logger.error(f"Error during data scraping: {str(e)}")

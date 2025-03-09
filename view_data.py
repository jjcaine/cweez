import pymongo
import json
from bson import json_util
import os

# MongoDB Configuration
MONGO_URI = "mongodb://admin:password@localhost:27017/"
DB_NAME = "basketball_db"

def connect_to_mongodb():
    """Connect to MongoDB and return the database object"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db

def print_collection_stats(db):
    """Print statistics about each collection"""
    collections = db.list_collection_names()
    
    print("\n=== MongoDB Collections ===")
    for collection in collections:
        count = db[collection].count_documents({})
        print(f"{collection}: {count} documents")

def view_leagues(db):
    """View all leagues in the database"""
    leagues = list(db.leagues.find())
    
    print("\n=== NCAA Leagues ===")
    for league in leagues:
        print(f"League ID: {league.get('league_id')}")
        print(f"Name: {league.get('name')}")
        print(f"Type: {league.get('type')}")
        print(f"Country: {league.get('country')}")
        print(f"Seasons: {league.get('seasons')}")
        print("-" * 30)

def view_teams(db, limit=5):
    """View teams in the database"""
    teams = list(db.teams.find().limit(limit))
    
    print(f"\n=== Teams (showing {limit}) ===")
    for team in teams:
        print(f"Team ID: {team.get('team_id')}")
        print(f"Name: {team.get('name')}")
        print(f"Country: {team.get('country')}")
        print(f"Leagues: {team.get('leagues')}")
        print("-" * 30)

def view_players(db, limit=5):
    """View players in the database"""
    players = list(db.players.find().limit(limit))
    
    print(f"\n=== Players (showing {limit}) ===")
    for player in players:
        print(f"Player ID: {player.get('player_id')}")
        print(f"Name: {player.get('first_name')} {player.get('last_name')}")
        print(f"Birth: {player.get('birth')}")
        print(f"Height: {player.get('height')} m")
        print(f"Weight: {player.get('weight')} kg")
        print(f"Teams: {player.get('teams')}")
        print("-" * 30)

def export_data(db, collection_name, filename):
    """Export a collection to a JSON file"""
    data = list(db[collection_name].find())
    
    # Convert MongoDB data to JSON
    json_data = json.loads(json_util.dumps(data))
    
    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)
    
    # Write to file
    with open(f"exports/{filename}", "w") as f:
        json.dump(json_data, f, indent=2)
    
    print(f"Exported {len(data)} documents to exports/{filename}")

if __name__ == "__main__":
    db = connect_to_mongodb()
    
    # Print collection statistics
    print_collection_stats(db)
    
    # View leagues
    view_leagues(db)
    
    # View teams
    view_teams(db)
    
    # View players
    view_players(db)
    
    # Export data to JSON files
    export_data(db, "leagues", "leagues.json")
    export_data(db, "teams", "teams.json")
    export_data(db, "players", "players.json") 
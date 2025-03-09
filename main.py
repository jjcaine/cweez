import random
import numpy as np
import pandas as pd
from collections import defaultdict
from enum import Enum

class PredictionMethod(Enum):
    KENPOM = "kenpom"
    CONFERENCE_RECORD = "conference_record"
    BARTTORVIK = "barttorvik"

# 1. Set up the teams with Barttorvik's ratings and venue effects
teams = [
    {"name": "St. John's", "adjOE": 112.7, "adjDE": 90.4, "seed": 1, "conf_wins": 18, "conf_losses": 2, "overall_wins": 27, "overall_losses": 4, "adjT": 70.1, "home_court": True, "travel_advantage": False},
    {"name": "Creighton", "adjOE": 117.2, "adjDE": 98.2, "seed": 2, "conf_wins": 15, "conf_losses": 5, "overall_wins": 22, "overall_losses": 9, "adjT": 67.8, "home_court": False, "travel_advantage": False},
    {"name": "Connecticut", "adjOE": 122.0, "adjDE": 102.5, "seed": 3, "conf_wins": 14, "conf_losses": 6, "overall_wins": 22, "overall_losses": 9, "adjT": 64.4, "home_court": False, "travel_advantage": True},
    {"name": "Marquette", "adjOE": 116.7, "adjDE": 96.6, "seed": 4, "conf_wins": 13, "conf_losses": 7, "overall_wins": 22, "overall_losses": 9, "adjT": 67.4, "home_court": False, "travel_advantage": False},
    {"name": "Xavier", "adjOE": 115.5, "adjDE": 97.7, "seed": 5, "conf_wins": 13, "conf_losses": 7, "overall_wins": 21, "overall_losses": 10, "adjT": 69.3, "home_court": False, "travel_advantage": False},
    {"name": "Villanova", "adjOE": 119.6, "adjDE": 103.7, "seed": 6, "conf_wins": 11, "conf_losses": 9, "overall_wins": 18, "overall_losses": 13, "adjT": 63.2, "home_court": False, "travel_advantage": False},
    {"name": "Georgetown", "adjOE": 107.4, "adjDE": 100.2, "seed": 7, "conf_wins": 8, "conf_losses": 12, "overall_wins": 17, "overall_losses": 14, "adjT": 68.4, "home_court": False, "travel_advantage": False},
    {"name": "Butler", "adjOE": 116.8, "adjDE": 106.1, "seed": 8, "conf_wins": 6, "conf_losses": 14, "overall_wins": 13, "overall_losses": 18, "adjT": 67.8, "home_court": False, "travel_advantage": False},
    {"name": "Providence", "adjOE": 112.0, "adjDE": 105.6, "seed": 9, "conf_wins": 6, "conf_losses": 14, "overall_wins": 12, "overall_losses": 19, "adjT": 66.6, "home_court": False, "travel_advantage": False},
    {"name": "DePaul", "adjOE": 109.4, "adjDE": 105.4, "seed": 10, "conf_wins": 4, "conf_losses": 16, "overall_wins": 13, "overall_losses": 18, "adjT": 67.3, "home_court": False, "travel_advantage": False},
    {"name": "Seton Hall", "adjOE": 98.6, "adjDE": 102.7, "seed": 11, "conf_wins": 2, "conf_losses": 18, "overall_wins": 7, "overall_losses": 24, "adjT": 64.6, "home_court": False, "travel_advantage": False}
]

# 2. Create the tournament bracket structure
def create_bracket():
    return {
        "first_round": [
            {"teamA": teams[7], "teamB": teams[8]},   # 8 vs 9
            {"teamA": teams[6], "teamB": teams[9]},   # 7 vs 10
            {"teamA": teams[5], "teamB": teams[10]}   # 6 vs 11
        ],
        "quarterfinals": [
            {"teamA": teams[0], "teamB": None},      # 1 vs 8/9 winner
            {"teamA": teams[3], "teamB": teams[4]},  # 4 vs 5
            {"teamA": teams[2], "teamB": None},      # 3 vs 6/11 winner
            {"teamA": teams[1], "teamB": None}       # 2 vs 7/10 winner
        ],
        "semifinals": [
            {"teamA": None, "teamB": None},
            {"teamA": None, "teamB": None}
        ],
        "final": {
            "teamA": None,
            "teamB": None,
            "winner": None
        }
    }

# 3. Predict game outcomes based on team ratings
def predict_game(teamA, teamB, method=PredictionMethod.BARTTORVIK):
    if not teamA or not teamB:
        return None
    
    # Default win probability without venue effects
    teamA_expected_win_pct = 0.5
    
    if method == PredictionMethod.KENPOM:
        # Calculate expected offensive and defensive performance
        teamA_offense = teamA["adjOE"]
        teamA_defense = teamA["adjDE"]
        teamB_offense = teamB["adjOE"]
        teamB_defense = teamB["adjDE"]
        
        # Expected points per 100 possessions
        teamA_expected_score = teamA_offense * (teamB_defense / 100)
        teamB_expected_score = teamB_offense * (teamA_defense / 100)
        
        # Calculate win probability using log5 formula with reduced multiplier
        teamA_expected_win_pct = 1 / (1 + 10 ** (-(teamA_expected_score - teamB_expected_score) * 0.175))
    
    elif method == PredictionMethod.CONFERENCE_RECORD:
        # Calculate win percentages
        teamA_win_pct = teamA["conf_wins"] / (teamA["conf_wins"] + teamA["conf_losses"])
        teamB_win_pct = teamB["conf_wins"] / (teamB["conf_wins"] + teamB["conf_losses"])
        
        # Use log5 formula with dampening for extreme records
        # Add a small constant to prevent extreme probabilities
        teamA_win_pct = (teamA_win_pct * 0.85) + 0.075
        teamB_win_pct = (teamB_win_pct * 0.85) + 0.075
        
        # Formula: p(A beats B) = (pA - pA*pB) / (pA + pB - 2*pA*pB)
        teamA_expected_win_pct = (teamA_win_pct - teamA_win_pct * teamB_win_pct) / (teamA_win_pct + teamB_win_pct - 2 * teamA_win_pct * teamB_win_pct)
    
    else:  # PredictionMethod.BARTTORVIK - calibrated to match Barttorvik's results
        # Calculate expected offensive and defensive performance
        teamA_offense = teamA["adjOE"]
        teamA_defense = teamA["adjDE"]
        teamB_offense = teamB["adjOE"]
        teamB_defense = teamB["adjDE"]
        
        # Expected points per 100 possessions
        teamA_expected_score = teamA_offense * (teamB_defense / 100)
        teamB_expected_score = teamB_offense * (teamA_defense / 100)
        
        # Calculate win probability using calibrated multiplier
        # Reduced from 0.175 to 0.135 for more balanced probabilities
        teamA_expected_win_pct = 1 / (1 + 10 ** (-(teamA_expected_score - teamB_expected_score) * 0.135))
        
        # Apply venue effects
        if teamA["home_court"] and not teamB["home_court"]:
            # Home court advantage boost (3-4% boost)
            teamA_expected_win_pct = min(0.95, teamA_expected_win_pct + 0.04)
        elif teamB["home_court"] and not teamA["home_court"]:
            # Home court disadvantage
            teamA_expected_win_pct = max(0.05, teamA_expected_win_pct - 0.04)
        
        # Apply travel advantage effects (smaller effect)
        if teamA["travel_advantage"] and not teamB["travel_advantage"] and not teamB["home_court"]:
            # Travel advantage boost (1-2% boost)
            teamA_expected_win_pct = min(0.95, teamA_expected_win_pct + 0.02)
        elif teamB["travel_advantage"] and not teamA["travel_advantage"] and not teamA["home_court"]:
            # Travel advantage disadvantage
            teamA_expected_win_pct = max(0.05, teamA_expected_win_pct - 0.02)
        
        # Add tournament variance - big upsets are slightly more likely in tournaments
        # Apply mild regression to the mean
        if teamA_expected_win_pct > 0.7:
            teamA_expected_win_pct = 0.7 + (teamA_expected_win_pct - 0.7) * 0.8
        elif teamA_expected_win_pct < 0.3:
            teamA_expected_win_pct = 0.3 - (0.3 - teamA_expected_win_pct) * 0.8
    
    # Generate random number to determine winner
    random_value = random.random()
    
    return teamA if random_value < teamA_expected_win_pct else teamB

# 4. Run a single tournament simulation
def simulate_tournament(prediction_method=PredictionMethod.BARTTORVIK):
    bracket = create_bracket()
    
    # First Round
    first_round_winners = [predict_game(matchup["teamA"], matchup["teamB"], prediction_method) for matchup in bracket["first_round"]]
    
    # Update Quarterfinals with First Round winners
    bracket["quarterfinals"][0]["teamB"] = first_round_winners[0]  # 8/9 winner
    bracket["quarterfinals"][2]["teamB"] = first_round_winners[2]  # 6/11 winner
    bracket["quarterfinals"][3]["teamB"] = first_round_winners[1]  # 7/10 winner
    
    # Quarterfinals
    quarterfinals_winners = [predict_game(matchup["teamA"], matchup["teamB"], prediction_method) for matchup in bracket["quarterfinals"]]
    
    # Update Semifinals
    bracket["semifinals"][0]["teamA"] = quarterfinals_winners[0]
    bracket["semifinals"][0]["teamB"] = quarterfinals_winners[1]
    bracket["semifinals"][1]["teamA"] = quarterfinals_winners[2]
    bracket["semifinals"][1]["teamB"] = quarterfinals_winners[3]
    
    # Track semifinal teams for additional analysis
    semifinal_teams = [
        quarterfinals_winners[0],
        quarterfinals_winners[1],
        quarterfinals_winners[2],
        quarterfinals_winners[3]
    ]
    
    # Semifinals
    semifinals_winners = [predict_game(matchup["teamA"], matchup["teamB"], prediction_method) for matchup in bracket["semifinals"]]
    
    # Update Finals
    bracket["final"]["teamA"] = semifinals_winners[0]
    bracket["final"]["teamB"] = semifinals_winners[1]
    
    # Track finals teams
    final_teams = [semifinals_winners[0], semifinals_winners[1]]
    
    # Championship game
    bracket["final"]["winner"] = predict_game(bracket["final"]["teamA"], bracket["final"]["teamB"], prediction_method)
    
    return {
        "champion": bracket["final"]["winner"],
        "finalists": final_teams,
        "semifinalists": semifinal_teams
    }

# 5. Run multiple simulations and aggregate results
def run_monte_carlo(num_simulations=10000, prediction_method=PredictionMethod.BARTTORVIK):
    championship_results = defaultdict(int)
    final_appearances = defaultdict(int)
    semifinal_appearances = defaultdict(int)
    
    for _ in range(num_simulations):
        results = simulate_tournament(prediction_method)
        
        # Track championship
        if results["champion"]:
            championship_results[results["champion"]["name"]] += 1
        
        # Track finals appearances
        for team in results["finalists"]:
            if team:
                final_appearances[team["name"]] += 1
        
        # Track semifinal appearances
        for team in results["semifinalists"]:
            if team:
                semifinal_appearances[team["name"]] += 1
    
    # Convert to probabilities
    team_names = [team["name"] for team in teams]
    
    championship_probs = {team: (championship_results[team] / num_simulations) * 100 for team in team_names}
    final_probs = {team: (final_appearances[team] / num_simulations) * 100 for team in team_names}
    semifinal_probs = {team: (semifinal_appearances[team] / num_simulations) * 100 for team in team_names}
    
    # Format and sort results
    results_df = pd.DataFrame({
        'Team': team_names,
        'Championship %': [championship_probs[team] for team in team_names],
        'Finals %': [final_probs[team] for team in team_names],
        'Semifinals %': [semifinal_probs[team] for team in team_names]
    })
    
    # Sort by championship probability
    results_df = results_df.sort_values('Championship %', ascending=False)
    
    return results_df

# Run simulations and display results
if __name__ == "__main__":
    np.random.seed(42)  # For reproducibility
    random.seed(42)
    
    # Run 10,000 simulations with Barttorvik calibrated model
    barttorvik_results = run_monte_carlo(100000, PredictionMethod.BARTTORVIK)
    
    print("Big East Tournament Simulation Results - Barttorvik Method (100,000 runs):")
    print(barttorvik_results.to_string(index=False, float_format=lambda x: f"{x:.1f}%"))
    
    print("\nBig East Tournament Simulation Results - KenPom Method (100,000 runs):")
    kenpom_results = run_monte_carlo(100000, PredictionMethod.KENPOM)
    print(kenpom_results.to_string(index=False, float_format=lambda x: f"{x:.1f}%"))
    
    print("\nBig East Tournament Simulation Results - Conference Record Method (100,000 runs):")
    conf_record_results = run_monte_carlo(100000, PredictionMethod.CONFERENCE_RECORD)
    print(conf_record_results.to_string(index=False, float_format=lambda x: f"{x:.1f}%"))
    
    # Additional analysis - expected seed of champion
    print("\nAdvanced Analysis:")
    # Add more sophisticated analysis here as needed
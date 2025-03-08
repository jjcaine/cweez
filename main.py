import random
import numpy as np
import pandas as pd
from collections import defaultdict

# 1. Set up the teams with their current KenPom ratings
teams = [
    {"name": "St. John's", "adjOE": 113.7, "adjDE": 89.0, "seed": 1},
    {"name": "Creighton", "adjOE": 116.5, "adjDE": 97.9, "seed": 2},
    {"name": "Marquette", "adjOE": 117.9, "adjDE": 95.6, "seed": 3},
    {"name": "Connecticut", "adjOE": 122.3, "adjDE": 103.7, "seed": 4},
    {"name": "Xavier", "adjOE": 115.4, "adjDE": 98.2, "seed": 5},
    {"name": "Villanova", "adjOE": 119.9, "adjDE": 104.8, "seed": 6},
    {"name": "Georgetown", "adjOE": 108.7, "adjDE": 99.1, "seed": 7},
    {"name": "Butler", "adjOE": 116.6, "adjDE": 105.7, "seed": 8},
    {"name": "Providence", "adjOE": 112.9, "adjDE": 105.8, "seed": 9},
    {"name": "DePaul", "adjOE": 109.4, "adjDE": 106.1, "seed": 10},
    {"name": "Seton Hall", "adjOE": 100.0, "adjDE": 102.9, "seed": 11}
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
def predict_game(teamA, teamB):
    if not teamA or not teamB:
        return None
    
    # Calculate expected offensive and defensive performance
    teamA_offense = teamA["adjOE"]
    teamA_defense = teamA["adjDE"]
    teamB_offense = teamB["adjOE"]
    teamB_defense = teamB["adjDE"]
    
    # Expected points per 100 possessions
    teamA_expected_score = teamA_offense * (teamB_defense / 100)
    teamB_expected_score = teamB_offense * (teamA_defense / 100)
    
    # Calculate win probability using log5 formula
    teamA_expected_win_pct = 1 / (1 + 10 ** (-(teamA_expected_score - teamB_expected_score) * 0.175))
    
    # Generate random number to determine winner
    random_value = random.random()
    
    return teamA if random_value < teamA_expected_win_pct else teamB

# 4. Run a single tournament simulation
def simulate_tournament():
    bracket = create_bracket()
    
    # First Round
    first_round_winners = [predict_game(matchup["teamA"], matchup["teamB"]) for matchup in bracket["first_round"]]
    
    # Update Quarterfinals with First Round winners
    bracket["quarterfinals"][0]["teamB"] = first_round_winners[0]  # 8/9 winner
    bracket["quarterfinals"][2]["teamB"] = first_round_winners[2]  # 6/11 winner
    bracket["quarterfinals"][3]["teamB"] = first_round_winners[1]  # 7/10 winner
    
    # Quarterfinals
    quarterfinals_winners = [predict_game(matchup["teamA"], matchup["teamB"]) for matchup in bracket["quarterfinals"]]
    
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
    semifinals_winners = [predict_game(matchup["teamA"], matchup["teamB"]) for matchup in bracket["semifinals"]]
    
    # Update Finals
    bracket["final"]["teamA"] = semifinals_winners[0]
    bracket["final"]["teamB"] = semifinals_winners[1]
    
    # Track finals teams
    final_teams = [semifinals_winners[0], semifinals_winners[1]]
    
    # Championship game
    bracket["final"]["winner"] = predict_game(bracket["final"]["teamA"], bracket["final"]["teamB"])
    
    return {
        "champion": bracket["final"]["winner"],
        "finalists": final_teams,
        "semifinalists": semifinal_teams
    }

# 5. Run multiple simulations and aggregate results
def run_monte_carlo(num_simulations=10000):
    championship_results = defaultdict(int)
    final_appearances = defaultdict(int)
    semifinal_appearances = defaultdict(int)
    
    for _ in range(num_simulations):
        results = simulate_tournament()
        
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
    
    # Run 10,000 simulations
    results = run_monte_carlo(10000)
    
    print("Big East Tournament Simulation Results (10,000 runs):")
    print(results.to_string(index=False, float_format=lambda x: f"{x:.1f}%"))
    
    # Additional analysis - expected seed of champion
    print("\nAdvanced Analysis:")
    # Add more sophisticated analysis here as needed

import random
import datetime

# Settings
bankroll = 10.00
target = 10000.00
daily_max_risk_percent = 0.10
single_bet_percent = 0.03
parlay_bet_percent = 0.02
single_bet_probability = 0.75

# Initialize log
bet_log = []

def get_odds_and_probabilities():
    odds = random.choice([1.5, 1.7, 2.0, 4.5, 6.0])
    probability = random.uniform(0.6, 0.75) if odds < 2 else random.uniform(0.20, 0.35)
    return odds, probability

def simulate_bet_result(probability):
    return "win" if random.random() < probability else "lose"

def place_bets(bankroll):
    daily_limit = bankroll * daily_max_risk_percent
    daily_spent = 0
    new_bankroll = bankroll

    while daily_spent < daily_limit:
        bet_type = "single" if random.random() < single_bet_probability else "parlay"
        odds, probability = get_odds_and_probabilities()
        stake_percent = single_bet_percent if bet_type == "single" else parlay_bet_percent
        stake = new_bankroll * stake_percent

        if daily_spent + stake > daily_limit:
            break

        daily_spent += stake
        result = simulate_bet_result(probability)
        ev_score = (probability * odds) - 1

        if result == "win":
            new_bankroll += stake * (odds - 1)
        else:
            new_bankroll -= stake

        log_entry = {
            "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Bet Type": bet_type,
            "Odds": round(odds, 2),
            "Stake": round(stake, 2),
            "Win Probability": round(probability, 2),
            "EV Score": round(ev_score, 2),
            "Result": result,
            "New Bankroll": round(new_bankroll, 2)
        }
        bet_log.append(log_entry)

    return new_bankroll

# Run one simulation round
bankroll = place_bets(bankroll)

# Display all logs and final bankroll
for entry in bet_log:
    print(entry)

print(f"End of Day Bankroll: {bankroll:.2f}")

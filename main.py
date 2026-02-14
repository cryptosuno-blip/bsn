import requests
import pandas as pd
import time

# --- 🔐 CREDENTIALS ---
API_KEY = "70617b57595c48c0b49f6319d73303bf"
TELEGRAM_TOKEN = "8087802550:AAGx-SjBm1fOF15vmLinbdsW11VbRldynlg"
CHAT_ID = "5447712499"
# ----------------------

BASE_URL = "http://api.football-data.org/v4"
HEADERS = {'X-Auth-Token': API_KEY}
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1'] 

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def get_advanced_stats(comp_code):
    """
    Fetches the table and calculates Attack/Defense power for every team.
    """
    url = f"{BASE_URL}/competitions/{comp_code}/standings"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        stats = {}
        
        if 'standings' in data:
            for table in data['standings']:
                if table['type'] == 'TOTAL':
                    for row in table['table']:
                        played = row['playedGames']
                        if played == 0: played = 1 # Avoid divide by zero
                        
                        # Calculate Metrics
                        goals_scored = row['goalsFor']
                        goals_conceded = row['goalsAgainst']
                        
                        # Avg Goals per Game (Attack Strength)
                        att_power = round(goals_scored / played, 2)
                        
                        # Avg Goals Conceded per Game (Defensive Weakness)
                        def_weakness = round(goals_conceded / played, 2)
                        
                        stats[row['team']['name']] = {
                            "att": att_power,
                            "def": def_weakness,
                            "gd": row['goalDifference'], # Goal Difference
                            "rank": row['position']
                        }
        return stats
    except: return {}

def run_deep_analysis():
    print(f"🧠 DEEP ANALYSIS AGENT: Calculating Goal Expectancy...")
    
    telegram_report = "🧠 *PRO-ANALYSIS REPORT* 🧠\n\n"
    bets_found = 0
    
    for league in LEAGUES:
        # Get next 5 scheduled games
        url = f"{BASE_URL}/competitions/{league}/matches"
        querystring = {"status": "SCHEDULED"}
        
        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            data = response.json()
            matches = data.get('matches', [])[:5] 
            
            if not matches: continue

            print(f"   -> Processing stats for {league}...")
            team_stats = get_advanced_stats(league)
            
            for match in matches:
                home = match['homeTeam']['name']
                away = match['awayTeam']['name']
                date = match['utcDate'].split("T")[0]
                
                # Get Stats (Default to 1.0 if missing)
                h_stats = team_stats.get(home, {"att": 1.0, "def": 1.0, "gd": 0, "rank": 10})
                a_stats = team_stats.get(away, {"att": 1.0, "def": 1.0, "gd": 0, "rank": 10})
                
                # --- 🧮 THE MATH MODEL ---
                
                # 1. Expected Goals (xG) Calculation
                # Home Expected Goals = (Home Attack + Away Defense) / 2
                h_exp_goals = (h_stats['att'] + a_stats['def']) / 2
                
                # Away Expected Goals = (Away Attack + Home Defense) / 2
                a_exp_goals = (a_stats['att'] + h_stats['def']) / 2
                
                # Add Home Advantage (+0.2 Goals is standard statistical boost)
                h_exp_goals += 0.2
                
                prediction = None
                reason = ""
                
                # --- DECISION LOGIC ---
                
                # STRONG HOME WIN
                # If Home is expected to score 0.8 goals MORE than away
                if h_exp_goals > (a_exp_goals + 0.8):
                    prediction = f"🏠 *HOME WIN:* {home}"
                    reason = f"Attack Rating {h_stats['att']} vs Weak Def {a_stats['def']}"
                
                # STRONG AWAY WIN
                elif a_exp_goals > (h_exp_goals + 0.8):
                    prediction = f"💎 *AWAY WIN:* {away}"
                    reason = f"Superior Attack ({a_stats['att']} goals/game)"
                    
                # OVER 2.5 GOALS (Goal Fest)
                # If combined expected goals > 3.0
                elif (h_exp_goals + a_exp_goals) > 3.0:
                    prediction = f"⚽ *OVER 2.5 GOALS*"
                    reason = f"Both teams leaky. Est Goals: {round(h_exp_goals + a_exp_goals, 2)}"

                if prediction:
                    bets_found += 1
                    telegram_report += f"{prediction}\n"
                    telegram_report += f"🆚 {home} vs {away}\n"
                    telegram_report += f"💡 Insight: {reason}\n"
                    telegram_report += f"📈 Exp. Score: {round(h_exp_goals,1)} - {round(a_exp_goals,1)}\n\n"
                    
        except Exception as e:
            print(f"Error checking {league}: {e}")

    if bets_found > 0:
        print(f"✅ Found {bets_found} deep-value bets. Sending Telegram...")
        send_telegram(telegram_report)
    else:
        print("❌ No statistical value found today.")

run_deep_analysis()

import os
import json
import random
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file, session
from flask_cors import CORS
import io
import csv

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
app.secret_key = 'your_secret_key_here'  # Change this to a random, secure value

DATA_FILE = 'prizes.json'
ADMIN_PASSWORD = 'supersecretpassword' # For demonstration, use a strong password

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "winProbability": {
                "COFFEE_MUG": 0.5,
                "NO_PRIZE": 0.5
            },
            "prizeLimits": {
                "COFFEE_MUG": 100
            },
            "prizesGiven": {},
            "winnerLog": []
        }
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get-prize', methods=['POST'])
def get_prize():
    data = load_data()
    probabilities = data.get('winProbability', {})
    prize_limits = data.get('prizeLimits', {})
    prizes_given = data.get('prizesGiven', {})
    winner_log = data.get('winnerLog', [])

    user_data = request.json
    name = user_data.get('name')
    email = user_data.get('email')

    prizes_available = {prize: (limit - prizes_given.get(prize, 0)) for prize, limit in prize_limits.items() if prize != 'NO_PRIZE'}
    
    available_probabilities = {p: prob for p, prob in probabilities.items() if prizes_available.get(p, 0) > 0}
    
    total_prob = sum(available_probabilities.values())
    no_prize_prob = max(0, 1.0 - total_prob)
    
    prize_options = list(available_probabilities.keys())
    prize_weights = list(available_probabilities.values())
    
    if no_prize_prob > 0:
        prize_options.append("NO_PRIZE")
        prize_weights.append(no_prize_prob)
    
    if not prize_options:
        selected_prize = "NO_PRIZE"
    else:
        selected_prize = random.choices(prize_options, weights=prize_weights, k=1)[0]
        
    results = [""] * 6
    winning_symbol = None
    
    if selected_prize != "NO_PRIZE":
        winning_symbol = selected_prize
        winning_positions = random.sample(range(6), 3)
        for pos in winning_positions:
            results[pos] = winning_symbol

        prizes_given[winning_symbol] = prizes_given.get(winning_symbol, 0) + 1
        winner_entry = {
            "name": name,
            "email": email,
            "prize": winning_symbol,
            "timestamp": datetime.now().isoformat()
        }
        winner_log.append(winner_entry)
        save_data(data)

        # New logic to populate the non-winning scratch pads
        # Get all other prize symbols excluding the winning one
        non_winning_symbols = [p for p in list(prizes_available.keys()) + ["NO_PRIZE"] if p != winning_symbol]
        
        # Get the remaining positions
        non_winning_positions = [i for i in range(6) if i not in winning_positions]
        
        # Fill the remaining positions with a random selection of non-winning symbols
        for pos in non_winning_positions:
            results[pos] = random.choice(non_winning_symbols)
    
    # If no prize was won, fill all pads with a random selection of other prizes
    else:
        all_prizes = list(prizes_available.keys())
        for pos in range(6):
            results[pos] = random.choice(all_prizes)

    return jsonify({"results": results, "prize": selected_prize})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('admin_panel'))
    else:
        return "Invalid password. <a href='/'>Go back</a>"

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    data = load_data()
    
    if request.method == 'POST':
        try:
            new_probabilities = {}
            new_prize_limits = {}
            for key, value in request.form.items():
                if key.startswith('prob_'):
                    prize_name = key.replace('prob_', '')
                    if value:
                        new_probabilities[prize_name] = float(value)
                    else:
                        new_probabilities[prize_name] = 0.0
                elif key.startswith('limit_'):
                    prize_name = key.replace('limit_', '')
                    if value:
                        new_prize_limits[prize_name] = int(value)
                    else:
                        new_prize_limits[prize_name] = 0
            
            data['winProbability'] = new_probabilities
            data['prizeLimits'] = new_prize_limits
            save_data(data)
            message = "Configuration updated successfully!"
        except ValueError:
            message = "Error: Invalid input. Please enter numbers only."
    else:
        message = None
        
    total_probability = sum(data['winProbability'].values())
    
    # Format the timestamps for the winner log
    for winner in data.get('winnerLog', []):
        try:
            # Convert the ISO string back to a datetime object
            timestamp_obj = datetime.fromisoformat(winner['timestamp'])
            # Reformat it to a more readable string
            winner['timestamp'] = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Handle cases where the timestamp might already be in a different format
            pass
    
    return render_template('admin.html', 
                           prizes=data['winProbability'], 
                           limits=data['prizeLimits'], 
                           given=data.get('prizesGiven', {}),
                           winner_log=data.get('winnerLog', []),
                           total_probability=total_probability,
                           message=message)

@app.route('/admin/export-winners')
def export_winners():
    data = load_data()
    winners = data.get('winnerLog', [])
    
    csv_data = io.StringIO()
    csv_writer = csv.writer(csv_data)
    
    # Write headers
    headers = ["Name", "Email", "Prize", "Timestamp"]
    csv_writer.writerow(headers)
    
    # Reformat the timestamp for each winner entry before writing
    for winner in winners:
        try:
            # Convert the ISO string back to a datetime object
            timestamp_obj = datetime.fromisoformat(winner['timestamp'])
            # Reformat it to a more readable string
            formatted_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # If the timestamp is already formatted or invalid, use it as is
            formatted_timestamp = winner['timestamp']

        # Write data row with the formatted timestamp
        csv_writer.writerow([winner['name'], winner['email'], winner['prize'], formatted_timestamp])
    
    output = io.BytesIO(csv_data.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(output, 
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='winner_log.csv')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
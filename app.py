from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    player = db.Column(db.String(10))
    computer = db.Column(db.String(10))
    winner = db.Column(db.String(10))

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect('/login')

# ---------- SIGNUP ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('signup.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/game')

    return render_template('login.html')

# ---------- GAME PAGE ----------
@app.route('/game')
@login_required
def game():
    return render_template('index.html')

# ---------- PLAY GAME (AI ENABLED) ----------
@app.route('/play', methods=['POST'])
@login_required
def play():
    data = request.get_json()
    player_choice = data['choice']
    choices = ["rock", "paper", "scissors"]

    # 🧠 AI LOGIC
    user_moves = Game.query.filter_by(user_id=current_user.id).all()

    if len(user_moves) == 0:
        computer_choice = random.choice(choices)
    else:
        counts = {"rock": 0, "paper": 0, "scissors": 0}
        for move in user_moves:
            counts[move.player] += 1

        predicted = max(counts, key=counts.get)

        counter = {
            "rock": "paper",
            "paper": "scissors",
            "scissors": "rock"
        }

        computer_choice = counter[predicted]

    # ---------- WINNER LOGIC ----------
    if player_choice == computer_choice:
        winner = "draw"
    elif (player_choice == "rock" and computer_choice == "scissors") or \
         (player_choice == "paper" and computer_choice == "rock") or \
         (player_choice == "scissors" and computer_choice == "paper"):
        winner = "player"
    else:
        winner = "computer"

    # ---------- SAVE GAME ----------
    new_game = Game(
        user_id=current_user.id,
        player=player_choice,
        computer=computer_choice,
        winner=winner
    )
    db.session.add(new_game)
    db.session.commit()

    return jsonify({
        "player": player_choice,
        "computer": computer_choice,
        "winner": winner
    })

# ---------- LEADERBOARD ----------
@app.route('/leaderboard')
@login_required
def leaderboard():
    from sqlalchemy import func

    results = db.session.query(
        Game.user_id,
        func.count(Game.id).label("wins")
    ).filter(Game.winner == "player").group_by(Game.user_id).all()

    return render_template('leaderboard.html', results=results)

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')

# ---------- RUN APP ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=10000)
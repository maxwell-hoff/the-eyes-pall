import os
import random
import json
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade as flask_migrate_upgrade
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --------------------- Load Levels Configuration ---------------------

with open('levels.json', 'r') as f:
    LEVELS = json.load(f)

# --------------------- Define Global Variables ---------------------

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')  # Secure your secret key

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Adjust the database URI to be compatible with SQLAlchemy
uri = os.environ.get('DATABASE_URL')  # Get the database URL from environment

if uri is None:
    # Running locally, use SQLite
    uri = 'sqlite:///users.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
else:
    # Heroku PostgreSQL
    if uri.startswith('postgres://'):
        # Fix the URI for SQLAlchemy if it starts with 'postgres://'
        uri = uri.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

# Add this line to create tables when the app starts
# with app.app_context():
#     db.create_all()

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'X'
DRONE_SYMBOLS = ['T1', 'T2', 'T3', 'T4', 'T5']

# Directions for movement
DIRECTIONS = {
    'UP': (-1, 0),     # Up
    'DOWN': (1, 0),    # Down
    'LEFT': (0, -1),   # Left
    'RIGHT': (0, 1),   # Right
    'STAY': (0, 0)     # Stay
}

def clear_screen():
    """Clear the terminal screen for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')

def is_adjacent_to_player_start(pos, player_start_pos, distance=1):
    """
    Check if a position is within a certain distance from the player's starting position.
    """
    return abs(pos[0] - player_start_pos[0]) + abs(pos[1] - player_start_pos[1]) <= distance

# --------------------- User Model ---------------------

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # specify the table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(512), nullable=False)
    total_tries = db.Column(db.Integer, default=0)
    highest_level_completed = db.Column(db.String(50), default='')

    def __repr__(self):
        return f'<User {self.username}>'

class UserLevelStats(db.Model):
    __tablename__ = 'user_level_stats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    level_id = db.Column(db.String(50), nullable=False)
    tries = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('level_stats', lazy=True))

    def __repr__(self):
        return f'<UserLevelStats user_id={self.user_id} level_id={self.level_id} tries={self.tries}>'

# --------------------- User Loader ---------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------- Game Definitions ---------------------

# Define sector shapes and patrol routes for each drone group globally
GROUP_DEFINITIONS = [
    {
        'symbol': 'T1',
        'sector_shape': [(0, 0), (0, 1), (1, 0), (1, 1)],  # 2x2 square
        'patrol_route': [(0, 0), (0, 1), (1, 1), (1, 0)]  # Loop around the square
    },
    {
        'symbol': 'T2',
        'sector_shape': [(0, 0), (0, 1), (0, 2)],
        'patrol_route': [(0, 0), (0, 1), (0, 2), (0, 1)]
    },
    {
        'symbol': 'T3',
        'sector_shape': [(0, 0), (1, 0), (2, 0)],
        'patrol_route': [(0, 0), (1, 0), (2, 0), (1, 0)]
    },
    {
        'symbol': 'T4',
        'sector_shape': [(0, 0), (1, 0), (1, 1)],
        'patrol_route': [(0, 0), (1, 0), (1, 1), (1, 0)]
    },
    {
        'symbol': 'T5',
        'sector_shape': [(0, 1), (1, 0), (1, 1), (1, 2)],
        'patrol_route': [(1, 0), (1, 1), (1, 2), (0, 1), (1, 1)]
    }
]

class DroneGroup:
    def __init__(self, symbol, sector_shape, patrol_route):
        """
        Initialize a drone group.
        """
        self.symbol = symbol
        self.sector_shape = sector_shape
        self.patrol_route = patrol_route
        self.drones = []

class Drone:
    def __init__(self, group, sector_origin, GRID_ROWS, GRID_COLS):
        """
        Initialize a drone.
        """
        self.symbol = group.symbol
        self.group = group
        self.sector_origin = sector_origin
        self.GRID_ROWS = GRID_ROWS
        self.GRID_COLS = GRID_COLS
        self.sector = self.calculate_sector()
        self.patrol_route = self.calculate_patrol_route()
        self.route_length = len(self.patrol_route)
        self.route_index = 0
        self.direction = 1  # 1 for forward, -1 for backward
        self.position = self.patrol_route[self.route_index]

    def calculate_sector(self):
        """
        Calculate the absolute positions of the drone's sector.
        """
        sector = set()
        for rel_pos in self.group.sector_shape:
            abs_pos = (self.sector_origin[0] + rel_pos[0], self.sector_origin[1] + rel_pos[1])
            sector.add(abs_pos)
        return sector

    def calculate_patrol_route(self):
        """
        Calculate the patrol route within the sector.
        """
        route = []
        for rel_pos in self.group.patrol_route:
            abs_pos = (self.sector_origin[0] + rel_pos[0], self.sector_origin[1] + rel_pos[1])
            # Ensure patrol route is within grid boundaries
            if 0 <= abs_pos[0] < self.GRID_ROWS and 0 <= abs_pos[1] < self.GRID_COLS:
                route.append(abs_pos)
            else:
                # Adjust to stay within grid
                clamped_r = max(0, min(self.GRID_ROWS - 1, abs_pos[0]))
                clamped_c = max(0, min(self.GRID_COLS - 1, abs_pos[1]))
                route.append((clamped_r, clamped_c))
        return route

    def move(self):
        """
        Move the drone along its patrol route.
        """
        if self.route_length <= 1:
            print(f"Warning: Drone {self.symbol} has an insufficient patrol route and cannot move.")
            return  # Drone cannot move due to insufficient patrol route

        next_index = self.route_index + self.direction

        # Check if we need to reverse direction
        if next_index >= self.route_length or next_index < 0:
            self.direction *= -1  # Reverse direction
            next_index = self.route_index + self.direction

        self.route_index = next_index
        self.position = self.patrol_route[self.route_index]

# --------------------- Game Initialization ---------------------

def initialize_game(GRID_ROWS, GRID_COLS, PLAYER_START_POS, END_POS, NUM_DRONES, NUM_DRONE_GROUPS, RANDOM_SEED):
    """
    Initialize the game state with drones and their patrol routes.
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Create drone groups
    drone_groups = []
    for group_def in GROUP_DEFINITIONS:
        group = DroneGroup(group_def['symbol'], group_def['sector_shape'], group_def['patrol_route'])
        drone_groups.append(group)

    # Distribute drones among groups
    drones_per_group = [NUM_DRONES // NUM_DRONE_GROUPS] * NUM_DRONE_GROUPS
    for i in range(NUM_DRONES % NUM_DRONE_GROUPS):
        drones_per_group[i] += 1  # Distribute remainder

    # Initialize drones and assign sectors
    drones = []
    assigned_positions = set()  # Positions already assigned to sectors

    # Set the random seed for reproducibility
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    for i, group in enumerate(drone_groups):
        num_drones_in_group = drones_per_group[i]
        for _ in range(num_drones_in_group):
            # Find a valid sector origin
            sector_placed = False
            for attempt in range(100):  # Limit attempts to prevent infinite loops
                max_row = GRID_ROWS - max(r for r, c in group.sector_shape)
                max_col = GRID_COLS - max(c for r, c in group.sector_shape)
                if max_row <= 0 or max_col <= 0:
                    continue  # Sector shape is too large for the grid
                origin_row = random.randint(0, max_row - 1)
                origin_col = random.randint(0, max_col - 1)
                sector_origin = (origin_row, origin_col)
                sector = set((sector_origin[0] + r, sector_origin[1] + c) for r, c in group.sector_shape)

                # Check if sector overlaps with assigned positions or is adjacent to player start
                if sector.isdisjoint(assigned_positions) and not any(is_adjacent_to_player_start(pos, PLAYER_START_POS) for pos in sector):
                    assigned_positions.update(sector)
                    drone = Drone(group, sector_origin, GRID_ROWS, GRID_COLS)
                    drones.append(drone)
                    group.drones.append(drone)
                    sector_placed = True
                    break

            if not sector_placed:
                print(f"Warning: Could not place a sector for drone in group {group.symbol}")
                continue

    return player_pos, end_pos, drones

def update_user_stats(won):
    level_id = session.get('level_id')
    if level_id is None:
        level_id = 'unknown'  # Handle missing level_id

    # Update total tries
    current_user.total_tries = (current_user.total_tries or 0) + 1

    # Update per-level tries
    # Find or create UserLevelStats for this user and level
    level_stats = UserLevelStats.query.filter_by(user_id=current_user.id, level_id=level_id).first()
    if level_stats is None:
        level_stats = UserLevelStats(user_id=current_user.id, level_id=level_id, tries=1)
        db.session.add(level_stats)
    else:
        level_stats.tries += 1

    # If the user has won, update highest_level_completed if necessary
    if won:
        level_stats.completed = True

        # Determine level order
        level_indices = {level['id']: idx for idx, level in enumerate(LEVELS)}
        current_level_index = level_indices.get(level_id, -1)

        # Get current highest level index
        if current_user.highest_level_completed:
            highest_level_index = level_indices.get(current_user.highest_level_completed, -1)
        else:
            highest_level_index = -1

        if current_level_index > highest_level_index:
            current_user.highest_level_completed = level_id

    db.session.commit()

    # Return updated stats
    total_tries = current_user.total_tries
    highest_level_completed = current_user.highest_level_completed or 'None'
    level_tries = level_stats.tries

    return {
        'total_tries': total_tries,
        'highest_level_completed': highest_level_completed,
        'level_tries': level_tries
    }

def draw_grid(player_pos, end_pos, drones, GRID_ROWS_, GRID_COLS_):
    """
    Create the current state of the grid.
    """
    grid = [[EMPTY_SYMBOL for _ in range(GRID_COLS_)] for _ in range(GRID_ROWS_)]

    # Place the end position
    er, ec = end_pos
    grid[er][ec] = END_SYMBOL

    # Place drones
    drone_positions = {}
    for drone in drones:
        r, c = drone.position
        if (r, c) == player_pos:
            continue  # Collision handled separately
        if (r, c) in drone_positions:
            drone_positions[(r, c)].add(drone.symbol)
        else:
            drone_positions[(r, c)] = {drone.symbol}

    for (r, c), symbols in drone_positions.items():
        if len(symbols) == 1:
            grid[r][c] = symbols.pop()
        else:
            grid[r][c] = '*'  # Indicate multiple drones

    # Place the player if within grid boundaries
    pr, pc = player_pos
    if 0 <= pr < GRID_ROWS_ and 0 <= pc < GRID_COLS_:
        grid[pr][pc] = PLAYER_SYMBOL

    return grid

def is_collision(player_pos, drones):
    """
    Check if the player has collided with any drone.
    """
    for drone in drones:
        if player_pos == drone.position:
            return True
    return False

# --------------------- Flask Web Interface ---------------------

# --------------------- Authentication Routes ---------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check for special characters in username
        if not username.isalnum():
            flash('Username must be alphanumeric and contain no special characters.')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('level_selection'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check for special characters in username
        if not username.isalnum():
            flash('Username must be alphanumeric and contain no special characters.')
            return redirect(url_for('signup'))
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('signup'))
        # Create new user
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/level_selection')
@login_required
def level_selection():
    # Render the level selection screen
    return render_template('level_selection.html', levels=LEVELS)

@app.route('/level_intro/<level_id>')
def level_intro(level_id):
    # Find the level configuration
    level_config = next((level for level in LEVELS if level['id'] == level_id), None)
    if not level_config:
        return "Level not found", 404

    # Store level configuration in session
    session['level_config'] = level_config

    # Get intro text and print speed
    intro_text = level_config.get('intro_text', '')
    print_speed = level_config.get('print_speed', 200)  # Default to 200ms if not specified

    return render_template('level_intro.html', intro_text=intro_text, print_speed=print_speed, level_id=level_id)

@app.route('/start_game/<level_id>')
@login_required
def start_game(level_id):
    # Find the level configuration
    level_config = next((level for level in LEVELS if level['id'] == level_id), None)
    if not level_config:
        return "Level not found", 404

    # Store level configuration in session
    session['level_config'] = level_config
    session['level_id'] = level_id  # Store level_id in session
    session['initialized'] = False  # Reset game initialization

    return redirect(url_for('game'))

def initialize_web_game():
    """Initialize the game state for the web version."""
    level_config = session['level_config']

    # Extract level parameters
    GRID_ROWS = level_config['grid_rows']
    GRID_COLS = level_config['grid_cols']
    PLAYER_START_POS = tuple(level_config['player_start_pos'])
    END_POS = tuple(level_config['end_pos'])
    NUM_DRONES = level_config['num_drones']
    NUM_DRONE_GROUPS = level_config['num_drone_groups']

    # Set random seed for reproducibility
    RANDOM_SEED = level_config['random_seed']
    # RANDOM_SEED = level_config.get('random_seed', None)

    # Initialize game state
    player_pos, end_pos, drones = initialize_game(
        GRID_ROWS, GRID_COLS, PLAYER_START_POS, END_POS, NUM_DRONES, NUM_DRONE_GROUPS, RANDOM_SEED
    )
    session['player_pos'] = player_pos
    session['end_pos'] = end_pos
    session['grid_rows'] = GRID_ROWS
    session['grid_cols'] = GRID_COLS
    session['player_start_pos'] = PLAYER_START_POS
    session['turn'] = 0
    session['max_turns'] = 200
    # Store drones as list of dicts for serialization
    session['drones'] = [
        {
            'symbol': drone.symbol,
            'position': drone.position,
            'route_index': drone.route_index,
            'direction': drone.direction,
            'sector_origin': drone.sector_origin
        } for drone in drones
    ]
    session['game_over'] = False
    session['message'] = ''
    session['initialized'] = True

@app.route('/game')
@login_required
def game():
    # Initialize the game if not already started
    if not session.get('initialized', False):
        initialize_web_game()

    # Get user stats
    total_tries = current_user.total_tries or 0
    highest_level_completed = current_user.highest_level_completed or 'None'

    # Get per-level tries
    level_id = session.get('level_id')
    level_stats = UserLevelStats.query.filter_by(user_id=current_user.id, level_id=level_id).first()
    level_tries = level_stats.tries if level_stats else 0

    return render_template('index.html', total_tries=total_tries,
                           highest_level_completed=highest_level_completed,
                           level_tries=level_tries)

@app.route('/game_state', methods=['GET'])
@login_required
def get_game_state():
    GRID_ROWS = session['grid_rows']
    GRID_COLS = session['grid_cols']
    PLAYER_START_POS = tuple(session['player_start_pos'])
    player_pos = tuple(session['player_pos'])
    end_pos = tuple(session['end_pos'])
    drones_data = session['drones']
    drones = []

    # Reconstruct drone groups
    drone_groups = {group_def['symbol']: DroneGroup(
        group_def['symbol'], group_def['sector_shape'], group_def['patrol_route']
    ) for group_def in GROUP_DEFINITIONS}

    # Reconstruct drones
    for drone_data in drones_data:
        symbol = drone_data['symbol']
        position = tuple(drone_data['position'])
        route_index = drone_data['route_index']
        direction = drone_data['direction']
        sector_origin = tuple(drone_data['sector_origin'])
        group = drone_groups.get(symbol)
        if not group:
            continue  # Skip if group not found

        drone = Drone(group, sector_origin, GRID_ROWS, GRID_COLS)
        drone.position = position
        drone.route_index = route_index
        drone.direction = direction
        drones.append(drone)

    grid = draw_grid(player_pos, end_pos, drones, GRID_ROWS, GRID_COLS)

    start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL

    return jsonify({
        'grid': grid,
        'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol},
        'turn': session['turn'],
        'game_over': session['game_over'],
        'message': session.get('message', ''),
        'player_pos': session['player_pos'],
        'drones': [
            {
                'symbol': drone_data['symbol'],
                'position': drone_data['position']
            } for drone_data in session['drones']
        ]
    })

def is_valid_move_from_start_box(move, PLAYER_START_POS, GRID_ROWS, GRID_COLS):
    if move == 'STAY':
        return True  # Allow staying in the start position
    if PLAYER_START_POS[0] == -1:
        return move == 'DOWN'
    elif PLAYER_START_POS[0] == GRID_ROWS:
        return move == 'UP'
    elif PLAYER_START_POS[1] == -1:
        return move == 'RIGHT'
    elif PLAYER_START_POS[1] == GRID_COLS:
        return move == 'LEFT'
    return False  # Should not happen

@app.route('/move', methods=['POST'])
@login_required
def move():
    if session.get('game_over', False):
        return jsonify({'message': session.get('message', 'Game Over'), 'game_over': True})

    GRID_ROWS = session['grid_rows']
    GRID_COLS = session['grid_cols']
    PLAYER_START_POS = tuple(session['player_start_pos'])

    data = request.get_json()
    move = data.get('move')
    move_dir = DIRECTIONS.get(move.upper(), DIRECTIONS['STAY'])

    player_pos = tuple(session['player_pos'])
    old_player_pos = player_pos  # Record old position

    new_r = player_pos[0] + move_dir[0]
    new_c = player_pos[1] + move_dir[1]

    # Enforce movement rules when in start box
    if player_pos == PLAYER_START_POS:
        if not is_valid_move_from_start_box(move, PLAYER_START_POS, GRID_ROWS, GRID_COLS):
            session['message'] = "🚫 Invalid move from the start position."
            return jsonify({'message': session['message'], 'game_over': False})

    # Enforce movement rules when moving back into the start box
    if (new_r, new_c) == PLAYER_START_POS:
        if not is_valid_move_from_start_box(move, PLAYER_START_POS, GRID_ROWS, GRID_COLS):
            session['message'] = "🚫 Invalid move into the start position."
            return jsonify({'message': session['message'], 'game_over': False})

    # Adjusted boundary checks
    if not (-1 <= new_r < GRID_ROWS) or not (-1 <= new_c < GRID_COLS):
        session['message'] = "🚫 Move out of bounds. Try again."
        return jsonify({'message': session['message'], 'game_over': False})

    # Update player's position AFTER all checks have passed
    player_pos = (new_r, new_c)
    session['player_pos'] = player_pos

    # Reconstruct drone groups
    drone_groups = {group_def['symbol']: DroneGroup(
        group_def['symbol'], group_def['sector_shape'], group_def['patrol_route']
    ) for group_def in GROUP_DEFINITIONS}

    # Reconstruct drones
    drones = []
    for drone_data in session['drones']:
        symbol = drone_data['symbol']
        position = tuple(drone_data['position'])
        route_index = drone_data['route_index']
        direction = drone_data['direction']
        sector_origin = tuple(drone_data['sector_origin'])
        group = drone_groups.get(symbol)
        if not group:
            continue  # Skip if group not found

        drone = Drone(group, sector_origin, GRID_ROWS, GRID_COLS)
        drone.position = position
        drone.route_index = route_index
        drone.direction = direction
        drones.append(drone)

    # Check for collision after player's move
    if 0 <= new_r < GRID_ROWS and 0 <= new_c < GRID_COLS:
        if is_collision(player_pos, drones):
            session['game_over'] = True
            session['won'] = False
            updated_stats = update_user_stats(won=False)
            session['message'] = "A gunshot rings out in the distnace. You turn the radio frequency preemptively."
            # Prepare start_box data
            start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL
            return jsonify({
                'message': session['message'],
                'game_over': True,
                'player_move': {'from': old_player_pos, 'to': player_pos},
                'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol},
                'player_pos': session['player_pos'],
                'updated_stats': updated_stats
            })

    # Record drone movements
    drone_moves = []

    # Move drones
    for drone in drones:
        old_pos = drone.position
        drone.move()
        new_pos = drone.position
        drone_moves.append({
            'symbol': drone.symbol,
            'from': old_pos,
            'to': new_pos
        })

    # Check for collision after drones' move
    if 0 <= player_pos[0] < GRID_ROWS and 0 <= player_pos[1] < GRID_COLS:
        if is_collision(player_pos, drones):
            session['game_over'] = True
            session['won'] = False
            updated_stats = update_user_stats(won=False)
            session['message'] = "A gunshot rings out in the distnace. You turn the radio frequency preemptively."
            # Update drones in session
            session['drones'] = [
                {
                    'symbol': drone.symbol,
                    'position': drone.position,
                    'route_index': drone.route_index,
                    'direction': drone.direction,
                    'sector_origin': drone.sector_origin
                } for drone in drones
            ]
            # Prepare start_box data
            start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL
            return jsonify({
                'message': session['message'],
                'game_over': True,
                'player_move': {'from': old_player_pos, 'to': player_pos},
                'drone_moves': drone_moves,
                'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol},
                'player_pos': session['player_pos'],
                'updated_stats': updated_stats
            })

    # Check if player has reached the end
    if player_pos == tuple(session['end_pos']):
        session['game_over'] = True
        session['won'] = True
        updated_stats = update_user_stats(won=True)
        session['message'] = "You've reached your target."
        # Update drones in session
        session['drones'] = [
            {
                'symbol': drone.symbol,
                'position': drone.position,
                'route_index': drone.route_index,
                'direction': drone.direction,
                'sector_origin': drone.sector_origin
            } for drone in drones
        ]
        # Prepare start_box data
        start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL
        return jsonify({
            'message': session['message'],
            'game_over': True,
            'player_move': {'from': old_player_pos, 'to': player_pos},
            'drone_moves': drone_moves,
            'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol},
            'player_pos': session['player_pos'],
            'updated_stats': updated_stats
        })

    # Update drones in session
    session['drones'] = [
        {
            'symbol': drone.symbol,
            'position': drone.position,
            'route_index': drone.route_index,
            'direction': drone.direction,
            'sector_origin': drone.sector_origin
        } for drone in drones
    ]

    # Increment turn
    session['turn'] += 1

    # Optional: Check for max turns
    if session['turn'] >= session.get('max_turns', 200):
        session['game_over'] = True
        session['won'] = False
        updated_stats = update_user_stats(won=False)
        session['message'] = "Drone tracking goes dark. There's nothing more you can do to help."
        # Prepare start_box data
        start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL
        return jsonify({
            'message': session['message'],
            'game_over': True,
            'player_move': {'from': old_player_pos, 'to': player_pos},
            'drone_moves': drone_moves,
            'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol},
            'player_pos': session['player_pos'],
            'updated_stats': updated_stats
        })

    session['message'] = ''

    # Prepare start_box data
    start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL

    return jsonify({
        'message': 'Move successful',
        'game_over': False,
        'player_move': {'from': old_player_pos, 'to': player_pos},
        'drone_moves': drone_moves,
        'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol},
        'player_pos': session['player_pos']
    })

# --------------------- Flask Initialization ---------------------

@app.route('/reset', methods=['POST'])
@login_required
def reset():
    """Reset the game state."""
    initialize_web_game()
    # Retrieve updated stats
    level_id = session.get('level_id')
    level_stats = UserLevelStats.query.filter_by(user_id=current_user.id, level_id=level_id).first()
    level_tries = level_stats.tries if level_stats else 0
    updated_stats = {
        'total_tries': current_user.total_tries or 0,
        'highest_level_completed': current_user.highest_level_completed or 'None',
        'level_tries': level_tries  # Use current level tries
    }
    return jsonify({'message': 'Game has been reset.', 'game_over': False, 'updated_stats': updated_stats})

# --------------------- Apply Migrations Function ---------------------

def apply_migrations():
    with app.app_context():
        try:
            # Try to run a simple query to check if the database is initialized
            db.session.execute('SELECT 1')
        except OperationalError:
            # Database is not initialized, apply migrations
            flask_migrate_upgrade()

# --------------------- Main Entry Point ---------------------

if __name__ == '__main__':
    apply_migrations()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
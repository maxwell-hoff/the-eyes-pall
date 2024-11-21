import os
import time
import random
from flask import Flask, render_template, request, session, jsonify
from flask_session import Session

# --------------------- Configurable Parameters ---------------------

# Grid Configuration
GRID_ROWS = 15  # Number of rows in the grid
GRID_COLS = 10  # Number of columns in the grid

# Player Configuration
PLAYER_START_POS = (-1, 1)  # Player starts above the grid at column 1
END_POS = (GRID_ROWS - 1, GRID_COLS - 1)  # End position inside the grid

# Drone Configuration
NUM_DRONES = 25          # Total number of drones
NUM_DRONE_GROUPS = 5     # Number of drone groups

# Random Seed for Reproducibility
RANDOM_SEED = 42  # Set to an integer value for reproducible results

# --------------------- End of Configurable Parameters ---------------------

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

def is_adjacent_to_player_start(pos, distance=1):
    """
    Check if a position is within a certain distance from the player's starting position.

    :param pos: Tuple (row, col) position to check.
    :param distance: Manhattan distance threshold.
    :return: Boolean indicating if position is within the threshold.
    """
    return abs(pos[0] - PLAYER_START_POS[0]) + abs(pos[1] - PLAYER_START_POS[1]) <= distance

# --------------------- Game Definitions ---------------------

# Define sector shapes and patrol routes for each drone group globally
GROUP_DEFINITIONS = [
    {
        'symbol': 'T1',
        'sector_shape': [(0, 0), (0, 1), (1, 0), (1, 1)],  # 2x2 square
        'patrol_route': [(0, 0), (0, 1), (1, 1), (1, 0)]  # Loop around the square
    },
    # Include T2, T3, T4, T5 definitions as in your code
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

        :param symbol: String representing the drone group.
        :param sector_shape: List of relative positions defining the sector shape.
        :param patrol_route: List of positions defining the patrol route within the sector.
        """
        self.symbol = symbol
        self.sector_shape = sector_shape
        self.patrol_route = patrol_route
        self.drones = []

class Drone:
    def __init__(self, group, sector_origin):
        """
        Initialize a drone.

        :param group: The DroneGroup object the drone belongs to.
        :param sector_origin: The top-left position of the drone's sector.
        """
        self.symbol = group.symbol
        self.group = group
        self.sector_origin = sector_origin
        self.sector = self.calculate_sector()
        self.patrol_route = self.calculate_patrol_route()
        self.route_length = len(self.patrol_route)
        self.route_index = 0
        self.direction = 1  # 1 for forward, -1 for backward
        self.position = self.patrol_route[self.route_index]

    def calculate_sector(self):
        """
        Calculate the absolute positions of the drone's sector based on its origin and group sector shape.

        :return: Set of positions representing the sector.
        """
        sector = set()
        for rel_pos in self.group.sector_shape:
            abs_pos = (self.sector_origin[0] + rel_pos[0], self.sector_origin[1] + rel_pos[1])
            sector.add(abs_pos)
        return sector

    def calculate_patrol_route(self):
        """
        Calculate the patrol route within the sector, adjusted for the sector's origin.

        :return: List of positions representing the patrol route.
        """
        route = []
        for rel_pos in self.group.patrol_route:
            abs_pos = (self.sector_origin[0] + rel_pos[0], self.sector_origin[1] + rel_pos[1])
            # Ensure patrol route is within grid boundaries
            if 0 <= abs_pos[0] < GRID_ROWS and 0 <= abs_pos[1] < GRID_COLS:
                route.append(abs_pos)
            else:
                # If out of bounds, adjust to stay within grid
                clamped_r = max(0, min(GRID_ROWS - 1, abs_pos[0]))
                clamped_c = max(0, min(GRID_COLS - 1, abs_pos[1]))
                route.append((clamped_r, clamped_c))
        return route

    def move(self):
        """
        Move the drone along its patrol route, reversing direction at the ends if necessary.
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

def initialize_game():
    """
    Initialize the game state with drones and their patrol routes.

    :return: Tuple (player_pos, end_pos, drones)
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
                if sector.isdisjoint(assigned_positions) and not any(is_adjacent_to_player_start(pos) for pos in sector):
                    assigned_positions.update(sector)
                    drone = Drone(group, sector_origin)
                    drones.append(drone)
                    group.drones.append(drone)
                    sector_placed = True
                    break

            if not sector_placed:
                print(f"Warning: Could not place a sector for drone in group {group.symbol}")
                continue

    return player_pos, end_pos, drones

def draw_grid(player_pos, end_pos, drones):
    """
    Create the current state of the grid.

    :param player_pos: Tuple (row, col) of the player's position.
    :param end_pos: Tuple (row, col) of the end position.
    :param drones: List of Drone objects.
    :return: List of lists representing the grid.
    """
    grid = [[EMPTY_SYMBOL for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

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
    if 0 <= pr < GRID_ROWS and 0 <= pc < GRID_COLS:
        grid[pr][pc] = PLAYER_SYMBOL

    return grid

def is_collision(player_pos, drones):
    """
    Check if the player has collided with any drone.

    :param player_pos: Tuple (row, col) of the player's position.
    :param drones: List of Drone objects.
    :return: Boolean indicating collision.
    """
    for drone in drones:
        if player_pos == drone.position:
            return True
    return False

# --------------------- Flask Web Interface ---------------------

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
def index():
    # Initialize the game if not already started
    if 'initialized' not in session:
        initialize_web_game()
    return render_template('index.html')

def initialize_web_game():
    """Initialize the game state for the web version."""
    player_pos, end_pos, drones = initialize_game()
    session['player_pos'] = player_pos
    session['end_pos'] = end_pos
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

@app.route('/game_state', methods=['GET'])
def get_game_state():
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

        drone = Drone(group, sector_origin)
        drone.position = position
        drone.route_index = route_index
        drone.direction = direction
        drones.append(drone)

    grid = draw_grid(player_pos, end_pos, drones)

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

def is_valid_move_from_start_box(move):
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
def move():
    if session.get('game_over', False):
        return jsonify({'message': session.get('message', 'Game Over'), 'game_over': True})

    data = request.get_json()
    move = data.get('move')
    move_dir = DIRECTIONS.get(move.upper(), DIRECTIONS['STAY'])

    player_pos = tuple(session['player_pos'])
    old_player_pos = player_pos  # Record old position

    new_r = player_pos[0] + move_dir[0]
    new_c = player_pos[1] + move_dir[1]

    # Enforce movement rules when in start box
    if player_pos == PLAYER_START_POS:
        if not is_valid_move_from_start_box(move):
            session['message'] = "🚫 Invalid move from the start position."
            return jsonify({'message': session['message']})

    # Enforce movement rules when moving back into the start box
    if (new_r, new_c) == PLAYER_START_POS:
        # Determine the required move to enter the start box
        if not is_valid_move_from_start_box(move):
            session['message'] = "🚫 Invalid move into the start position."
            return jsonify({'message': session['message']})

    # Check boundaries
    if not (-1 <= new_r <= GRID_ROWS) or not (-1 <= new_c <= GRID_COLS):
        session['message'] = "🚫 Move out of bounds. Try again."
        return jsonify({'message': session['message']})

    # Update player's position
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

        drone = Drone(group, sector_origin)
        drone.position = position
        drone.route_index = route_index
        drone.direction = direction
        drones.append(drone)

    # Check for collision after player's move (only if inside the grid)
    if 0 <= new_r < GRID_ROWS and 0 <= new_c < GRID_COLS:
        if is_collision(player_pos, drones):
            session['game_over'] = True
            session['message'] = "💥 Oh no! You've been caught by a drone. Game Over. 💥"
            # Prepare start_box data
            start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL
            return jsonify({
                'message': session['message'],
                'game_over': True,
                'player_move': {'from': old_player_pos, 'to': player_pos},
                'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol}
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

    # Check for collision after drones' move (only if player is inside the grid)
    if 0 <= player_pos[0] < GRID_ROWS and 0 <= player_pos[1] < GRID_COLS:
        if is_collision(player_pos, drones):
            session['game_over'] = True
            session['message'] = "💥 A drone has moved into your square. Game Over. 💥"
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
                'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol}
            })

    # Check if player has reached the end
    if player_pos == tuple(session['end_pos']):
        session['game_over'] = True
        session['message'] = "🎉 Congratulations! You've reached the end and won the game! 🎉"
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
            'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol}
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
        session['message'] = "⏰ Maximum turns reached. Game Over."
        # Prepare start_box data
        start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL
        return jsonify({
            'message': session['message'],
            'game_over': True,
            'player_move': {'from': old_player_pos, 'to': player_pos},
            'drone_moves': drone_moves,
            'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol}
        })

    session['message'] = ''
    # Prepare start_box data
    start_box_symbol = PLAYER_SYMBOL if player_pos == PLAYER_START_POS else EMPTY_SYMBOL

    return jsonify({
        'message': 'Move successful',
        'game_over': False,
        'player_move': {'from': old_player_pos, 'to': player_pos},
        'drone_moves': drone_moves,
        'start_box': {'position': PLAYER_START_POS, 'symbol': start_box_symbol}
    })

# --------------------- Flask Initialization ---------------------

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the game state."""
    initialize_web_game()
    return jsonify({'message': 'Game has been reset.', 'game_over': False})

# --------------------- Main Entry Point ---------------------

if __name__ == '__main__':
    import sys
    if 'cli' in sys.argv:
        pass  # Adjust CLI code as needed
    else:
        app.run(debug=True)
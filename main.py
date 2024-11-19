import os
import time
import random

# --------------------- Configurable Parameters ---------------------

# Grid Configuration
GRID_SIZE = 10  # Size of the grid (10x10)

# Player Configuration
PLAYER_START_POS = (0, 0)  # Starting position of the player
END_POS = (GRID_SIZE - 1, GRID_SIZE - 1)  # End position

# Drone Configuration
NUM_DRONES = 25          # Total number of drones
NUM_DRONE_GROUPS = 5     # Number of drone groups

# Random Seed for Reproducibility
RANDOM_SEED = 42  # Set to an integer value for reproducible results

# --------------------- End of Configurable Parameters ---------------------

# Set the random seed for reproducibility
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

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
            route.append(abs_pos)
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

def initialize_game():
    """
    Initialize the game state with drones and their patrol routes.

    :return: Tuple (player_pos, end_pos, drones)
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Define sector shapes and patrol routes for each drone group
    group_definitions = [
        {
            'symbol': 'T1',
            'sector_shape': [(0, 0), (0, 1), (1, 0), (1, 1)],  # 2x2 square
            'patrol_route': [(0, 0), (0, 1), (1, 1), (1, 0)]  # Loop around the square
        },
        {
            'symbol': 'T2',
            'sector_shape': [(0, 0), (0, 1), (0, 2)],  # Horizontal line of 3 squares
            'patrol_route': [(0, 0), (0, 1), (0, 2), (0, 1)]  # Back and forth
        },
        {
            'symbol': 'T3',
            'sector_shape': [(0, 0), (1, 0), (2, 0)],  # Vertical line of 3 squares
            'patrol_route': [(0, 0), (1, 0), (2, 0), (1, 0)]  # Up and down
        },
        {
            'symbol': 'T4',
            'sector_shape': [(0, 0), (1, 0), (1, 1)],  # L-shape
            'patrol_route': [(0, 0), (1, 0), (1, 1), (1, 0)]  # Loop around the L
        },
        {
            'symbol': 'T5',
            'sector_shape': [(0, 1), (1, 0), (1, 1), (1, 2)],  # T-shape
            'patrol_route': [(1, 0), (1, 1), (1, 2), (0, 1), (1, 1)]  # Traverse the T
        }
    ]

    # Create drone groups
    drone_groups = []
    for group_def in group_definitions:
        group = DroneGroup(group_def['symbol'], group_def['sector_shape'], group_def['patrol_route'])
        drone_groups.append(group)

    # Distribute drones among groups
    drones_per_group = [NUM_DRONES // NUM_DRONE_GROUPS] * NUM_DRONE_GROUPS
    for i in range(NUM_DRONES % NUM_DRONE_GROUPS):
        drones_per_group[i] += 1  # Distribute remainder

    # Initialize drones and assign sectors
    drones = []
    assigned_positions = set([PLAYER_START_POS])  # Positions already assigned to sectors
    for i, group in enumerate(drone_groups):
        num_drones_in_group = drones_per_group[i]
        for _ in range(num_drones_in_group):
            # Find a valid sector origin
            sector_placed = False
            for attempt in range(100):  # Limit attempts to prevent infinite loops
                max_row = GRID_SIZE - max(r for r, c in group.sector_shape)
                max_col = GRID_SIZE - max(c for r, c in group.sector_shape)
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
    grid = [[EMPTY_SYMBOL for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

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
            grid[r][c] = '*'  # Indicate multiple drones (should not occur)

    # Place the player
    pr, pc = player_pos
    grid[pr][pc] = PLAYER_SYMBOL

    return grid

def print_grid(grid):
    """Print the grid to the console."""
    # Print the grid with row and column indices
    header = "    " + " ".join([f"{c:2}" for c in range(GRID_SIZE)])
    print(header)
    for idx, row in enumerate(grid):
        row_str = f"{idx:2} | " + " ".join([f"{cell:2}" for cell in row])
        print(row_str)
    print("\nLegend: P=Player, X=End, T1/T2/T3/T4/T5= Drone Groups, *=Multiple Drones, .=Empty")

def get_player_move():
    """
    Prompt the player for a move and return the corresponding direction.

    :return: Tuple (dr, dc) representing the move direction.
    """
    MOVES = {
        'w': DIRECTIONS['UP'],      # Up
        's': DIRECTIONS['DOWN'],    # Down
        'a': DIRECTIONS['LEFT'],    # Left
        'd': DIRECTIONS['RIGHT'],   # Right
        'f': DIRECTIONS['STAY']     # Stay
    }
    move = input("\nMove (w=up, s=down, a=left, d=right, f=stay): ").strip().lower()
    if move not in MOVES:
        print("Invalid move. Please enter 'w', 'a', 's', 'd', or 'f'.")
        return get_player_move()
    return MOVES[move]

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

# --------------------- Command-Line Interface ---------------------

def play_cli():
    """Play the game using the command-line interface."""
    print("Welcome to 'Pall of the Eye' - Drone Group Patrol Edition!")

    # Initialize the game
    player_pos, end_pos, drones = initialize_game()

    turn = 0
    max_turns = 200  # Adjust as needed

    while turn < max_turns:
        clear_screen()
        print(f"Turn: {turn}")
        grid = draw_grid(player_pos, end_pos, drones)
        print_grid(grid)

        # Check if player has reached the end
        if player_pos == end_pos:
            print("🎉 Congratulations! You've reached the end and won the game! 🎉")
            return

        # Get player move
        move = get_player_move()
        new_r = player_pos[0] + move[0]
        new_c = player_pos[1] + move[1]

        # Check boundaries
        if 0 <= new_r < GRID_SIZE and 0 <= new_c < GRID_SIZE:
            player_pos = (new_r, new_c)
        else:
            print("🚫 Move out of bounds. Try again.")
            time.sleep(1)
            continue

        # Check for collision after player's move
        if is_collision(player_pos, drones):
            clear_screen()
            print(f"Turn: {turn + 1}")
            grid = draw_grid(player_pos, end_pos, drones)
            print_grid(grid)
            print("💥 Oh no! You've been caught by a drone. Game Over. 💥")
            return

        # Move drones
        for drone in drones:
            drone.move()

        # Check for collision after drones' move
        if is_collision(player_pos, drones):
            clear_screen()
            print(f"Turn: {turn + 1}")
            grid = draw_grid(player_pos, end_pos, drones)
            print_grid(grid)
            print("💥 A drone has moved into your square. Game Over. 💥")
            return

        turn += 1

    print("⏰ Maximum turns reached. Game Over.")

# --------------------- Flask Web Interface ---------------------

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
def index():
    if 'game_state' not in session:
        # Initialize the game
        player_pos, end_pos, drones = initialize_game()
        session['player_pos'] = player_pos
        session['end_pos'] = end_pos
        session['turn'] = 0
        session['max_turns'] = 200
        session['drones'] = [(drone.group.symbol, drone.position, drone.route_index, drone.direction, drone.sector_origin) for drone in drones]
        session['game_over'] = False

    return render_template('index.html')

@app.route('/game_state', methods=['GET'])
def get_game_state():
    player_pos = tuple(session['player_pos'])
    end_pos = tuple(session['end_pos'])
    drones = []
    for data in session['drones']:
        symbol, position, route_index, direction, sector_origin = data
        drone = Drone(next(group for group in create_drone_groups() if group.symbol == symbol), sector_origin)
        drone.position = tuple(position)
        drone.route_index = route_index
        drone.direction = direction
        drones.append(drone)
    grid = draw_grid(player_pos, end_pos, drones)
    return jsonify({
        'grid': grid,
        'turn': session['turn'],
        'game_over': session['game_over'],
        'message': session.get('message', '')
    })

def create_drone_groups():
    # Define sector shapes and patrol routes for each drone group
    group_definitions = [
        {
            'symbol': 'T1',
            'sector_shape': [(0, 0), (0, 1), (1, 0), (1, 1)],  # 2x2 square
            'patrol_route': [(0, 0), (0, 1), (1, 1), (1, 0)]  # Loop around the square
        },
        {
            'symbol': 'T2',
            'sector_shape': [(0, 0), (0, 1), (0, 2)],  # Horizontal line of 3 squares
            'patrol_route': [(0, 0), (0, 1), (0, 2), (0, 1)]  # Back and forth
        },
        {
            'symbol': 'T3',
            'sector_shape': [(0, 0), (1, 0), (2, 0)],  # Vertical line of 3 squares
            'patrol_route': [(0, 0), (1, 0), (2, 0), (1, 0)]  # Up and down
        },
        {
            'symbol': 'T4',
            'sector_shape': [(0, 0), (1, 0), (1, 1)],  # L-shape
            'patrol_route': [(0, 0), (1, 0), (1, 1), (1, 0)]  # Loop around the L
        },
        {
            'symbol': 'T5',
            'sector_shape': [(0, 1), (1, 0), (1, 1), (1, 2)],  # T-shape
            'patrol_route': [(1, 0), (1, 1), (1, 2), (0, 1), (1, 1)]  # Traverse the T
        }
    ]

    # Create drone groups
    drone_groups = []
    for group_def in group_definitions:
        group = DroneGroup(group_def['symbol'], group_def['sector_shape'], group_def['patrol_route'])
        drone_groups.append(group)
    return drone_groups

@app.route('/move', methods=['POST'])
def move():
    if session['game_over']:
        return jsonify({'message': 'Game Over', 'game_over': True})

    data = request.get_json()
    move = data.get('move')
    move_dir = DIRECTIONS.get(move.upper(), (0, 0))

    player_pos = tuple(session['player_pos'])
    new_r = player_pos[0] + move_dir[0]
    new_c = player_pos[1] + move_dir[1]

    if not (0 <= new_r < GRID_SIZE and 0 <= new_c < GRID_SIZE):
        session['message'] = "🚫 Move out of bounds. Try again."
        return jsonify({'message': session['message']})

    player_pos = (new_r, new_c)

    # Reconstruct drones
    drones = []
    for data in session['drones']:
        symbol, position, route_index, direction, sector_origin = data
        drone = Drone(next(group for group in create_drone_groups() if group.symbol == symbol), sector_origin)
        drone.position = tuple(position)
        drone.route_index = route_index
        drone.direction = direction
        drones.append(drone)

    # Check for collision after player's move
    if is_collision(player_pos, drones):
        session['game_over'] = True
        session['message'] = "💥 Oh no! You've been caught by a drone. Game Over. 💥"
        return jsonify({'message': session['message'], 'game_over': True})

    # Move drones
    for drone in drones:
        drone.move()

    # Check for collision after drones' move
    if is_collision(player_pos, drones):
        session['game_over'] = True
        session['message'] = "💥 A drone has moved into your square. Game Over. 💥"
        return jsonify({'message': session['message'], 'game_over': True})

    # Update session data
    session['player_pos'] = player_pos
    session['drones'] = [(drone.group.symbol, drone.position, drone.route_index, drone.direction, drone.sector_origin) for drone in drones]
    session['turn'] += 1

    # Check if player has reached the end
    if player_pos == tuple(session['end_pos']):
        session['game_over'] = True
        session['message'] = "🎉 Congratulations! You've reached the end and won the game! 🎉"
        return jsonify({'message': session['message'], 'game_over': True})

    session['message'] = ''
    return jsonify({'message': 'Move successful', 'game_over': False})

if __name__ == '__main__':
    import sys
    if 'cli' in sys.argv:
        play_cli()
    else:
        app.run(debug=True)
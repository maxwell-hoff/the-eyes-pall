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
NUM_DRONES = 5  # Total number of drones
DRONE_PATROL_STRATEGY = 'row'  # 'row', 'column', or 'spiral'

# Random Seed for Reproducibility
RANDOM_SEED = None  # Set to an integer value for reproducible results, e.g., 42

# --------------------- End of Configurable Parameters ---------------------

# Set the random seed for reproducibility
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'E'
DRONE_SYMBOLS = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']

# Directions for player movement
MOVES = {
    'w': (-1, 0),  # Up
    's': (1, 0),   # Down
    'a': (0, -1),  # Left
    'd': (0, 1),   # Right
    'f': (0, 0)    # Stay
}

def clear_screen():
    """Clear the terminal screen for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')

def is_adjacent_to_player_start(pos, distance=2):
    """
    Check if a position is within a certain distance from the player's starting position.

    :param pos: Tuple (row, col) position to check.
    :param distance: Manhattan distance threshold.
    :return: Boolean indicating if position is within the threshold.
    """
    return abs(pos[0] - PLAYER_START_POS[0]) + abs(pos[1] - PLAYER_START_POS[1]) < distance

class Drone:
    def __init__(self, symbol, start_pos, patrol_route):
        """
        Initialize a drone.

        :param symbol: Single character representing the drone.
        :param start_pos: Starting position of the drone.
        :param patrol_route: List of positions representing the patrol route.
        """
        self.symbol = symbol
        self.position = start_pos
        self.patrol_route = patrol_route
        self.route_index = 0

    def move(self, occupied_positions):
        """
        Move the drone along its patrol route.

        :param occupied_positions: Set of positions currently occupied by other drones.
        """
        # Calculate next position
        next_index = (self.route_index + 1) % len(self.patrol_route)
        next_pos = self.patrol_route[next_index]

        # Ensure the next position is not occupied
        if next_pos not in occupied_positions:
            self.position = next_pos
            self.route_index = next_index
        # If next position is occupied, drone stays in place this turn

def generate_patrol_routes(strategy):
    """
    Generate patrol routes for drones based on the selected strategy.

    :param strategy: 'row', 'column', or 'spiral'
    :return: List of patrol routes (list of positions)
    """
    routes = []
    if strategy == 'row':
        # Each drone patrols a set of rows
        rows_per_drone = GRID_SIZE // NUM_DRONES
        for i in range(NUM_DRONES):
            start_row = i * rows_per_drone
            end_row = start_row + rows_per_drone
            route = []
            for r in range(start_row, min(end_row, GRID_SIZE)):
                for c in range(GRID_SIZE):
                    route.append((r, c))
                # Reverse direction to create a zigzag pattern
                for c in reversed(range(GRID_SIZE)):
                    route.append((r, c))
            routes.append(route)
    elif strategy == 'column':
        # Each drone patrols a set of columns
        cols_per_drone = GRID_SIZE // NUM_DRONES
        for i in range(NUM_DRONES):
            start_col = i * cols_per_drone
            end_col = start_col + cols_per_drone
            route = []
            for c in range(start_col, min(end_col, GRID_SIZE)):
                for r in range(GRID_SIZE):
                    route.append((r, c))
                # Reverse direction to create a zigzag pattern
                for r in reversed(range(GRID_SIZE)):
                    route.append((r, c))
            routes.append(route)
    elif strategy == 'spiral':
        # Drones patrol in spiral patterns starting from different corners
        for i in range(NUM_DRONES):
            route = generate_spiral_route(start_corner=i % 4)
            routes.append(route)
    else:
        print("Invalid patrol strategy. Using default 'row' strategy.")
        return generate_patrol_routes('row')
    return routes

def generate_spiral_route(start_corner=0):
    """
    Generate a spiral route starting from a specific corner.

    :param start_corner: 0=top-left, 1=top-right, 2=bottom-right, 3=bottom-left
    :return: List of positions representing the spiral route
    """
    route = []
    visited = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
    dirs = [ (0,1), (1,0), (0,-1), (-1,0) ]  # Right, Down, Left, Up
    dir_index = start_corner
    r, c = {
        0: (0,0),
        1: (0, GRID_SIZE-1),
        2: (GRID_SIZE-1, GRID_SIZE-1),
        3: (GRID_SIZE-1, 0)
    }[start_corner]
    steps = 1
    total_cells = GRID_SIZE * GRID_SIZE
    while len(route) < total_cells:
        for _ in range(2):
            dr, dc = dirs[dir_index % 4]
            for _ in range(steps):
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and not visited[r][c]:
                    route.append((r, c))
                    visited[r][c] = True
                r += dr
                c += dc
            dir_index += 1
        steps += 1
    return route

def initialize_game():
    """
    Initialize the game state with drones and their patrol routes.

    :return: Tuple (player_pos, end_pos, drones)
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Generate patrol routes for drones
    patrol_routes = generate_patrol_routes(DRONE_PATROL_STRATEGY)

    # Initialize drones
    drones = []
    for i in range(NUM_DRONES):
        symbol = DRONE_SYMBOLS[i % len(DRONE_SYMBOLS)]
        # Start each drone at the first position of its patrol route
        start_pos = patrol_routes[i][0]
        # Ensure drones do not start at the player's position or adjacent to it
        if start_pos == player_pos or is_adjacent_to_player_start(start_pos, distance=1):
            # Find the next available position
            for pos in patrol_routes[i]:
                if pos != player_pos and not is_adjacent_to_player_start(pos, distance=1):
                    start_pos = pos
                    break
        drone = Drone(symbol, start_pos, patrol_routes[i])
        drones.append(drone)

    return player_pos, end_pos, drones

def draw_grid(player_pos, end_pos, drones):
    """
    Display the current state of the grid.

    :param player_pos: Tuple (row, col) of the player's position.
    :param end_pos: Tuple (row, col) of the end position.
    :param drones: List of Drone objects.
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
            drone_positions[(r, c)] += 1
        else:
            drone_positions[(r, c)] = 1

    for (r, c), count in drone_positions.items():
        if count == 1:
            # Find the drone symbol at this position
            for drone in drones:
                if drone.position == (r, c):
                    grid[r][c] = drone.symbol
                    break
        else:
            grid[r][c] = '*'  # Indicate multiple drones (shouldn't happen)

    # Place the player
    pr, pc = player_pos
    grid[pr][pc] = PLAYER_SYMBOL

    # Print the grid with row and column indices
    header = "    " + " ".join([f"{c:2}" for c in range(GRID_SIZE)])
    print(header)
    for idx, row in enumerate(grid):
        row_str = f"{idx:2} | " + " ".join([f"{cell:2}" for cell in row])
        print(row_str)
    print("\nLegend: P=Player, E=End, D/E/F/G/H= Drones, *=Multiple Drones (should not occur), .=Empty")

def get_player_move():
    """
    Prompt the player for a move and return the corresponding direction.

    :return: Tuple (dr, dc) representing the move direction.
    """
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

def main():
    """Main game loop."""
    print("Welcome to 'Pall of the Eye' - Drone Patrol Edition!")

    # Initialize the game
    player_pos, end_pos, drones = initialize_game()

    turn = 0
    max_turns = 200  # Adjust as needed

    while turn < max_turns:
        clear_screen()
        print(f"Turn: {turn}")
        draw_grid(player_pos, end_pos, drones)

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
            draw_grid(player_pos, end_pos, drones)
            print("💥 Oh no! You've been caught by a drone. Game Over. 💥")
            return

        # Move drones
        occupied_positions = set(drone.position for drone in drones)
        for drone in drones:
            occupied_positions.discard(drone.position)  # Remove current position
            drone.move(occupied_positions)
            occupied_positions.add(drone.position)  # Add new position

        # Check for collision after drones' move
        if is_collision(player_pos, drones):
            clear_screen()
            print(f"Turn: {turn + 1}")
            draw_grid(player_pos, end_pos, drones)
            print("💥 A drone has moved into your square. Game Over. 💥")
            return

        turn += 1

    print("⏰ Maximum turns reached. Game Over.")

if __name__ == "__main__":
    main()
import os
import time
import random
import math

# --------------------- Configurable Parameters ---------------------

# Grid Configuration
GRID_SIZE = 10  # Size of the grid (10x10)

# Player Configuration
PLAYER_START_POS = (0, 0)  # Starting position of the player
END_POS = (GRID_SIZE - 1, GRID_SIZE - 1)  # End position

# Drone Configuration
NUM_DRONES = 5  # Total number of drones

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

class Drone:
    def __init__(self, symbol, sector):
        """
        Initialize a drone.

        :param symbol: Single character representing the drone.
        :param sector: Dictionary with 'start_row', 'end_row', 'start_col', 'end_col' defining the sector.
        """
        self.symbol = symbol
        self.sector = sector
        self.patrol_route = self.generate_patrol_route()
        self.route_index = 0
        self.position = self.patrol_route[self.route_index]

    def generate_patrol_route(self):
        """
        Generate a patrol route that covers all squares in the sector without repeating until all squares are visited.

        :return: List of positions representing the patrol route.
        """
        route = []
        sr = self.sector['start_row']
        er = self.sector['end_row']
        sc = self.sector['start_col']
        ec = self.sector['end_col']

        for r in range(sr, er):
            cols = range(sc, ec)
            if (r - sr) % 2 == 1:
                cols = reversed(cols)
            for c in cols:
                route.append((r, c))

        return route

    def move(self):
        """
        Move the drone along its patrol route.
        """
        self.route_index = (self.route_index + 1) % len(self.patrol_route)
        self.position = self.patrol_route[self.route_index]

def compute_sectors(grid_size, num_drones):
    """
    Compute the sectors for each drone.

    :param grid_size: Size of the grid.
    :param num_drones: Number of drones.
    :return: List of sector dictionaries.
    """
    # Determine number of sectors along rows and columns
    sectors_per_row = int(math.sqrt(num_drones))
    while num_drones % sectors_per_row != 0 and sectors_per_row > 1:
        sectors_per_row -= 1
    sectors_per_col = num_drones // sectors_per_row

    # Adjust if necessary
    if sectors_per_row * sectors_per_col < num_drones:
        sectors_per_col += 1

    sector_height = grid_size // sectors_per_row
    sector_width = grid_size // sectors_per_col

    sectors = []
    drone_index = 0

    for i in range(sectors_per_row):
        for j in range(sectors_per_col):
            if drone_index >= num_drones:
                break
            start_row = i * sector_height
            end_row = (i + 1) * sector_height if (i + 1) * sector_height <= grid_size else grid_size
            start_col = j * sector_width
            end_col = (j + 1) * sector_width if (j + 1) * sector_width <= grid_size else grid_size

            # Adjust for any leftover rows or columns
            if i == sectors_per_row - 1:
                end_row = grid_size
            if j == sectors_per_col - 1:
                end_col = grid_size

            sectors.append({
                'start_row': start_row,
                'end_row': end_row,
                'start_col': start_col,
                'end_col': end_col
            })
            drone_index += 1

    return sectors

def initialize_game():
    """
    Initialize the game state with drones and their patrol routes.

    :return: Tuple (player_pos, end_pos, drones)
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Compute sectors for drones
    sectors = compute_sectors(GRID_SIZE, NUM_DRONES)

    # Initialize drones
    drones = []
    for i in range(NUM_DRONES):
        symbol = DRONE_SYMBOLS[i % len(DRONE_SYMBOLS)]
        sector = sectors[i]

        # Start each drone at the beginning of its patrol route
        drone = Drone(symbol, sector)

        # Ensure drones do not start at the player's position or adjacent to it
        if drone.position == player_pos or is_adjacent_to_player_start(drone.position):
            # Shift the drone's starting position along its patrol route
            for idx, pos in enumerate(drone.patrol_route):
                if pos != player_pos and not is_adjacent_to_player_start(pos):
                    drone.route_index = idx
                    drone.position = pos
                    break

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
            grid[r][c] = '*'  # Indicate multiple drones (should not occur)

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
    MOVES = {
        'w': (-1, 0),  # Up
        's': (1, 0),   # Down
        'a': (0, -1),  # Left
        'd': (0, 1),   # Right
        'f': (0, 0)    # Stay
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

def main():
    """Main game loop."""
    print("Welcome to 'Pall of the Eye' - Sector Patrol Edition!")

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
        for drone in drones:
            drone.move()

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
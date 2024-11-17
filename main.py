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

# Directions for movement
DIRECTIONS = [
    (-1, 0),  # Up
    (1, 0),   # Down
    (0, -1),  # Left
    (0, 1)    # Right
]

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
    def __init__(self, symbol, start_pos, grid_size):
        """
        Initialize a drone.

        :param symbol: Single character representing the drone.
        :param start_pos: Starting position of the drone.
        :param grid_size: Size of the grid.
        """
        self.symbol = symbol
        self.position = start_pos
        self.grid_size = grid_size
        self.visited = set()
        self.visited.add(start_pos)

    def move(self, occupied_positions):
        """
        Move the drone to a random adjacent square, avoiding occupied positions.

        :param occupied_positions: Set of positions currently occupied by other drones.
        """
        possible_moves = []

        for dr, dc in DIRECTIONS:
            new_r = self.position[0] + dr
            new_c = self.position[1] + dc

            # Check bounds
            if 0 <= new_r < self.grid_size and 0 <= new_c < self.grid_size:
                new_pos = (new_r, new_c)
                if new_pos not in occupied_positions:
                    possible_moves.append(new_pos)

        # If there are possible moves, choose one
        if possible_moves:
            # Prioritize unvisited squares
            unvisited_moves = [pos for pos in possible_moves if pos not in self.visited]
            if unvisited_moves:
                next_pos = random.choice(unvisited_moves)
            else:
                next_pos = random.choice(possible_moves)

            self.position = next_pos
            self.visited.add(next_pos)
        else:
            # No possible moves; drone stays in place
            pass

        # Reset visited squares if all have been visited
        if len(self.visited) == self.grid_size * self.grid_size:
            self.visited = set([self.position])

def initialize_game():
    """
    Initialize the game state with drones and their patrol routes.

    :return: Tuple (player_pos, end_pos, drones)
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Initialize drones
    drones = []
    occupied_positions = set()
    attempts = 0
    max_attempts = 1000

    for i in range(NUM_DRONES):
        symbol = DRONE_SYMBOLS[i % len(DRONE_SYMBOLS)]

        while attempts < max_attempts:
            attempts += 1
            r = random.randint(0, GRID_SIZE - 1)
            c = random.randint(0, GRID_SIZE - 1)
            start_pos = (r, c)

            if start_pos == player_pos or is_adjacent_to_player_start(start_pos, distance=2):
                continue  # Avoid starting near the player
            if start_pos in occupied_positions:
                continue  # Avoid starting on another drone

            occupied_positions.add(start_pos)
            drone = Drone(symbol, start_pos, GRID_SIZE)
            drones.append(drone)
            break
        else:
            print("Could not place all drones. Consider reducing the number of drones or increasing the grid size.")
            exit()

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
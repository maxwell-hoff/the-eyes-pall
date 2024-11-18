import os
import time
import random
import math
from collections import deque

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

def is_adjacent_to_player_start(pos, distance=1):
    """
    Check if a position is within a certain distance from the player's starting position.

    :param pos: Tuple (row, col) position to check.
    :param distance: Manhattan distance threshold.
    :return: Boolean indicating if position is within the threshold.
    """
    return abs(pos[0] - PLAYER_START_POS[0]) + abs(pos[1] - PLAYER_START_POS[1]) <= distance

def generate_sectors():
    """
    Generate unique sectors for each drone group, ensuring they are connected, cover the entire grid,
    and exclude the player's starting position.

    :return: List of sectors, where each sector is a set of positions.
    """
    # Initialize sector assignments
    grid = [[-1 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    sectors = [set() for _ in range(NUM_DRONE_GROUPS)]

    # Place seed points for each group
    seed_positions = []
    attempts = 0
    max_attempts = 1000
    while len(seed_positions) < NUM_DRONE_GROUPS and attempts < max_attempts:
        attempts += 1
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        pos = (r, c)
        if pos == PLAYER_START_POS or is_adjacent_to_player_start(pos):
            continue
        if pos in seed_positions:
            continue
        seed_positions.append(pos)
        grid[r][c] = len(seed_positions) - 1
        sectors[len(seed_positions) - 1].add(pos)

    if len(seed_positions) < NUM_DRONE_GROUPS:
        print("Could not place all drone groups. Consider reducing the number of groups or increasing the grid size.")
        exit()

    # Initialize queues for BFS
    queues = [deque([pos]) for pos in seed_positions]

    # BFS to assign cells to sectors
    while any(queues):
        for i in range(NUM_DRONE_GROUPS):
            if queues[i]:
                r, c = queues[i].popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        if grid[nr][nc] == -1 and (nr, nc) != PLAYER_START_POS:
                            grid[nr][nc] = i
                            sectors[i].add((nr, nc))
                            queues[i].append((nr, nc))

    return sectors

class DroneGroup:
    def __init__(self, symbol, sector):
        """
        Initialize a drone group.

        :param symbol: Single character representing the drone group.
        :param sector: Set of positions defining the group's sector.
        """
        self.symbol = symbol
        self.sector = sector
        self.patrol_route = self.generate_patrol_route()
        self.drones = []

    def generate_patrol_route(self):
        """
        Generate a patrol route that covers all squares in the sector without repeating until all squares are visited.
        The route is cyclical, and the last position is adjacent to the first.

        :return: List of positions representing the patrol route.
        """
        # Use a simple Hamiltonian path approach within the sector
        route = []
        visited = set()
        stack = []

        # Start from a random position in the sector
        start_pos = random.choice(list(self.sector))
        stack.append(start_pos)
        visited.add(start_pos)

        while stack:
            current_pos = stack.pop()
            route.append(current_pos)
            neighbors = []

            for dr, dc in DIRECTIONS:
                nr, nc = current_pos[0] + dr, current_pos[1] + dc
                neighbor = (nr, nc)
                if neighbor in self.sector and neighbor not in visited:
                    neighbors.append(neighbor)

            if neighbors:
                stack.append(current_pos)  # Re-add current position to backtrack later
                next_pos = random.choice(neighbors)
                stack.append(next_pos)
                visited.add(next_pos)

        # Ensure the last position is adjacent to the first
        if abs(route[-1][0] - route[0][0]) + abs(route[-1][1] - route[0][1]) == 1:
            return route
        else:
            # Modify the route to make it cyclical
            route.append(route[0])
            return route

class Drone:
    def __init__(self, group, start_offset):
        """
        Initialize a drone.

        :param group: The DroneGroup object the drone belongs to.
        :param start_offset: Starting index offset in the patrol route to desynchronize drones.
        """
        self.symbol = group.symbol
        self.patrol_route = group.patrol_route
        self.route_length = len(self.patrol_route)
        self.route_index = start_offset % self.route_length
        self.position = self.patrol_route[self.route_index]

    def move(self):
        """
        Move the drone along its patrol route.
        """
        self.route_index = (self.route_index + 1) % self.route_length
        self.position = self.patrol_route[self.route_index]

def initialize_game():
    """
    Initialize the game state with drones and their patrol routes.

    :return: Tuple (player_pos, end_pos, drones)
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Generate sectors for drone groups
    sectors = generate_sectors()

    # Distribute drones among groups
    drones = []
    drones_per_group = [NUM_DRONES // NUM_DRONE_GROUPS] * NUM_DRONE_GROUPS
    for i in range(NUM_DRONES % NUM_DRONE_GROUPS):
        drones_per_group[i] += 1  # Distribute remainder

    drone_groups = []
    for i in range(NUM_DRONE_GROUPS):
        symbol = DRONE_SYMBOLS[i % len(DRONE_SYMBOLS)]
        sector = sectors[i]
        group = DroneGroup(symbol, sector)
        drone_groups.append(group)

    # Initialize drones within groups
    drone_id = 0
    for i, group in enumerate(drone_groups):
        num_drones_in_group = drones_per_group[i]
        for _ in range(num_drones_in_group):
            # Introduce a random start offset to desynchronize drones within the group
            start_offset = random.randint(0, len(group.patrol_route) - 1)
            drone = Drone(group, start_offset)

            # Ensure drone does not start at the player's position or adjacent to it
            if drone.position == player_pos or is_adjacent_to_player_start(drone.position):
                for idx in range(len(drone.patrol_route)):
                    pos = drone.patrol_route[idx]
                    if pos != player_pos and not is_adjacent_to_player_start(pos):
                        drone.route_index = idx
                        drone.position = pos
                        break

            drones.append(drone)
            group.drones.append(drone)
            drone_id += 1

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

    # Print the grid with row and column indices
    header = "    " + " ".join([f"{c:2}" for c in range(GRID_SIZE)])
    print(header)
    for idx, row in enumerate(grid):
        row_str = f"{idx:2} | " + " ".join([f"{cell:2}" for cell in row])
        print(row_str)
    print("\nLegend: P=Player, E=End, D/E/F/G/H= Drone Groups, *=Multiple Drones, .=Empty")

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
    print("Welcome to 'Pall of the Eye' - Drone Group Patrol Edition!")

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
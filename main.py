import os
import time
import random
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
DRONE_SYMBOLS = ['D', 'E', 'F', 'G', 'H']

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
    Generate unique sectors for each drone, ensuring they are connected, cover the entire grid,
    and exclude the player's starting position.

    :return: List of sectors, where each sector is a set of positions.
    """
    total_positions = GRID_SIZE * GRID_SIZE - 1  # Exclude player's starting position
    min_sector_size = 2
    max_sector_size = 4
    sectors = []
    assigned_positions = set([PLAYER_START_POS])
    unassigned_positions = set(
        (r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if (r, c) != PLAYER_START_POS)

    for i in range(NUM_DRONES):
        remaining_positions = len(unassigned_positions)
        if remaining_positions < min_sector_size:
            print(f"Warning: Not enough positions left to create a sector of minimum size {min_sector_size}")
            break  # No more sectors can be created

        sector_size = random.randint(min_sector_size, min(max_sector_size, remaining_positions))
        sector = set()

        # Find a starting position for this sector
        possible_starts = list(unassigned_positions)
        if not possible_starts:
            break  # No more positions to assign
        start_pos = random.choice(possible_starts)
        sector.add(start_pos)
        unassigned_positions.remove(start_pos)
        assigned_positions.add(start_pos)

        # Expand the sector using BFS to reach the desired size
        queue = deque([start_pos])
        while queue and len(sector) < sector_size:
            current_pos = queue.popleft()
            for dr, dc in DIRECTIONS:
                nr, nc = current_pos[0] + dr, current_pos[1] + dc
                neighbor = (nr, nc)
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                    if neighbor in unassigned_positions:
                        sector.add(neighbor)
                        unassigned_positions.remove(neighbor)
                        assigned_positions.add(neighbor)
                        queue.append(neighbor)
        if len(sector) >= min_sector_size:
            sectors.append(sector)
        else:
            print(f"Warning: Could not create a sector of minimum size {min_sector_size}, sector size is {len(sector)}")
            # Return unassigned positions to the pool
            unassigned_positions.update(sector)
            assigned_positions.difference_update(sector)

    # If there are remaining unassigned positions, assign them to existing sectors
    while unassigned_positions:
        for sector in sectors:
            if not unassigned_positions:
                break
            possible_starts = [pos for pos in sector if any(
                (pos[0] + dr, pos[1] + dc) in unassigned_positions for dr, dc in DIRECTIONS)]
            if possible_starts:
                start_pos = random.choice(possible_starts)
                for dr, dc in DIRECTIONS:
                    nr, nc = start_pos[0] + dr, start_pos[1] + dc
                    neighbor = (nr, nc)
                    if neighbor in unassigned_positions:
                        sector.add(neighbor)
                        unassigned_positions.remove(neighbor)
                        assigned_positions.add(neighbor)
                        break

    # Verify that all sectors have at least min_sector_size positions
    for i, sector in enumerate(sectors):
        if len(sector) < min_sector_size:
            print(f"Error: Sector {i} has size less than minimum: {len(sector)}")
            # Optionally, merge this sector with another

    return sectors

class DroneGroup:
    def __init__(self, symbol, direction_order):
        """
        Initialize a drone group.

        :param symbol: Single character representing the drone group.
        :param direction_order: List of directions to use when traversing sectors.
        """
        self.symbol = symbol
        self.direction_order = direction_order
        self.drones = []

class Drone:
    def __init__(self, group, sector):
        """
        Initialize a drone.

        :param group: The DroneGroup object the drone belongs to.
        :param sector: Set of positions defining the drone's sector.
        """
        self.symbol = group.symbol
        self.group = group
        self.sector = sector
        self.patrol_route = self.generate_patrol_route()
        self.route_length = len(self.patrol_route)
        self.route_index = 0
        self.direction = 1  # 1 for forward, -1 for backward
        self.position = self.patrol_route[self.route_index]

    def generate_patrol_route(self):
        """
        Generate a patrol route for the drone based on the group's direction order and the drone's sector.

        :return: List of positions representing the patrol route.
        """
        route = []
        visited = set()
        stack = []
        start_pos = random.choice(list(self.sector))
        stack.append(start_pos)
        visited.add(start_pos)

        while stack:
            current_pos = stack.pop()
            route.append(current_pos)

            # Get directions in the group's order
            found_next = False
            for move in self.group.direction_order:
                dr, dc = move
                next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                if next_pos in self.sector and next_pos not in visited:
                    stack.append(next_pos)
                    visited.add(next_pos)
                    found_next = True
                    break  # Only add one next position to ensure moving to adjacent square

            if not found_next:
                # Try other directions if no move found in group's direction order
                for dr, dc in DIRECTIONS:
                    next_pos = (current_pos[0] + dr, current_pos[1] + dc)
                    if next_pos in self.sector and next_pos not in visited:
                        stack.append(next_pos)
                        visited.add(next_pos)
                        break  # Only add one next position

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

        next_position = self.patrol_route[next_index]

        # Ensure the drone does not stay in the same square
        if next_position == self.position:
            # Find the next different position in the current direction
            temp_index = next_index
            while 0 <= temp_index < self.route_length and self.patrol_route[temp_index] == self.position:
                temp_index += self.direction
            if 0 <= temp_index < self.route_length:
                next_index = temp_index
            else:
                # Can't find a different position in current direction; reverse direction
                self.direction *= -1
                next_index = self.route_index + self.direction
                if next_index < 0 or next_index >= self.route_length:
                    print(f"Error: Drone {self.symbol} cannot move; patrol route exhausted.")
                    return

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

    # Generate sectors for drones
    sectors = generate_sectors()

    # Define direction orders for each drone group
    direction_orders = [
        [ (0, 1), (1, 0), (0, -1), (-1, 0) ],  # Group 0: Right, Down, Left, Up
        [ (1, 0), (0, 1), (-1, 0), (0, -1) ],  # Group 1: Down, Right, Up, Left
        [ (0, 1), (0, -1) ],                   # Group 2: Right, Left
        [ (1, 0), (-1, 0) ],                   # Group 3: Down, Up
        [ (1, 1), (-1, -1) ]                   # Group 4: Diagonal moves
    ]

    # Create drone groups
    drone_groups = []
    for i in range(NUM_DRONE_GROUPS):
        symbol = DRONE_SYMBOLS[i % len(DRONE_SYMBOLS)]
        direction_order = direction_orders[i % len(direction_orders)]
        group = DroneGroup(symbol, direction_order)
        drone_groups.append(group)

    # Distribute drones among groups
    drones_per_group = [NUM_DRONES // NUM_DRONE_GROUPS] * NUM_DRONE_GROUPS
    for i in range(NUM_DRONES % NUM_DRONE_GROUPS):
        drones_per_group[i] += 1  # Distribute remainder

    # Initialize drones and assign sectors
    drones = []
    sector_index = 0
    for i, group in enumerate(drone_groups):
        num_drones_in_group = drones_per_group[i]
        for _ in range(num_drones_in_group):
            if sector_index >= len(sectors):
                break  # No more sectors to assign
            sector = sectors[sector_index]
            sector_index += 1
            drone = Drone(group, sector)

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
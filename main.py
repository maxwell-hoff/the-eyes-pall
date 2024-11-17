import os
import time
import random

# --------------------- Configurable Parameters ---------------------

# Grid Configuration
GRID_SIZE = 10  # Size of the grid (10x10)

# Player Configuration
PLAYER_START_POS = (0, 0)  # Starting position of the player
END_POS = (GRID_SIZE - 1, GRID_SIZE - 1)  # End position

# Enemy Configuration
NUM_ENEMIES = 5  # Total number of enemies
MEAN_HUBS_PER_ENEMY = 3  # Average number of hubs per enemy
STD_HUBS_PER_ENEMY = 1  # Standard deviation for hubs per enemy
HUB_SHAREDNESS = 0.5  # Probability that hubs are shared among enemies (0 to 1)
PATH_CONCENTRATION = 0.5  # Probability that paths are shared among enemies (0 to 1)

# Random Seed for Reproducibility
RANDOM_SEED = None  # Set to an integer value for reproducible results, e.g., 42

# Stay Duration at Hubs
MIN_STAY_DURATION = 1  # Minimum turns to stay at a hub
MAX_STAY_DURATION = 3  # Maximum turns to stay at a hub

# --------------------- End of Configurable Parameters ---------------------

# Set the random seed for reproducibility
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'E'
ENEMY_SYMBOLS = ['X', 'Y', 'Z', 'W', 'V', 'Q', 'R', 'S', 'T', 'U']

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

class Enemy:
    def __init__(self, symbol, hubs, paths_between_hubs, path_concentration):
        """
        Initialize an enemy.

        :param symbol: Single character representing the enemy.
        :param hubs: List of hubs assigned to the enemy.
        :param paths_between_hubs: Shared dictionary of paths between hubs.
        :param path_concentration: Parameter controlling path concentration (0 to 1).
        """
        self.symbol = symbol
        self.hubs = hubs
        self.paths_between_hubs = paths_between_hubs
        self.path_concentration = path_concentration
        self.current_hub = random.choice(self.hubs)
        self.next_hub = None
        self.path = []
        self.stay_duration = random.randint(MIN_STAY_DURATION, MAX_STAY_DURATION)
        self.position = self.current_hub  # Initialize position
        # Do not generate movement plan immediately
        # self.generate_movement_plan()

    def generate_movement_plan(self):
        """Determine the next hub and the path to it."""
        possible_hubs = [hub for hub in self.hubs if hub != self.current_hub]
        if not possible_hubs:
            self.next_hub = self.current_hub
            self.path = []
            self.stay_duration = random.randint(MIN_STAY_DURATION, MAX_STAY_DURATION)
            return

        self.next_hub = random.choice(possible_hubs)

        # Determine the path key
        path_key = (self.current_hub, self.next_hub)
        reverse_key = (self.next_hub, self.current_hub)

        # Check if path already exists (for shared paths)
        if path_key in self.paths_between_hubs:
            self.path = self.paths_between_hubs[path_key].copy()
        elif reverse_key in self.paths_between_hubs and random.random() < self.path_concentration:
            # Use the reverse of an existing path
            self.path = self.paths_between_hubs[reverse_key][::-1].copy()
            self.paths_between_hubs[path_key] = self.paths_between_hubs[reverse_key].copy()
        else:
            # Generate a new path
            self.path = generate_path_between_hubs(self.current_hub, self.next_hub)
            self.paths_between_hubs[path_key] = self.path.copy()

        # Set stay duration at the new hub (will be set when the hub is reached)

    def move(self):
        """Move the enemy along the path or stay at the hub."""
        if self.stay_duration > 0:
            # Stay at the current hub
            self.stay_duration -= 1
            if self.stay_duration == 0:
                # Generate movement plan when ready to move
                self.generate_movement_plan()
            return

        if self.path:
            # Move along the path
            self.position = self.path.pop(0)
            if not self.path:
                # Reached the next hub, set stay duration
                self.current_hub = self.next_hub
                self.stay_duration = random.randint(MIN_STAY_DURATION, MAX_STAY_DURATION)
        else:
            # No movement path; wait at current position
            pass

def generate_path_between_hubs(hub1, hub2):
    """
    Generate a path between two hubs using cardinal directions (no diagonal moves).

    :param hub1: Starting hub (row, col).
    :param hub2: Ending hub (row, col).
    :return: List of (row, col) tuples representing the path.
    """
    path = []
    current_pos = hub1
    while current_pos != hub2:
        r1, c1 = current_pos
        r2, c2 = hub2

        possible_moves = []

        if r1 < r2:
            possible_moves.append((1, 0))  # Move down
        elif r1 > r2:
            possible_moves.append((-1, 0))  # Move up

        if c1 < c2:
            possible_moves.append((0, 1))  # Move right
        elif c1 > c2:
            possible_moves.append((0, -1))  # Move left

        # Randomly select one of the possible moves
        if possible_moves:
            move_r, move_c = random.choice(possible_moves)
        else:
            break  # Already at the destination

        new_r = r1 + move_r
        new_c = c1 + move_c

        # Ensure the new position is within bounds
        new_r = max(0, min(GRID_SIZE - 1, new_r))
        new_c = max(0, min(GRID_SIZE - 1, new_c))

        current_pos = (new_r, new_c)
        path.append(current_pos)

    return path

def assign_hubs_to_enemy(all_hubs, num_hubs, hub_sharedness, hub_assignments):
    """
    Assign hubs to an enemy based on sharedness.

    :param all_hubs: List of all hubs.
    :param num_hubs: Number of hubs to assign to the enemy.
    :param hub_sharedness: Probability that hubs are shared among enemies.
    :param hub_assignments: Dictionary mapping hubs to the number of enemies assigned.
    :return: List of hubs assigned to the enemy.
    """
    enemy_hubs = []
    for _ in range(num_hubs):
        # Calculate weights for hubs
        hub_weights = []
        for hub in all_hubs:
            if hub in enemy_hubs:
                continue  # Avoid duplicate hubs for the same enemy

            # If hub is already assigned to other enemies, weight it based on sharedness
            if hub_assignments.get(hub, 0) > 0:
                weight = hub_sharedness
            else:
                weight = 1 - hub_sharedness

            hub_weights.append((hub, weight))

        if not hub_weights:
            break  # No more hubs to assign

        # Normalize weights
        total_weight = sum(weight for hub, weight in hub_weights)
        if total_weight == 0:
            break  # Avoid division by zero

        # Select a hub based on weights
        rand_val = random.uniform(0, total_weight)
        cumulative_weight = 0
        selected_hub = None
        for hub, weight in hub_weights:
            cumulative_weight += weight
            if rand_val <= cumulative_weight:
                selected_hub = hub
                break

        if selected_hub:
            enemy_hubs.append(selected_hub)
            hub_assignments[selected_hub] = hub_assignments.get(selected_hub, 0) + 1

    return enemy_hubs

def initialize_game(num_enemies, mean_hubs, std_hubs, hub_sharedness, path_concentration):
    """
    Initialize the game state with enemies, hubs, and paths.

    :param num_enemies: Total number of enemies.
    :param mean_hubs: Mean number of hubs per enemy.
    :param std_hubs: Standard deviation for hubs per enemy.
    :param hub_sharedness: Probability that hubs are shared among enemies.
    :param path_concentration: Probability that paths are shared among enemies.
    :return: Tuple (player_pos, end_pos, enemies).
    """
    # Initialize player and end positions
    player_pos = PLAYER_START_POS
    end_pos = END_POS

    # Generate hubs
    total_hubs = max(5, int(num_enemies * mean_hubs * 0.7))  # Ensure sufficient hubs
    hubs = []
    attempts = 0
    while len(hubs) < total_hubs and attempts < 1000:
        attempts += 1
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        pos = (r, c)
        if pos == player_pos or is_adjacent_to_player_start(pos, distance=2):
            continue  # Avoid placing hubs too close to the player
        if pos in hubs:
            continue  # Avoid duplicate hubs
        hubs.append(pos)

    if len(hubs) < total_hubs:
        print("Could not generate enough hubs. Consider increasing the grid size or adjusting parameters.")
        exit()

    # Assign hubs to enemies
    hub_assignments = {}
    paths_between_hubs = {}
    enemies = []
    for i in range(num_enemies):
        symbol = ENEMY_SYMBOLS[i % len(ENEMY_SYMBOLS)]
        # Determine number of hubs for this enemy based on Gaussian distribution
        num_hubs = max(2, int(random.gauss(mean_hubs, std_hubs)))
        num_hubs = min(num_hubs, len(hubs))  # Prevent assigning more hubs than available

        # Assign hubs to the enemy
        enemy_hubs = assign_hubs_to_enemy(hubs, num_hubs, hub_sharedness, hub_assignments)
        if not enemy_hubs:
            print(f"Enemy {i+1} could not be assigned any hubs. Consider adjusting hub_sharedness.")
            continue

        # Create and add the enemy
        enemy = Enemy(symbol, enemy_hubs, paths_between_hubs, path_concentration)
        enemies.append(enemy)

    return player_pos, end_pos, enemies

def draw_grid(player_pos, end_pos, enemies):
    """
    Display the current state of the grid.

    :param player_pos: Tuple (row, col) of the player's position.
    :param end_pos: Tuple (row, col) of the end position.
    :param enemies: List of Enemy objects.
    """
    grid = [[EMPTY_SYMBOL for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    # Place the end position
    er, ec = end_pos
    grid[er][ec] = END_SYMBOL

    # Place enemies
    enemy_positions = {}
    for enemy in enemies:
        r, c = enemy.position
        if (r, c) == player_pos:
            continue  # Collision handled separately
        if (r, c) in enemy_positions:
            enemy_positions[(r, c)] += 1
        else:
            enemy_positions[(r, c)] = 1

    for (r, c), count in enemy_positions.items():
        if count == 1:
            # Find the enemy symbol at this position
            for enemy in enemies:
                if enemy.position == (r, c):
                    grid[r][c] = enemy.symbol
                    break
        else:
            grid[r][c] = '*'  # Indicate multiple enemies

    # Place the player
    pr, pc = player_pos
    grid[pr][pc] = PLAYER_SYMBOL

    # Print the grid with row and column indices
    header = "    " + " ".join([f"{c:2}" for c in range(GRID_SIZE)])
    print(header)
    for idx, row in enumerate(grid):
        row_str = f"{idx:2} | " + " ".join([f"{cell:2}" for cell in row])
        print(row_str)
    print("\nLegend: P=Player, E=End, X/Y/Z/W/V/Q/R/S/T/U=Enemies, *=Multiple Enemies, .=Empty")

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

def is_collision(player_pos, enemies):
    """
    Check if the player has collided with any enemy.

    :param player_pos: Tuple (row, col) of the player's position.
    :param enemies: List of Enemy objects.
    :return: Boolean indicating collision.
    """
    for enemy in enemies:
        if player_pos == enemy.position:
            return True
    return False

def main():
    """Main game loop."""
    print("Welcome to 'Pall of the Eye'!")

    # Initialize the game
    player_pos, end_pos, enemies = initialize_game(
        num_enemies=NUM_ENEMIES,
        mean_hubs=MEAN_HUBS_PER_ENEMY,
        std_hubs=STD_HUBS_PER_ENEMY,
        hub_sharedness=HUB_SHAREDNESS,
        path_concentration=PATH_CONCENTRATION
    )

    turn = 0
    max_turns = 200  # Adjust as needed

    while turn < max_turns:
        clear_screen()
        print(f"Turn: {turn}")
        draw_grid(player_pos, end_pos, enemies)

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
        if is_collision(player_pos, enemies):
            clear_screen()
            print(f"Turn: {turn + 1}")
            draw_grid(player_pos, end_pos, enemies)
            print("💥 Oh no! You've been caught by an enemy. Game Over. 💥")
            return

        # Move enemies
        for enemy in enemies:
            enemy.move()

        # Check for collision after enemies' move
        if is_collision(player_pos, enemies):
            clear_screen()
            print(f"Turn: {turn + 1}")
            draw_grid(player_pos, end_pos, enemies)
            print("💥 An enemy has moved into your square. Game Over. 💥")
            return

        turn += 1

    print("⏰ Maximum turns reached. Game Over.")

if __name__ == "__main__":
    main()
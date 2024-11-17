import os
import time
import random

# Define the grid size
GRID_SIZE = 10

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'E'
ENEMY_SYMBOLS = ['X', 'Y', 'Z', 'W', 'V', 'Q', 'R', 'S', 'T', 'U']

# Directions for player movement
MOVES = {
    'w': (-1, 0),   # Up
    's': (1, 0),    # Down
    'a': (0, -1),   # Left
    'd': (0, 1),    # Right
    'f': (0, 0)     # Stay
}

def clear_screen():
    """Clear the terminal screen for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')

def is_adjacent_to_player_start(pos):
    """Check if a position is adjacent to the player's starting position (0, 0)."""
    adjacent_positions = [(0, 1), (1, 0), (1, 1)]
    return pos in adjacent_positions

class Enemy:
    def __init__(self, symbol, hubs, paths_between_hubs, path_concentration):
        """
        Initialize an enemy.

        :param symbol: Single character representing the enemy
        :param hubs: List of hubs assigned to the enemy
        :param paths_between_hubs: Shared dictionary of paths between hubs
        :param path_concentration: Parameter controlling path concentration (0 to 1)
        """
        self.symbol = symbol
        self.hubs = hubs
        self.paths_between_hubs = paths_between_hubs
        self.path_concentration = path_concentration
        self.position = random.choice(hubs)
        self.current_hub = self.position
        self.next_hub = None
        self.path = []
        self.stay_duration = random.randint(1, 3)
        self.generate_movement_plan()

    def generate_movement_plan(self):
        # Determine the next hub to move to
        if len(self.hubs) > 1:
            self.next_hub = random.choice([hub for hub in self.hubs if hub != self.current_hub])
        else:
            self.next_hub = self.current_hub  # Only one hub assigned
        # Get the path between current hub and next hub
        path_key = (self.current_hub, self.next_hub)
        if path_key in self.paths_between_hubs:
            self.path = self.paths_between_hubs[path_key].copy()
        else:
            # Generate path
            path = generate_path_between_hubs(self.current_hub, self.next_hub)
            # With probability path_concentration, use an existing path if available
            if random.random() < self.path_concentration:
                # Check if there is an existing path between these hubs in reverse
                reverse_key = (self.next_hub, self.current_hub)
                if reverse_key in self.paths_between_hubs:
                    path = self.paths_between_hubs[reverse_key][::-1]
            # Store the path
            self.paths_between_hubs[path_key] = path
            self.path = path.copy()
        # Set stay duration at hub
        self.stay_duration = random.randint(1, 3)

    def move(self):
        if self.stay_duration > 0:
            # Stay at current hub
            self.stay_duration -= 1
            return
        if self.path:
            # Move along the path
            self.position = self.path.pop(0)
            if not self.path:
                # Reached next hub
                self.current_hub = self.next_hub
                self.generate_movement_plan()
        else:
            # No path, generate new movement plan
            self.generate_movement_plan()

def generate_path_between_hubs(hub1, hub2):
    """
    Generate a path between two hubs.

    :param hub1: Starting hub (position)
    :param hub2: Ending hub (position)
    :return: List of positions representing the path
    """
    path = []
    current_pos = hub1
    while current_pos != hub2:
        r1, c1 = current_pos
        r2, c2 = hub2
        dr = r2 - r1
        dc = c2 - c1
        move_r = (1 if dr > 0 else -1) if dr != 0 else 0
        move_c = (1 if dc > 0 else -1) if dc != 0 else 0
        new_r = r1 + move_r
        new_c = c1 + move_c
        current_pos = (new_r, new_c)
        path.append(current_pos)
    return path

def assign_hubs_to_enemy(hubs, num_hubs, hub_sharedness, hub_assignments):
    """
    Assign hubs to an enemy, considering hub sharedness.

    :param hubs: List of all hubs
    :param num_hubs: Number of hubs to assign to the enemy
    :param hub_sharedness: Parameter controlling hub sharedness (0 to 1)
    :param hub_assignments: Dictionary mapping hubs to the number of enemies assigned
    :return: List of hubs assigned to the enemy
    """
    enemy_hubs = []
    for _ in range(num_hubs):
        # Compute weights for hubs
        hub_weights = []
        for hub in hubs:
            if hub in enemy_hubs:
                continue  # Already assigned to this enemy
            if hub in hub_assignments and hub_assignments[hub] > 0:
                weight = hub_sharedness
            else:
                weight = 1 - hub_sharedness
            hub_weights.append((hub, weight))
        if not hub_weights:
            break  # No more hubs to assign
        # Normalize weights
        total_weight = sum(weight for hub, weight in hub_weights)
        if total_weight == 0:
            break
        # Choose a hub based on weights
        rand_val = random.uniform(0, total_weight)
        cumulative_weight = 0
        for hub, weight in hub_weights:
            cumulative_weight += weight
            if rand_val <= cumulative_weight:
                enemy_hubs.append(hub)
                if hub in hub_assignments:
                    hub_assignments[hub] += 1
                else:
                    hub_assignments[hub] = 1
                break
    return enemy_hubs

def initialize_game(num_enemies, mean_hubs, std_hubs, hub_sharedness, path_concentration):
    """
    Initialize the game state based on the selected parameters.

    :param num_enemies: Number of enemies
    :param mean_hubs: Mean number of hubs per enemy
    :param std_hubs: Standard deviation of hubs per enemy
    :param hub_sharedness: Parameter controlling hub sharedness (0 to 1)
    :param path_concentration: Parameter controlling path concentration (0 to 1)
    :return: Tuple (player_pos, end_pos, enemies)
    """
    # Initialize player and end positions
    player_pos = (0, 0)  # Top-left corner
    end_pos = (GRID_SIZE - 1, GRID_SIZE - 1)  # Bottom-right corner

    # Generate hubs
    total_hubs = max(5, int(num_enemies * mean_hubs * 0.7))
    hubs = []
    attempts = 0
    while len(hubs) < total_hubs and attempts < 1000:
        attempts += 1
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        pos = (r, c)
        if pos == player_pos or is_adjacent_to_player_start(pos):
            continue
        if pos in hubs:
            continue
        hubs.append(pos)
    if len(hubs) < total_hubs:
        print("Could not generate enough hubs. Reduce the number of hubs or grid size.")
        exit()

    # Assign hubs to enemies
    hub_assignments = {}
    paths_between_hubs = {}
    enemies = []
    for i in range(num_enemies):
        symbol = ENEMY_SYMBOLS[i % len(ENEMY_SYMBOLS)]
        # Determine number of hubs for this enemy
        num_hubs = max(2, int(random.gauss(mean_hubs, std_hubs)))
        num_hubs = min(num_hubs, len(hubs))  # Can't have more hubs than available
        # Assign hubs to enemy
        enemy_hubs = assign_hubs_to_enemy(hubs, num_hubs, hub_sharedness, hub_assignments)
        # Create enemy
        enemy = Enemy(symbol, enemy_hubs, paths_between_hubs, path_concentration)
        enemies.append(enemy)

    return player_pos, end_pos, enemies

def draw_grid(player_pos, end_pos, enemies):
    """
    Display the current state of the grid.

    :param player_pos: Tuple (row, col) of the player's position
    :param end_pos: Tuple (row, col) of the end position
    :param enemies: List of Enemy objects
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
            continue  # Collision will be handled separately
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

    :return: Tuple (dr, dc) representing the move direction
    """
    valid_moves = list(MOVES.keys())
    move = input("\nMove (w=up, s=down, a=left, d=right, f=stay): ").strip().lower()
    if move not in MOVES:
        print("Invalid move. Please enter 'w', 'a', 's', 'd', or 'f'.")
        return get_player_move()
    return MOVES[move]

def is_collision(player_pos, enemies):
    """
    Check if the player has collided with any enemy.

    :param player_pos: Tuple (row, col) of the player's position
    :param enemies: List of Enemy objects
    :return: Boolean indicating collision
    """
    for enemy in enemies:
        if player_pos == enemy.position:
            return True
    return False

def main():
    """
    Main game loop.
    """
    print("Welcome to 'Pall of the Eye'!")

    # Get number of enemies
    while True:
        try:
            num_enemies = int(input("Enter number of enemies: "))
            if num_enemies > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

    # Get mean and std dev for hubs per enemy
    while True:
        try:
            mean_hubs = float(input("Enter mean number of hubs per enemy (2-5 recommended): "))
            std_hubs = float(input("Enter standard deviation for hubs per enemy (0-2 recommended): "))
            if mean_hubs > 0 and std_hubs >= 0:
                break
            else:
                print("Please enter positive numbers.")
        except ValueError:
            print("Invalid input. Please enter numbers.")

    # Get hub sharedness (between 0 and 1)
    while True:
        try:
            hub_sharedness = float(input("Enter hub sharedness (0 to 1): "))
            if 0 <= hub_sharedness <= 1:
                break
            else:
                print("Please enter a number between 0 and 1.")
        except ValueError:
            print("Invalid input. Please enter a number between 0 and 1.")

    # Get path concentration (0 to 1)
    while True:
        try:
            path_concentration = float(input("Enter path concentration (0 to 1): "))
            if 0 <= path_concentration <= 1:
                break
            else:
                print("Please enter a number between 0 and 1.")
        except ValueError:
            print("Invalid input. Please enter a number between 0 and 1.")

    # Initialize the game
    player_pos, end_pos, enemies = initialize_game(num_enemies, mean_hubs, std_hubs, hub_sharedness, path_concentration)
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
    return

if __name__ == "__main__":
    main()
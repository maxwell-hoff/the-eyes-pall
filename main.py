import os
import time
import random

# Define the grid size
GRID_SIZE = 10

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'E'
ENEMY_SYMBOLS = ['X', 'Y', 'Z', 'W', 'V', 'Q', 'R', 'S', 'T', 'U']  # Extend as needed

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

class Enemy:
    def __init__(self, symbol, pattern, adaptive=False):
        """
        Initialize an enemy.

        :param symbol: Single character representing the enemy
        :param pattern: List of (row, col) tuples defining the movement pattern
        :param adaptive: Boolean indicating if the enemy adapts to the player's position
        """
        self.symbol = symbol
        self.pattern = pattern
        self.adaptive = adaptive
        self.current_step = 0
        self.position = self.pattern[self.current_step]

    def move(self, player_pos=None):
        """
        Move the enemy based on its pattern or adaptively towards the player.

        :param player_pos: Tuple (row, col) of the player's current position
        """
        if self.adaptive and player_pos:
            self.move_towards_player(player_pos)
        else:
            # Advance to the next step in the pattern
            next_step = (self.current_step + 1) % len(self.pattern)
            next_position = self.pattern[next_step]
            # Ensure enemy doesn't move into (0, 0)
            if next_position == (0, 0):
                # Skip this position and advance to the next one
                next_step = (next_step + 1) % len(self.pattern)
                next_position = self.pattern[next_step]
            self.current_step = next_step
            self.position = next_position

    def move_towards_player(self, player_pos):
        """
        Move one square towards the player's position, avoiding (0, 0).

        :param player_pos: Tuple (row, col) of the player's current position
        """
        r, c = self.position
        pr, pc = player_pos
        dr = pr - r
        dc = pc - c

        # Determine the direction to move (one square)
        move_r = (1 if dr > 0 else -1) if dr != 0 else 0
        move_c = (1 if dc > 0 else -1) if dc != 0 else 0

        new_r = r + move_r
        new_c = c + move_c

        # Ensure the enemy stays within the grid bounds and doesn't move into (0,0)
        if (new_r, new_c) == (0, 0):
            # Try alternative moves to avoid (0, 0)
            alternative_moves = [
                (r + move_r, c),  # Move vertically
                (r, c + move_c),  # Move horizontally
                (r - move_r, c),  # Move opposite vertically
                (r, c - move_c)   # Move opposite horizontally
            ]
            for alt_r, alt_c in alternative_moves:
                if 0 <= alt_r < GRID_SIZE and 0 <= alt_c < GRID_SIZE and (alt_r, alt_c) != (0, 0):
                    new_r, new_c = alt_r, alt_c
                    break
            else:
                # Stay in place if no alternative moves are available
                new_r, new_c = r, c
        else:
            # Ensure the enemy stays within the grid bounds
            new_r = max(0, min(GRID_SIZE - 1, new_r))
            new_c = max(0, min(GRID_SIZE - 1, new_c))

        self.position = (new_r, new_c)

def initialize_game(complexity_level):
    """
    Initialize the game state based on the selected complexity level.

    :param complexity_level: Integer from 1 to 10 representing difficulty
    :return: Tuple (player_pos, end_pos, enemies)
    """
    # Initialize player and end positions
    player_pos = (0, 0)  # Top-left corner
    end_pos = (GRID_SIZE - 1, GRID_SIZE - 1)  # Bottom-right corner

    # Determine the number of enemies based on complexity level
    num_enemies = complexity_level  # Simple scaling; adjust as needed

    # Generate enemies with movement patterns based on complexity level
    enemies = []
    for i in range(num_enemies):
        symbol = ENEMY_SYMBOLS[i % len(ENEMY_SYMBOLS)]
        pattern = generate_enemy_pattern(complexity_level)
        adaptive = complexity_level >= 8 and random.random() < 0.5  # 50% chance of being adaptive at high complexity
        enemies.append(Enemy(symbol, pattern, adaptive))

    return player_pos, end_pos, enemies

def generate_enemy_pattern(complexity_level):
    """
    Generate a movement pattern for an enemy based on complexity level.

    :param complexity_level: Integer from 1 to 10 representing difficulty
    :return: List of (row, col) tuples
    """
    pattern_length = max(4, complexity_level * 2)  # Longer patterns at higher complexity
    pattern = []

    # Start position (exclude (0,0))
    while True:
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        if (r, c) != (0, 0):
            break
    pattern.append((r, c))

    while len(pattern) < pattern_length:
        # Determine possible moves (only one square in any direction)
        possible_moves = [(-1, 0), (1, 0), (0, -1), (0, 1),
                         (-1, -1), (-1, 1), (1, -1), (1, 1)]
        # At higher complexity levels, prefer diagonal moves
        if complexity_level >= 5:
            weighted_moves = possible_moves.copy()
            # Add more diagonal moves to increase pattern complexity
            weighted_moves += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            weighted_moves = possible_moves.copy()

        dr, dc = random.choice(weighted_moves)
        r_new = pattern[-1][0] + dr
        c_new = pattern[-1][1] + dc

        # Ensure the enemy stays within the grid bounds and doesn't move into (0,0)
        if (r_new, c_new) == (0, 0):
            # Skip this move and try another
            continue
        r_new = max(0, min(GRID_SIZE - 1, r_new))
        c_new = max(0, min(GRID_SIZE - 1, c_new))

        if (r_new, c_new) == (0, 0):
            continue

        pattern.append((r_new, c_new))

    return pattern

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
        if (r, c) == (0, 0):
            # Ensure enemies are not placed at the player's starting square
            continue
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
    # Get complexity level from user
    while True:
        try:
            complexity_level = int(input("Enter enemy pattern complexity level (1-10): "))
            if 1 <= complexity_level <= 10:
                break
            else:
                print("Please enter a number between 1 and 10.")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 10.")

    player_pos, end_pos, enemies = initialize_game(complexity_level)
    turn = 0
    max_turns = 200  # Increased turn limit for larger grid and complexity

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
            enemy.move(player_pos if enemy.adaptive else None)

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
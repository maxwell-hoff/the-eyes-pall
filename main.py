import os
import time

# Define the grid size
GRID_SIZE = 4

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'E'
ENEMY_SYMBOLS = ['X', 'Y']  # You can add more symbols for more enemies

# Directions for player movement
MOVES = {
    'w': (-1, 0),  # Up
    's': (1, 0),   # Down
    'a': (0, -1),  # Left
    'd': (0, 1),   # Right
    'f': (0, 0)  # Stay
}

def clear_screen():
    # Clear the terminal screen for better readability
    os.system('cls' if os.name == 'nt' else 'clear')

class Enemy:
    def __init__(self, symbol, pattern):
        """
        symbol: Single character representing the enemy
        pattern: List of (row, col) tuples defining the movement pattern
        """
        self.symbol = symbol
        self.pattern = pattern
        self.current_step = 0
        self.position = self.pattern[self.current_step]

    def move(self):
        # Advance to the next step in the pattern
        self.current_step = (self.current_step + 1) % len(self.pattern)
        self.position = self.pattern[self.current_step]

def initialize_game():
    # Initialize player and end positions
    player_pos = (0, 0)  # Top-left corner
    end_pos = (3, 3)     # Bottom-right corner

    # Define enemies with their movement patterns
    # Example: Enemy X moves in a square clockwise
    enemy1_pattern = [(0, 2), (1, 2), (1, 3), (0, 3)]
    enemy2_pattern = [(2, 0), (2, 1), (3, 1), (3, 0)]

    enemies = [
        Enemy(ENEMY_SYMBOLS[0], enemy1_pattern),
        Enemy(ENEMY_SYMBOLS[1], enemy2_pattern)
    ]

    return player_pos, end_pos, enemies

def draw_grid(player_pos, end_pos, enemies):
    grid = [[EMPTY_SYMBOL for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    # Place the end position
    grid[end_pos[0]][end_pos[1]] = END_SYMBOL

    # Place enemies
    for enemy in enemies:
        r, c = enemy.position
        grid[r][c] = enemy.symbol

    # Place the player
    pr, pc = player_pos
    if grid[pr][pc] == EMPTY_SYMBOL or grid[pr][pc] == END_SYMBOL:
        grid[pr][pc] = PLAYER_SYMBOL
    else:
        # Player is on the same square as an enemy or the end
        grid[pr][pc] = PLAYER_SYMBOL  # Will handle collision separately

    # Print the grid
    print("Grid:")
    print("  " + " ".join([str(c) for c in range(GRID_SIZE)]))
    for idx, row in enumerate(grid):
        print(str(idx) + " " + " ".join(row))
    print("\nLegend: P=Player, E=End, X/Y=Enemies, .=Empty")

def get_player_move():
    print("\nMove (w=up, s=down, a=left, d=right, f=stay): ", end='')
    move = input().strip().lower()
    if move not in MOVES:
        print("Invalid move. Please enter 'w', 'a', 's', 'd', or 'f'.")
        return get_player_move()
    return MOVES[move]

def is_collision(player_pos, enemies):
    for enemy in enemies:
        if player_pos == enemy.position:
            return True
    return False

def main():
    player_pos, end_pos, enemies = initialize_game()
    turn = 0
    max_turns = 50  # To prevent infinite games

    while turn < max_turns:
        clear_screen()
        print(f"Turn: {turn}")
        draw_grid(player_pos, end_pos, enemies)

        # Check if player has reached the end
        if player_pos == end_pos:
            print("Congratulations! You've reached the end and won the game!")
            return

        # Get player move
        move = get_player_move()
        new_r = player_pos[0] + move[0]
        new_c = player_pos[1] + move[1]

        # Check boundaries
        if 0 <= new_r < GRID_SIZE and 0 <= new_c < GRID_SIZE:
            player_pos = (new_r, new_c)
        else:
            print("Move out of bounds. Try again.")
            time.sleep(1)
            continue

        # Move enemies
        for enemy in enemies:
            enemy.move()

        # Check for collisions
        if is_collision(player_pos, enemies):
            clear_screen()
            draw_grid(player_pos, end_pos, enemies)
            print("Oh no! You've been caught by an enemy. Game Over.")
            return

        turn += 1

    print("Maximum turns reached. Game Over.")
    return

if __name__ == "__main__":
    main()
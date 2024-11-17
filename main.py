import os
import time

# Define the grid size
GRID_SIZE = 10

# Define symbols
EMPTY_SYMBOL = '.'
PLAYER_SYMBOL = 'P'
END_SYMBOL = 'E'
ENEMY_SYMBOLS = ['X', 'Y', 'Z', 'W', 'V']  # Extend as needed for more enemies

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
    player_pos = (0, 0)    # Top-left corner
    end_pos = (9, 9)       # Bottom-right corner

    # Define enemies with their movement patterns
    enemies = [
        Enemy('X', [  # Enemy X: Moves in a square clockwise
            (0, 3), (1, 3), (1, 4), (0, 4)
        ]),
        Enemy('Y', [  # Enemy Y: Vertical oscillation between rows 2 and 7 in column 6
            (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6), (6, 6), (5, 6), (4, 6), (3, 6)
        ]),
        Enemy('Z', [  # Enemy Z: Diagonal movement from top-left to bottom-right and back
            (2, 2), (3, 3), (4, 4), (5, 5), (4, 4), (3, 3)
        ]),
        Enemy('W', [  # Enemy W: Zig-zag horizontally across row 5
            (5, 0), (5, 1), (5, 2), (5, 1), (5, 0), (5, 1), (5, 2)
        ]),
        Enemy('V', [  # Enemy V: Circular movement around a center point
            (7, 2), (7, 3), (8, 3), (8, 2), (8, 1), (7, 1), (7, 2)
        ]),
        # Add more enemies with complex patterns as desired
    ]

    return player_pos, end_pos, enemies

def draw_grid(player_pos, end_pos, enemies):
    grid = [[EMPTY_SYMBOL for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    # Place the end position
    er, ec = end_pos
    grid[er][ec] = END_SYMBOL

    # Place enemies
    for enemy in enemies:
        r, c = enemy.position
        if grid[r][c] == EMPTY_SYMBOL or grid[r][c] == END_SYMBOL:
            grid[r][c] = enemy.symbol
        else:
            # If multiple enemies occupy the same cell, display a special symbol or choose one
            grid[r][c] = enemy.symbol  # For simplicity, display the last enemy's symbol

    # Place the player
    pr, pc = player_pos
    if grid[pr][pc] == EMPTY_SYMBOL or grid[pr][pc] == END_SYMBOL:
        grid[pr][pc] = PLAYER_SYMBOL
    else:
        # Player is on the same square as an enemy or the end
        grid[pr][pc] = PLAYER_SYMBOL  # Collision handled separately

    # Print the grid with row and column indices
    header = "   " + " ".join([f"{c:2}" for c in range(GRID_SIZE)])
    print(header)
    for idx, row in enumerate(grid):
        row_str = f"{idx:2} " + " ".join([f"{cell:2}" for cell in row])
        print(row_str)
    print("\nLegend: P=Player, E=End, X/Y/Z/W/V=Enemies, .=Empty")

def get_player_move():
    valid_moves = list(MOVES.keys())
    move = input("\nMove (w=up, s=down, a=left, d=right, f=stay): ").strip().lower()
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
    max_turns = 100  # Increased turn limit for larger grid

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
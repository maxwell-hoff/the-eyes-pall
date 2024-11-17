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
    'f': (0, 0)  # Stay
}

def clear_screen():
    # Clear the terminal screen for better readability
    os.system('cls' if os.name == 'nt' else 'clear')

class Enemy:
    def __init__(self, symbol, pattern, adaptive=False):
        """
        symbol: Single character representing the enemy
        pattern: List of (row, col) tuples defining the movement pattern
        adaptive: Boolean indicating if the enemy adapts to the player's position
        """
        self.symbol = symbol
        self.pattern = pattern
        self.adaptive = adaptive
        self.current_step = 0
        self.position = self.pattern[self.current_step]
    
    def move(self, player_pos=None):
        if self.adaptive and player_pos:
            # Simple adaptive behavior: move towards the player if within a certain range
            self.move_towards_player(player_pos)
        else:
            # Advance to the next step in the pattern
            self.current_step = (self.current_step + 1) % len(self.pattern)
            self.position = self.pattern[self.current_step]
    
    def move_towards_player(self, player_pos):
        r, c = self.position
        pr, pc = player_pos
        dr = pr - r
        dc = pc - c
        if abs(dr) > abs(dc):
            r += (1 if dr > 0 else -1) if dr != 0 else 0
        else:
            c += (1 if dc > 0 else -1) if dc != 0 else 0
        # Ensure the enemy stays within the grid bounds
        self.position = (max(0, min(GRID_SIZE - 1, r)), max(0, min(GRID_SIZE - 1, c)))

def initialize_game(complexity_level):
    # Initialize player and end positions
    player_pos = (0, 0)    # Top-left corner
    end_pos = (GRID_SIZE - 1, GRID_SIZE - 1)       # Bottom-right corner

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
    pattern_length = max(4, complexity_level * 2)  # Longer patterns at higher complexity
    pattern = []

    # Start position
    r = random.randint(0, GRID_SIZE - 1)
    c = random.randint(0, GRID_SIZE - 1)

    for _ in range(pattern_length):
        # Determine possible moves
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        # At higher complexity levels, include diagonal moves
        if complexity_level >= 5:
            moves.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        # At the highest complexity, include random jumps
        if complexity_level >= 9:
            moves.extend([(random.randint(-2, 2), random.randint(-2, 2))])

        dr, dc = random.choice(moves)
        r_new = r + dr
        c_new = c + dc
        # Ensure the enemy stays within the grid bounds
        r_new = max(0, min(GRID_SIZE - 1, r_new))
        c_new = max(0, min(GRID_SIZE - 1, c_new))
        pattern.append((r_new, c_new))
        r, c = r_new, c_new

    return pattern

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
            grid[r][c] = '*'  # Indicate multiple enemies

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
    print("\nLegend: P=Player, E=End, X/Y/Z/W/V/Q/R/S/T/U=Enemies, *=Multiple Enemies, .=Empty")

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
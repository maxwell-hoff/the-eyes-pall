import networkx as nx
import yaml
import pygame
import random

# Load configuration
with open('test/config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Define the Piece class
class Piece:
    def __init__(self, piece_type, owner, position, movement_range, attack_capability, attack_range=1, visibility_range=0):
        self.piece_type = piece_type
        self.owner = owner
        self.position = tuple(position)
        self.movement_range = movement_range
        self.attack_capability = attack_capability
        self.attack_range = attack_range
        self.visibility_range = visibility_range  # Add visibility range

# Create the board as a grid graph
def create_board(width, height, special_nodes, impassable_nodes):
    board = nx.grid_2d_graph(width, height)
    nx.set_node_attributes(board, None, 'special')
    nx.set_node_attributes(board, True, 'passable')
    for node in special_nodes:
        position = tuple(node['position'])
        special = node['special']
        if position in board:
            board.nodes[position]['special'] = special
    for position in impassable_nodes:
        position = tuple(position)
        if position in board:
            board.nodes[position]['passable'] = False
            # Remove edges to this node to prevent movement into it
            for neighbor in list(board.neighbors(position)):
                board.remove_edge(position, neighbor)
    return board

# Create pieces
def create_pieces(pieces_config):
    pieces = []
    for p in pieces_config:
        attack_range = p.get('attack_range', 1)
        visibility_range = p.get('visibility_range', 0)
        piece = Piece(
            piece_type=p['type'],
            owner=p['owner'],
            position=p['position'],
            movement_range=p['movement_range'],
            attack_capability=p['attack_capability'],
            attack_range=attack_range,
            visibility_range=visibility_range
        )
        pieces.append(piece)
    return pieces

# Initialize board and pieces
board = create_board(
    config['board']['width'],
    config['board']['height'],
    config['board'].get('special_nodes', []),
    config['board'].get('impassable_nodes', [])
)
pieces = create_pieces(config['pieces'])

def is_position_occupied(position):
    return any(p.position == position for p in pieces)

def move_piece(piece, target_position):
    # Validate movement range
    if not board.nodes[target_position].get('passable', True):
        print(f"Cannot move to impassable square {target_position}")
        return False
    if is_position_occupied(target_position):
        print(f"Cannot move to occupied square {target_position}")
        return False
    try:
        path = nx.shortest_path(board, piece.position, target_position)
        if len(path) - 1 <= piece.movement_range:
            piece.position = target_position
            return True
        else:
            print(f"{piece.piece_type} cannot move that far.")
            return False
    except nx.NetworkXNoPath:
        print(f"No path between {piece.position} and {target_position}")
        return False

def get_positions_within_range(position, max_range):
    positions = set()
    visited = set()
    queue = [(position, 0)]
    while queue:
        current_position, distance = queue.pop(0)
        if distance > max_range:
            continue
        if current_position != position:
            positions.add(current_position)
        visited.add(current_position)
        for neighbor in board.neighbors(current_position):
            if neighbor not in visited and board.nodes[neighbor].get('passable', True):
                queue.append((neighbor, distance + 1))
    return positions

def resolve_attacks():
    # For AI pieces that can attack after moving
    for piece in pieces:
        if piece.owner == 'Player2' and piece.attack_range > 0 and piece.attack_capability:
            positions_in_attack_range = get_positions_within_range(piece.position, piece.attack_range)
            for target_piece in pieces:
                if (target_piece.owner != piece.owner and
                    target_piece.position in positions_in_attack_range and
                    target_piece.piece_type in piece.attack_capability):
                    print(f"{piece.owner}'s {piece.piece_type} at {piece.position} attacks {target_piece.owner}'s {target_piece.piece_type} at {target_piece.position}")
                    pieces.remove(target_piece)

# Pygame setup
pygame.init()

CELL_SIZE = 60
GRID_WIDTH = config['board']['width']
GRID_HEIGHT = config['board']['height']
INFO_PANEL_HEIGHT = 100  # Height for the text panel
WINDOW_SIZE = (GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE + INFO_PANEL_HEIGHT)
FPS = 30

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER1_COLOR = (0, 0, 255)
PLAYER2_COLOR = (255, 0, 0)
SPECIAL_COLOR = (0, 255, 0)

screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Custom Grid Game")
font = pygame.font.Font(None, 24)

def draw_board():
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + INFO_PANEL_HEIGHT, CELL_SIZE, CELL_SIZE)
            position = (x, y)
            special = board.nodes[position].get('special', None)
            passable = board.nodes[position].get('passable', True)
            if not passable:
                color = BLACK
            elif special == 'stealth':
                color = SPECIAL_COLOR
            else:
                color = WHITE
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

def draw_pieces():
    for piece in pieces:
        x, y = piece.position
        center = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + INFO_PANEL_HEIGHT + CELL_SIZE // 2)
        radius = CELL_SIZE // 3
        color = PLAYER1_COLOR if piece.owner == 'Player1' else PLAYER2_COLOR
        pygame.draw.circle(screen, color, center, radius)
        text = font.render(piece.piece_type[0], True, BLACK)
        text_rect = text.get_rect(center=center)
        screen.blit(text, text_rect)

def draw_info():
    # Clear the info panel
    info_rect = pygame.Rect(0, 0, WINDOW_SIZE[0], INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, WHITE, info_rect)

    # Prepare the text
    texts = []
    for piece in pieces:
        text = f"{piece.owner}'s {piece.piece_type}: At {piece.position}, Attack Range={piece.attack_range}, Attack Capability={piece.attack_capability}"
        texts.append(text)

    # Render the texts
    y_offset = 10
    for text in texts:
        text_surface = font.render(text, True, BLACK)
        screen.blit(text_surface, (10, y_offset))
        y_offset += 20  # Adjust the spacing as needed

def get_user_move(piece):
    while True:
        draw_board()
        draw_pieces()
        draw_info()
        pygame.display.flip()

        print(f"Select action for your {piece.piece_type} at {piece.position}:")
        print("Press 'm' to Move or 'a' to Attack")

        action_selected = False
        while not action_selected:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        action = 'move'
                        action_selected = True
                    elif event.key == pygame.K_a:
                        action = 'attack'
                        action_selected = True

        if action == 'move':
            # Calculate possible moves
            possible_moves = []
            visited = set()
            queue = [(piece.position, 0)]
            while queue:
                current_position, distance = queue.pop(0)
                if distance > piece.movement_range:
                    continue
                if current_position != piece.position and not is_position_occupied(current_position):
                    possible_moves.append(current_position)
                visited.add(current_position)
                for neighbor in board.neighbors(current_position):
                    if neighbor not in visited and board.nodes[neighbor].get('passable', True):
                        queue.append((neighbor, distance + 1))

            moving = True
            while moving:
                draw_board()
                # Highlight possible moves
                for pos in possible_moves:
                    x, y = pos
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + INFO_PANEL_HEIGHT, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(screen, (173, 216, 230), rect)  # Light blue
                    pygame.draw.rect(screen, BLACK, rect, 1)
                draw_pieces()
                draw_info()
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        x = mouse_pos[0] // CELL_SIZE
                        y = (mouse_pos[1] - INFO_PANEL_HEIGHT) // CELL_SIZE
                        target_position = (x, y)
                        if target_position in possible_moves:
                            move_piece(piece, target_position)
                            moving = False
                            break
            break  # Exit after moving

        elif action == 'attack':
            # Calculate attackable positions
            attackable_positions = set()
            if piece.attack_range > 0:
                positions_in_attack_range = get_positions_within_range(piece.position, piece.attack_range)
                for p in pieces:
                    if p.owner != piece.owner and p.position in positions_in_attack_range and p.piece_type in piece.attack_capability:
                        attackable_positions.add(p.position)
                if attackable_positions:
                    attacking = True
                    while attacking:
                        draw_board()
                        draw_pieces()
                        # Highlight attackable positions
                        for pos in attackable_positions:
                            x, y = pos
                            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + INFO_PANEL_HEIGHT, CELL_SIZE, CELL_SIZE)
                            pygame.draw.rect(screen, (255, 0, 0), rect)  # Red
                            pygame.draw.rect(screen, BLACK, rect, 1)
                        draw_info()
                        pygame.display.flip()
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                exit()
                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                mouse_pos = event.pos
                                x = mouse_pos[0] // CELL_SIZE
                                y = (mouse_pos[1] - INFO_PANEL_HEIGHT) // CELL_SIZE
                                target_position = (x, y)
                                if target_position in attackable_positions:
                                    # Perform attack
                                    target_piece = next((p for p in pieces if p.position == target_position and p.owner != piece.owner), None)
                                    if target_piece:
                                        print(f"{piece.owner}'s {piece.piece_type} at {piece.position} attacks {target_piece.owner}'s {target_piece.piece_type} at {target_piece.position}")
                                        pieces.remove(target_piece)
                                    attacking = False
                                    break
                    break  # Exit after attacking
                else:
                    print("No enemies in range to attack.")
                    break  # Exit if no attack possible
            else:
                print("This piece cannot attack.")
                break  # Exit if no attack possible

def get_ai_move(piece):
    if piece.piece_type == 'Recon':
        # Recon drone logic
        # Move towards the nearest Player1 piece
        player1_pieces = [p for p in pieces if p.owner == 'Player1']
        if player1_pieces:
            # Find the closest Player1 piece
            distances = []
            for p in player1_pieces:
                try:
                    path = nx.shortest_path(board, piece.position, p.position)
                    distances.append((len(path) - 1, p.position))
                except nx.NetworkXNoPath:
                    continue
            if distances:
                distances.sort()
                _, target_position = distances[0]
                # Move towards the target
                path = nx.shortest_path(board, piece.position, target_position)
                if len(path) > 1:
                    next_position = path[1]
                    if board.nodes[next_position].get('passable', True) and not is_position_occupied(next_position):
                        move_piece(piece, next_position)
    else:
        # Attack drone logic
        # Check if any Player1 piece is within the visibility range of any recon drone
        recon_drones = [p for p in pieces if p.owner == 'Player2' and p.piece_type == 'Recon']
        detected_positions = set()
        for recon in recon_drones:
            positions_in_visibility = get_positions_within_range(recon.position, recon.visibility_range)
            for p in pieces:
                if p.owner == 'Player1' and p.position in positions_in_visibility:
                    detected_positions.add(p.position)
        if detected_positions:
            # Move towards the nearest detected Player1 piece
            target_positions = list(detected_positions)
            distances = []
            for pos in target_positions:
                try:
                    path = nx.shortest_path(board, piece.position, pos)
                    distances.append((len(path) - 1, pos))
                except nx.NetworkXNoPath:
                    continue
            if distances:
                distances.sort()
                _, target_position = distances[0]
                # Move towards the target
                path = nx.shortest_path(board, piece.position, target_position)
                if len(path) > 1:
                    next_position = path[1]
                    if board.nodes[next_position].get('passable', True) and not is_position_occupied(next_position):
                        move_piece(piece, next_position)
        else:
            # Remain idle or patrol
            pass  # For now, do nothing

def game_loop():
    clock = pygame.time.Clock()
    running = True
    while running:
        for player in ['Player1', 'Player2']:
            for piece in [p for p in pieces if p.owner == player]:
                if player == 'Player1':
                    get_user_move(piece)
                else:
                    get_ai_move(piece)

                # Redraw after each move
                draw_board()
                draw_pieces()
                draw_info()
                pygame.display.flip()

                # Check victory conditions
                if not any(p for p in pieces if p.piece_type == 'Commander' and p.owner == 'Player1'):
                    print("Player2 wins!")
                    running = False
                    break
                if not any(p for p in pieces if p.piece_type == 'Commander' and p.owner == 'Player2'):
                    print("Player1 wins!")
                    running = False
                    break
            if not running:
                break

        # After all moves, resolve attacks
        resolve_attacks()

        # Redraw after attacks
        draw_board()
        draw_pieces()
        draw_info()
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    game_loop()
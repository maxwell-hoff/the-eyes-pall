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

board = create_board(
    config['board']['width'],
    config['board']['height'],
    config['board'].get('special_nodes', []),
    config['board'].get('impassable_nodes', [])
)
pieces = create_pieces(config['pieces'])

player1_had_commander = any(p.owner == 'Player1' and p.piece_type == 'Commander' for p in pieces)
player2_had_commander = any(p.owner == 'Player2' and p.piece_type == 'Commander' for p in pieces)

# Count total Player1 pieces for Recon logic
initial_player1_positions = {(p.position): p for p in pieces if p.owner == 'Player1'}
total_player1_pieces = len(initial_player1_positions)

def is_position_occupied(position):
    return any(p.position == position for p in pieces)

def log_move(action_str):
    moves_log.append(action_str)
    # Keep only the last 5
    if len(moves_log) > 5:
        moves_log.pop(0)

def move_piece(piece, target_position):
    if not board.nodes[target_position].get('passable', True):
        print(f"Cannot move to impassable square {target_position}")
        return False
    if is_position_occupied(target_position):
        print(f"Cannot move to occupied square {target_position}")
        return False
    try:
        path = nx.shortest_path(board, piece.position, target_position)
        if len(path) - 1 <= piece.movement_range:
            old_pos = piece.position
            piece.position = target_position
            log_move(f"{piece.owner}'s {piece.piece_type} moved from {old_pos} to {target_position}")
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
    for piece in pieces[:]:  # Use a copy as we might remove pieces
        if piece.owner == 'Player2' and piece.attack_range > 0 and piece.attack_capability:
            positions_in_attack_range = get_positions_within_range(piece.position, piece.attack_range)
            for target_piece in pieces[:]:
                if (target_piece.owner != piece.owner and
                    target_piece.position in positions_in_attack_range and
                    target_piece.piece_type in piece.attack_capability):
                    print(f"{piece.owner}'s {piece.piece_type} at {piece.position} attacks {target_piece.owner}'s {target_piece.piece_type} at {target_piece.position}")
                    log_move(f"{piece.owner}'s {piece.piece_type} attacks {target_piece.owner}'s {target_piece.piece_type} at {target_piece.position}")
                    pieces.remove(target_piece)

pygame.init()

CELL_SIZE = 60
GRID_WIDTH = config['board']['width']
GRID_HEIGHT = config['board']['height']
INFO_PANEL_HEIGHT = 200
WINDOW_SIZE = (GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE + INFO_PANEL_HEIGHT)
FPS = 30

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER1_COLOR = (0, 0, 255)
PLAYER2_COLOR = (255, 0, 0)
SPECIAL_COLOR = (0, 255, 0)

screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Custom Grid Game")
font = pygame.font.Font(None, 20)

current_turn_message = ""
moves_log = []

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

def piece_at_mouse(mouse_pos):
    # Convert mouse coordinates to board coordinates
    mx, my = mouse_pos
    if my < INFO_PANEL_HEIGHT:
        return None
    bx = mx // CELL_SIZE
    by = (my - INFO_PANEL_HEIGHT) // CELL_SIZE
    board_pos = (bx, by)
    for piece in pieces:
        if piece.position == board_pos:
            return piece
    return None

def draw_info(hovered_piece):
    # Clear the info panel
    info_rect = pygame.Rect(0, 0, WINDOW_SIZE[0], INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, WHITE, info_rect)

    y_offset = 10

    # Display current turn message if any
    if current_turn_message:
        msg_surface = font.render(current_turn_message, True, BLACK)
        screen.blit(msg_surface, (10, y_offset))
        y_offset += 30

    # Show last 5 moves
    if moves_log:
        # Title for move log
        log_title_surface = font.render("Last Moves:", True, BLACK)
        screen.blit(log_title_surface, (10, y_offset))
        y_offset += 20
        for move_str in moves_log:
            move_surface = font.render(move_str, True, BLACK)
            screen.blit(move_surface, (10, y_offset))
            y_offset += 20

    # If hovered over a piece, show its info
    if hovered_piece is not None:
        y_offset += 10
        piece_info = (
            f"{hovered_piece.owner}'s {hovered_piece.piece_type}\n"
            f"Position: {hovered_piece.position}\n"
            f"Move Range: {hovered_piece.movement_range}\n"
            f"Attack Range: {hovered_piece.attack_range}\n"
            f"Attack Capability: {hovered_piece.attack_capability}"
        )
        # Render multiline
        for line in piece_info.split("\n"):
            line_surf = font.render(line, True, BLACK)
            screen.blit(line_surf, (10, y_offset))
            y_offset += 20

def get_user_move(piece):
    global current_turn_message
    current_turn_message = f"It is {piece.owner}'s {piece.piece_type} turn. Press 'm' to Move or 'a' to Attack."

    while True:
        hovered_piece = piece_at_mouse(pygame.mouse.get_pos())
        draw_board()
        draw_pieces()
        draw_info(hovered_piece)
        pygame.display.flip()

        action_selected = False
        action = None
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

        if not action_selected:
            continue

        if action == 'move':
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
                hovered_piece = piece_at_mouse(pygame.mouse.get_pos())
                draw_board()
                # Highlight possible moves
                for pos in possible_moves:
                    x, y = pos
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + INFO_PANEL_HEIGHT, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(screen, (173, 216, 230), rect)  # Light blue
                    pygame.draw.rect(screen, BLACK, rect, 1)
                draw_pieces()
                draw_info(hovered_piece)
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = event.pos
                        tx = mx // CELL_SIZE
                        ty = (my - INFO_PANEL_HEIGHT) // CELL_SIZE
                        target_position = (tx, ty)
                        if target_position in possible_moves:
                            move_piece(piece, target_position)
                            moving = False
                            break
            break  # Exit after moving

        elif action == 'attack':
            attackable_positions = set()
            if piece.attack_range > 0:
                positions_in_attack_range = get_positions_within_range(piece.position, piece.attack_range)
                for p in pieces:
                    if p.owner != piece.owner and p.position in positions_in_attack_range and p.piece_type in piece.attack_capability:
                        attackable_positions.add(p.position)
                if attackable_positions:
                    attacking = True
                    while attacking:
                        hovered_piece = piece_at_mouse(pygame.mouse.get_pos())
                        draw_board()
                        draw_pieces()
                        # Highlight attackable positions
                        for pos in attackable_positions:
                            x, y = pos
                            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + INFO_PANEL_HEIGHT, CELL_SIZE, CELL_SIZE)
                            pygame.draw.rect(screen, (255, 0, 0), rect)  # Red
                            pygame.draw.rect(screen, BLACK, rect, 1)
                        draw_info(hovered_piece)
                        pygame.display.flip()
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                exit()
                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                mx, my = event.pos
                                tx = mx // CELL_SIZE
                                ty = (my - INFO_PANEL_HEIGHT) // CELL_SIZE
                                target_position = (tx, ty)
                                if target_position in attackable_positions:
                                    target_piece = next((p for p in pieces if p.position == target_position and p.owner != piece.owner), None)
                                    if target_piece:
                                        print(f"{piece.owner}'s {piece.piece_type} at {piece.position} attacks {target_piece.owner}'s {target_piece.piece_type} at {target_piece.position}")
                                        log_move(f"{piece.owner}'s {piece.piece_type} attacks {target_piece.owner}'s {target_piece.piece_type} at {target_piece.position}")
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

    current_turn_message = ""

# Recon AI State
recon_state = {
    'visited_positions': set(),
    'discovered_player1_positions': set(),
    'search_mode': 'explore',  # 'explore', 'search_area', 'monitor'
    'search_center': None,
    'search_attempts': 0
}

def get_ai_move(piece):
    if piece.piece_type == 'Recon':
        # Recon logic:
        # 1. If sees Player1 pieces, record them and switch to 'search_area' mode around them.
        # 2. If in search_area mode and no new pieces found after some tries, revert to explore mode.
        # 3. In explore mode, try to move to unexplored positions.
        # 4. Once all Player1 pieces discovered, move to 'monitor' mode and hover around them.

        # Update discovered Player1 pieces if any are visible
        positions_in_visibility = get_positions_within_range(piece.position, piece.visibility_range)
        visible_player1 = [p for p in pieces if p.owner == 'Player1' and p.position in positions_in_visibility]

        # Record newly discovered pieces
        for vp in visible_player1:
            recon_state['discovered_player1_positions'].add(vp.position)

        discovered_count = len(recon_state['discovered_player1_positions'])

        # Check if all Player1 pieces discovered
        all_discovered = (discovered_count == total_player1_pieces)

        # State transitions
        if visible_player1 and not all_discovered:
            # We have found at least one piece, let's search the area around it
            if recon_state['search_mode'] != 'search_area':
                # Set center to the position of a found piece
                recon_state['search_center'] = visible_player1[0].position
                recon_state['search_mode'] = 'search_area'
                recon_state['search_attempts'] = 0
        elif all_discovered:
            # All discovered, move to monitor mode
            recon_state['search_mode'] = 'monitor'
        else:
            # No one visible
            if recon_state['search_mode'] == 'search_area':
                # If we're searching the area but not finding anyone new after several attempts:
                recon_state['search_attempts'] += 1
                if recon_state['search_attempts'] > 5:
                    # Give up and go back to exploring
                    recon_state['search_mode'] = 'explore'
                    recon_state['search_center'] = None
                    recon_state['search_attempts'] = 0

        # Behaviors
        if recon_state['search_mode'] == 'monitor' and all_discovered:
            # Monitor mode: bounce around discovered pieces
            # Just pick one discovered piece and move around it to keep it in range
            target_positions = list(recon_state['discovered_player1_positions'])
            # Find a vantage point near one discovered piece
            # We'll just pick a random discovered piece and stand within visibility_range of it
            target = random.choice(target_positions)
            # If already in range, maybe move a bit around it
            if piece.position in get_positions_within_range(target, piece.visibility_range):
                # Move randomly nearby
                neighbors = list(board.neighbors(piece.position))
                random.shuffle(neighbors)
                for npos in neighbors:
                    if board.nodes[npos].get('passable', True) and not is_position_occupied(npos):
                        move_piece(piece, npos)
                        break
            else:
                # Move closer to that discovered piece
                move_towards(piece, target)
        elif recon_state['search_mode'] == 'search_area' and recon_state['search_center'] is not None:
            # Search around search_center
            # Move to a nearby tile not visited yet to see if we can spot more player1 units
            target = find_unvisited_near_center(recon_state['search_center'], piece)
            if target:
                move_towards(piece, target)
            else:
                # If no unvisited tiles near center, just move randomly nearby
                random_move(piece)
        else:
            # Explore mode
            # Find an unvisited passable node
            target = find_unvisited_passable_node(piece)
            if target:
                move_towards(piece, target)
            else:
                # If no unvisited found, just move randomly
                random_move(piece)

        # Mark current position as visited
        recon_state['visited_positions'].add(piece.position)

    else:
        # Attack drone logic: remain as before (unchanged)
        # Check if any Player1 piece is visible by recon drones
        recon_drones = [p for p in pieces if p.owner == 'Player2' and p.piece_type == 'Recon']
        detected_positions = set()
        for recon in recon_drones:
            positions_in_visibility = get_positions_within_range(recon.position, recon.visibility_range)
            for plp in pieces:
                if plp.owner == 'Player1' and plp.position in positions_in_visibility:
                    detected_positions.add(plp.position)
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
                move_towards(piece, target_position)
        else:
            # Idle if no targets
            pass

def move_towards(piece, target_position):
    # Move piece towards target_position if possible
    try:
        path = nx.shortest_path(board, piece.position, target_position)
        if len(path) > 1:
            next_position = path[1]
            if board.nodes[next_position].get('passable', True) and not is_position_occupied(next_position):
                move_piece(piece, next_position)
    except nx.NetworkXNoPath:
        # No path, do nothing
        pass

def find_unvisited_passable_node(piece):
    # Find a random passable node that is not visited yet
    all_positions = list(board.nodes())
    random.shuffle(all_positions)
    for pos in all_positions:
        if board.nodes[pos].get('passable', True) and pos not in recon_state['visited_positions']:
            return pos
    return None

def find_unvisited_near_center(center, piece):
    # Find a tile near 'center' that is not visited, within some range
    # We'll use a BFS approach starting from center
    from collections import deque
    visited_local = set()
    q = deque([(center, 0)])
    while q:
        pos, dist = q.popleft()
        if dist > piece.visibility_range * 2:  # arbitrary limit to not wander too far
            continue
        if (board.nodes[pos].get('passable', True) and
            pos not in recon_state['visited_positions'] and pos != piece.position):
            return pos
        visited_local.add(pos)
        for n in board.neighbors(pos):
            if n not in visited_local:
                q.append((n, dist+1))
    return None

def random_move(piece):
    # Move the piece to a random adjacent passable and unoccupied node if possible
    neighbors = list(board.neighbors(piece.position))
    random.shuffle(neighbors)
    for npos in neighbors:
        if board.nodes[npos].get('passable', True) and not is_position_occupied(npos):
            move_piece(piece, npos)
            return

def check_victory():
    if player1_had_commander and not any(p for p in pieces if p.piece_type == 'Commander' and p.owner == 'Player1'):
        print("Player2 wins!")
        return True
    if player2_had_commander and not any(p for p in pieces if p.piece_type == 'Commander' and p.owner == 'Player2'):
        print("Player1 wins!")
        return True
    return False

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

                hovered_piece = piece_at_mouse(pygame.mouse.get_pos())
                draw_board()
                draw_pieces()
                draw_info(hovered_piece)
                pygame.display.flip()

                # Check victory conditions
                if check_victory():
                    running = False
                    break
            if not running:
                break

        # After all moves, resolve attacks
        resolve_attacks()

        hovered_piece = piece_at_mouse(pygame.mouse.get_pos())
        draw_board()
        draw_pieces()
        draw_info(hovered_piece)
        pygame.display.flip()

        # Check victory after attacks
        if check_victory():
            running = False

        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    game_loop()

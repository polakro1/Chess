import curses
import time
from flask import Flask, request, jsonify
import requests
import threading
import socket

# Unicode representations for chess pieces
pieces = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟', ' ': ' '
}

# Initial board setup
board = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

# Variable to track which side you are ('white' or 'black')
player_side = 'white'  # Set to 'white' or 'black'

# Game state variables
selection_mode = 'select_piece'  # Modes: 'select_piece', 'select_move', 'error'
selected_piece = None  # Tuple (row, col) of selected piece
last_move = ""  # Variable to keep track of the last move
turn = 'white'  # 'white' or 'black'

client_connected = threading.Event()  # Flag to detect client connection

def initialize_colors():
    curses.start_color()
    curses.use_default_colors()
    # Define custom brown color with values (627, 322, 176)
    curses.init_color(10, 627, 322, 176)
    curses.init_color(11, 400, 400, 400)  # Custom gray color (adjust values as needed)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)     # Red tile
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_BLACK)   # Black tile
    curses.init_pair(3, curses.COLOR_BLACK, 10)                   # Custom brown outline
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_BLUE)    # Blue (select piece)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Green (select move)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Yellow (error)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_RED)     # White piece on red tile
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)   # White piece on black tile
    curses.init_pair(9, 11, curses.COLOR_RED)     # Black piece on red tile
    curses.init_pair(10, 11, curses.COLOR_BLACK)  # Black piece on black tile

def is_legal_move(from_pos, to_pos):
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    piece = board[from_row][from_col]

    # Check if the target square is within bounds
    if not (0 <= to_row < 8 and 0 <= to_col < 8):
        return False

    # Basic checks for moving to an empty square or capturing opponent's piece
    if board[to_row][to_col] != ' ':
        if (player_side == 'white' and board[to_row][to_col].isupper()) or \
           (player_side == 'black' and board[to_row][to_col].islower()):
            return False  # Cannot capture your own piece

    # Movement logic based on piece type
    if piece.lower() == 'p':  # Pawn movement
        direction = -1 if piece.isupper() else 1  # White moves up (-1), black moves down (+1)
        start_row = 6 if piece.isupper() else 1  # Starting row for pawns (6 for white, 1 for black)
        # Moving straight
        if from_col == to_col:
            if to_row == from_row + direction and board[to_row][to_col] == ' ':
                return True  # Move one step forward
            if from_row == start_row and to_row == from_row + 2 * direction and board[to_row][to_col] == ' ':
                return True  # Move two steps forward
        # Capturing
        if abs(from_col - to_col) == 1 and to_row == from_row + direction:
            return True  # Capture move

    elif piece.lower() == 'r':  # Rook movement
        if from_row == to_row or from_col == to_col:
            return path_clear(from_pos, to_pos)

    elif piece.lower() == 'n':  # Knight movement
        if (abs(from_row - to_row) == 2 and abs(from_col - to_col) == 1) or \
           (abs(from_row - to_row) == 1 and abs(from_col - to_col) == 2):
            return True  # Knight can jump over other pieces

    elif piece.lower() == 'b':  # Bishop movement
        if abs(from_row - to_row) == abs(from_col - to_col):
            return path_clear(from_pos, to_pos)

    elif piece.lower() == 'q':  # Queen movement
        if (from_row == to_row or from_col == to_col or
            abs(from_row - to_row) == abs(from_col - to_col)):
            return path_clear(from_pos, to_pos)

    elif piece.lower() == 'k':  # King movement
        if max(abs(from_row - to_row), abs(from_col - to_col)) == 1:
            return True  # One square in any direction

    return False

def path_clear(from_pos, to_pos):
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Determine step direction
    step_row = (to_row - from_row) // max(1, abs(to_row - from_row)) if from_row != to_row else 0
    step_col = (to_col - from_col) // max(1, abs(to_col - from_col)) if from_col != to_col else 0

    # Check all squares in the path between from_pos and to_pos
    current_row, current_col = from_row + step_row, from_col + step_col
    while (current_row, current_col) != (to_row, to_col):
        if board[current_row][current_col] != ' ':
            return False  # Blocked path
        current_row += step_row
        current_col += step_col

    return True

def move_piece(from_pos, to_pos, stdscr):
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    piece = board[from_row][from_col]
    
    # Update the board
    board[to_row][to_col] = piece
    board[from_row][from_col] = ' '
    
    # Check for pawn promotion
    if piece.lower() == 'p':
        if (player_side == 'white' and to_row == 0) or (player_side == 'black' and to_row == 7):
            promoted_piece = prompt_promotion(stdscr, player_side)
            if promoted_piece:
                board[to_row][to_col] = promoted_piece if player_side == 'white' else promoted_piece.lower()
                move_notation = generate_move_notation(piece, from_pos, to_pos) + promoted_piece.upper()
            else:
                move_notation = generate_move_notation(piece, from_pos, to_pos)
        else:
            move_notation = generate_move_notation(piece, from_pos, to_pos)
    else:
        move_notation = generate_move_notation(piece, from_pos, to_pos)
    
    # Print move to the console
    print_move_to_console(stdscr, move_notation)

def prompt_promotion(stdscr, player_side):
    stdscr.addstr(len(board) + 4, 0, "Promote to (Q, R, B, N): ")
    stdscr.refresh()
    promotion_piece = ''
    while True:
        key = stdscr.getch()
        if key in [ord('q'), ord('Q'), ord('r'), ord('R'), ord('b'), ord('B'), ord('n'), ord('N')]:
            promotion_piece = chr(key).upper() if player_side == 'white' else chr(key).lower()
            break
    # Clear the promotion prompt
    stdscr.addstr(len(board) + 4, 0, " " * 30)
    stdscr.refresh()
    return promotion_piece

def parse_move_data(move_data):
    """
    Parses the move notation and extracts from and to positions along with promotion piece if any.

    Parameters:
        move_data (str): Move notation string (e.g., 'e2e4' or 'e7e8Q').

    Returns:
        tuple: ((from_row, from_col), (to_row, to_col), promotion_piece or None)
    """
    col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    
    if len(move_data) < 4:
        return None, None, None  # Invalid move data

    from_col = col_map.get(move_data[0].lower(), None)
    from_row = 8 - int(move_data[1]) if move_data[1].isdigit() else None
    to_col = col_map.get(move_data[2].lower(), None)
    to_row = 8 - int(move_data[3]) if move_data[3].isdigit() else None

    if from_col is None or from_row is None or to_col is None or to_row is None:
        return None, None, None  # Invalid move data

    promotion_piece = move_data[4].upper() if len(move_data) == 5 else None

    return (from_row, from_col), (to_row, to_col), promotion_piece
    
def flash_error(stdscr, row, col):
    global selection_mode, last_move
    selection_mode = 'error'

    # Display the yellow error blink for a short duration
    for _ in range(3):  # Loop for a short duration to create the blink effect
        update_board(stdscr, row, col, last_move)
        stdscr.refresh()
        curses.napms(300)  # Pause for 300 milliseconds

    # Reset to the previous mode
    selection_mode = 'select_piece' if selected_piece is None else 'select_move'

def update_board(stdscr, sel_row, sel_col, last_move):
    stdscr.clear()

    # Top border with width 26
    for x in range(26):
        stdscr.addstr(0, x, "▀", curses.color_pair(3))

    for i, board_row in enumerate(board):
        # Left border for each row
        stdscr.addstr(i + 1, 0, " ", curses.color_pair(3))

        for j, piece in enumerate(board_row):
            # Base tile color
            base_color = curses.color_pair(1) if (i + j) % 2 == 0 else curses.color_pair(2)

            # Determine piece color (white or black)
            if piece.isupper():  # White pieces
                tile_color = curses.color_pair(7) if (i + j) % 2 == 0 else curses.color_pair(8)
            elif piece.islower():  # Black pieces
                tile_color = curses.color_pair(9) if (i + j) % 2 == 0 else curses.color_pair(10)
            else:  # Empty tile
                tile_color = base_color

            # Blinking logic for selected tiles
            if i == sel_row and j == sel_col:
                if selection_mode == 'select_piece':
                    tile_color = curses.color_pair(4) if int(time.time() * 2) % 2 == 0 else tile_color  # Blue blink
                elif selection_mode == 'select_move':
                    tile_color = curses.color_pair(5) if int(time.time() * 2) % 2 == 0 else tile_color  # Green blink
                elif selection_mode == 'error':
                    tile_color = curses.color_pair(6) if int(time.time() * 2) % 2 == 0 else tile_color  # Yellow blink
            else:
                # Highlight the selected piece in green when in select_move mode
                if selection_mode == 'select_move' and selected_piece == (i, j):
                    tile_color = curses.color_pair(5)

            # Fetch Unicode symbol for the piece
            piece_char = pieces[piece]

            # Draw each tile with a three-character width
            stdscr.addstr(i + 1, 1 + j * 3, f" {piece_char} ", tile_color)

        # Right border for each row
        stdscr.addstr(i + 1, 1 + 8 * 3, " ", curses.color_pair(3))

    # Bottom border with width 26
    for x in range(26):
        stdscr.addstr(len(board) + 1, x, "▄", curses.color_pair(3))

    # Print the last move below the board
    stdscr.addstr(len(board) + 3, 0, f"Last move: {last_move}                    ")  # Display the move text
    stdscr.addstr(len(board) + 4, 0, f"Turn: {turn.capitalize()}")
    stdscr.refresh()

def handle_movement_keys(key, row, col):
    if key == curses.KEY_UP:
        row = (row - 1) % 8
    elif key == curses.KEY_DOWN:
        row = (row + 1) % 8
    elif key == curses.KEY_LEFT:
        col = (col - 1) % 8
    elif key == curses.KEY_RIGHT:
        col = (col + 1) % 8
    return row, col

def handle_enter_key(stdscr, row, col, last_move, role, server_address=None):
    global selection_mode, selected_piece, turn
    piece = board[row][col]
    if selection_mode == 'select_piece':
        if (player_side == 'white' and piece.isupper()) or (player_side == 'black' and piece.islower()):
            if turn == player_side:
                selection_mode = 'select_move'
                selected_piece = (row, col)
            else:
                flash_error(stdscr, row, col)
        else:
            flash_error(stdscr, row, col)
    elif selection_mode == 'select_move':
        if turn != player_side:
            flash_error(stdscr, row, col)
            return last_move
        if is_legal_move(selected_piece, (row, col)):
            move_notation = generate_move_notation(board[selected_piece[0]][selected_piece[1]], selected_piece, (row, col))
            last_move = move_notation  # Update the last move
            move_piece(selected_piece, (row, col), stdscr)  # Make the move
            selection_mode = 'select_piece'
            selected_piece = None
            turn = 'black' if turn == 'white' else 'white'
            # Send the move
            if role == 'client' and server_address:
                send_move_to_server(move_notation, server_address)
            elif role == 'server':
                send_move_to_client(move_notation)
        else:
            flash_error(stdscr, row, col)
    return last_move

def handle_escape_key(selection_mode, selected_piece):
    if selection_mode == 'select_move':
        selection_mode = 'select_piece'
        selected_piece = None
    return selection_mode, selected_piece

# Updated board rendering with three-character-wide tiles
def main(stdscr):
    initialize_colors()
    curses.curs_set(0)   # Hide the cursor
    stdscr.nodelay(1)    # Non-blocking input
    stdscr.timeout(100)  # Refresh rate for blinking effect

    role_info = decide_server_or_client(stdscr)  # Ask user to be server or client

    global selection_mode, selected_piece, last_move, turn
    row, col = 0, 0  # Initial selection position

    if isinstance(role_info, tuple) and role_info[0] == 'client':
        server_address = role_info[1]
        stdscr.addstr(4, 0, f"Connected to server at {server_address}:5050. You can start playing.")
        stdscr.refresh()
    else:
        server_address = None

    while True:
        update_board(stdscr, row, col, last_move)  # Draw the board and last move
        handle_received_moves(role_info[0], server_address)  # Handle incoming moves

        key = stdscr.getch()

        # Handle key inputs for selection and movement
        if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            row, col = handle_movement_keys(key, row, col)
        elif key in [ord('\n'), curses.KEY_ENTER]:
            last_move = handle_enter_key(stdscr, row, col, last_move, role_info[0], server_address)
        elif key == 27:  # Escape key
            selection_mode, selected_piece = handle_escape_key(selection_mode, selected_piece)
        elif key == ord('q'):
            break

def generate_move_notation(piece, from_pos, to_pos):
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Convert column index to letter (a-h)
    col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
    from_square = f"{col_map[from_col]}{8 - from_row}"
    to_square = f"{col_map[to_col]}{8 - to_row}"

    # Return simple move notation
    return f"{from_square}{to_square}"

def print_move_to_console(stdscr, move_notation):
    stdscr.addstr(len(board) + 3, 0, f"Last move: {move_notation}                    ")  # Display the move with padding to clear previous text
    stdscr.refresh()

def decide_server_or_client(stdscr):
    global player_side, turn
    stdscr.addstr(0, 0, "Press 's' to start as server or 'c' to start as client.")
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key == ord('s'):
            player_side = 'white'
            turn = 'white'
            stdscr.addstr(1, 0, "Running as server. Waiting for client to connect...")
            stdscr.refresh()
            server_thread = threading.Thread(target=run_flask_server, daemon=True)
            server_thread.start()

            # Wait for client to connect
            stdscr.addstr(2, 0, "Waiting for a client to connect...")
            stdscr.refresh()
            while not client_connected.is_set():
                time.sleep(1)  # Check periodically for client connection

            stdscr.addstr(3, 0, "Client connected! Starting the game...")
            stdscr.refresh()
            return 'server'
        elif key == ord('c'):
            player_side = 'black'
            turn = 'white'
            stdscr.addstr(1, 0, "Running as client. Enter the server's IP address:")
            stdscr.refresh()

            curses.echo()
            stdscr.nodelay(0)  # Disable nodelay to allow blocking input
            stdscr.addstr(2, 0, "Server IP: ")
            server_address = stdscr.getstr(2, 11, 50).decode().strip()
            stdscr.nodelay(1)  # Re-enable nodelay
            curses.noecho()

            # Notify the server of the connection
            try:
                stdscr.addstr(3, 0, f"Connecting to server at {server_address}:5050...")
                stdscr.refresh()
                response = requests.post(f'http://{server_address}:5050/connect')
                if response.status_code == 200:
                    stdscr.addstr(4, 0, f"Connected to server at {server_address}:5050. You can start playing.")
                    stdscr.refresh()
                    return 'client', server_address
                else:
                    stdscr.addstr(4, 0, "Failed to connect to server. Try again.")
                    stdscr.refresh()
            except requests.RequestException:
                stdscr.addstr(4, 0, "Server connection failed. Try again.")
                stdscr.refresh()
    return 'client', server_address  # Ensure a return statement exists

app = Flask(__name__)

moves = []
client_connected = threading.Event()  # Flag to detect client connection


@app.route('/connect', methods=['POST'])
def connect_client():
    client_connected.set()  # Signal that a client is connected
    return jsonify({'status': 'connected'}), 200

@app.route('/move', methods=['POST'])
def receive_move():
    data = request.get_json()
    move = data.get('move')
    if move:
        moves.append(move)
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'fail'}), 400

@app.route('/moves', methods=['GET'])
def get_moves():
    return jsonify({'moves': moves}), 200


def run_flask_server():
    global client_connected
    host_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running on {host_ip}:5050")  # Display server info
    app.run(host=host_ip, port=5050)

def handle_received_moves(role, server_address=None):
    global last_move, turn
    if role == 'client' and server_address:
        try:
            response = requests.get(f'http://{server_address}:5050/moves')  # Fetch moves from the server
            if response.status_code == 200:
                data = response.json()
                if 'moves' in data and data['moves']:
                    latest_move = data['moves'][-1]
                    if latest_move != last_move:
                        last_move = latest_move
                        process_received_move(latest_move)  # Apply the move to the local board
                        turn = 'black' if turn == 'white' else 'white'
        except requests.RequestException:
            pass
    elif role == 'server':
        # Server does not need to fetch moves from itself
        pass

def process_received_move(move):
    parsed = parse_move_data(move)
    if parsed is None:
        print("Received invalid move data.")
        return

    from_pos, to_pos, promotion_piece = parsed

    if from_pos is None or to_pos is None:
        print("Received incomplete move data.")
        return

    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Update the board with the received move
    piece = board[from_row][from_col]
    board[to_row][to_col] = piece
    board[from_row][from_col] = ' '

    # Handle pawn promotion if applicable
    if promotion_piece:
        board[to_row][to_col] = promotion_piece if player_side == 'black' else promotion_piece.upper()

    # Update the last_move and turn
    global last_move, turn
    last_move = move
    turn = 'black' if turn == 'white' else 'white'
    
def send_move_to_server(move, server_address):
    try:
        data = {'move': move}
        requests.post(f'http://{server_address}:5050/move', json=data)
    except requests.RequestException:
        pass

def send_move_to_client(move):
    try:
        data = {'move': move}
        # Assuming only one client, send move to client via a specific endpoint
        # You need to implement an endpoint on the client to receive moves
        # This is a placeholder implementation
        client_ip = socket.gethostbyname(socket.gethostname())
        requests.post(f'http://{client_ip}:5051/move', json=data)
    except requests.RequestException:
        pass

curses.wrapper(main)
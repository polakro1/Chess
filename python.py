import curses
import time
import socket

#added generate chess notation function

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
# Game state variables
selection_mode = 'select_piece'  # Modes: 'select_piece', 'select_move', 'error'
selected_piece = None  # Tuple (row, col) of selected piece
last_move = ""  # Variable to keep track of the last move
in_check_white = False  # Tracks if white is in check
in_check_black = False  # Tracks if black is in check
en_passant_target = None  # Initialize en passant target

# Lists to track captured pieces
captured_white_pieces = []
captured_black_pieces = []

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

def handle_enter_key(stdscr, row, col):
    global selection_mode, selected_piece
    piece = board[row][col]
    if selection_mode == 'select_piece':
        if (player_side == 'white' and piece.isupper()) or (player_side == 'black' and piece.islower()):
            selection_mode = 'select_move'
            selected_piece = (row, col)
        else:
            flash_error(stdscr, row, col)
    elif selection_mode == 'select_move':
        if is_legal_move(selected_piece, (row, col)):
            move_piece(selected_piece, (row, col), stdscr)
            selection_mode = 'select_piece'
            selected_piece = None
        else:
            flash_error(stdscr, row, col)

def find_king(player_side):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if player_side == 'white' and piece == 'K':
                return (row, col)
            elif player_side == 'black' and piece == 'k':
                return (row, col)
    return None

def is_checkmate(player_side):
    if not is_in_check(player_side):
        return False
    # Iterate over all player's pieces
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if (player_side == 'white' and piece.isupper()) or (player_side == 'black' and piece.islower()):
                from_pos = (row, col)
                # Iterate through all possible to_pos
                for to_row in range(8):
                    for to_col in range(8):
                        to_pos = (to_row, to_col)
                        if is_legal_move(from_pos, to_pos, player_side):
                            return False  # Found at least one legal move
    return True  # No legal moves found and in check

def is_in_check(side):
    king_pos = find_king(side)
    if not king_pos:
        return False  # King not found; handle as needed

    opponent_side = 'black' if side == 'white' else 'white'
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if (opponent_side == 'white' and piece.isupper()) or \
               (opponent_side == 'black' and piece.islower()):
                if is_legal_move((row, col), king_pos, opponent_side):
                    return True
    return False

def is_legal_move(from_pos, to_pos, side=player_side):
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    piece = board[from_row][from_col]

    # Check if the target square is within bounds
    if not (0 <= to_row < 8 and 0 <= to_col < 8):
        return False

    # Basic checks for moving to an empty square or capturing opponent's piece
    target_piece = board[to_row][to_col]
    if target_piece != ' ':
        if (side == 'white' and target_piece.isupper()) or \
           (side == 'black' and target_piece.islower()):
            return False  # Cannot capture your own piece

    # Movement logic based on piece type
    if piece.lower() == 'p':  # Pawn movement
        direction = -1 if piece.isupper() else 1  # White moves up (-1), black moves down (+1)
        start_row = 6 if piece.isupper() else 1  # Starting row for pawns (6 for white, 1 for black)
        # Moving straight
        if from_col == to_col:
            if to_row == from_row + direction and board[to_row][to_col] == ' ':
                pass  # Move one step forward
            elif from_row == start_row and to_row == from_row + 2 * direction and \
                 board[to_row][to_col] == ' ' and board[from_row + direction][to_col] == ' ':
                pass  # Move two steps forward
            else:
                return False
        # Capturing
        elif abs(from_col - to_col) == 1 and to_row == from_row + direction:
            if board[to_row][to_col] == ' ':
                # En Passant capture condition
                if en_passant_target == (to_row, to_col):
                    pass  # En passant capture
                else:
                    return False  # No piece to capture
        else:
            return False  # Invalid pawn move
    elif piece.lower() == 'r':  # Rook movement
        if from_row == to_row or from_col == to_col:
            if not path_clear(from_pos, to_pos):
                return False
        else:
            return False
    elif piece.lower() == 'n':  # Knight movement
        if not ((abs(from_row - to_row) == 2 and abs(from_col - to_col) == 1) or \
                (abs(from_row - to_row) == 1 and abs(from_col - to_col) == 2)):
            return False
    elif piece.lower() == 'b':  # Bishop movement
        if abs(from_row - to_row) == abs(from_col - to_col):
            if not path_clear(from_pos, to_pos):
                return False
        else:
            return False
    elif piece.lower() == 'q':  # Queen movement
        if (from_row == to_row or from_col == to_col or \
            abs(from_row - to_row) == abs(from_col - to_col)):
            if not path_clear(from_pos, to_pos):
                return False
        else:
            return False
    elif piece.lower() == 'k':  # King movement
        if max(abs(from_row - to_row), abs(from_col - to_col)) > 1:
            return False

    # Simulate the move
    temp_piece = board[to_row][to_col]
    board[to_row][to_col] = board[from_row][from_col]
    board[from_row][from_col] = ' '

    # Check if the move leaves the king in check
    if is_in_check(side):
        # Undo the move
        board[from_row][from_col] = board[to_row][to_col]
        board[to_row][to_col] = temp_piece
        return False

    # Undo the move
    board[from_row][from_col] = board[to_row][to_col]
    board[to_row][to_col] = temp_piece

    return True

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
    global en_passant_target, last_move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    piece = board[from_row][from_col]

    # Capture the opponent's piece, if applicable
    captured_piece = board[to_row][to_col]
    if captured_piece != ' ':
        if captured_piece.isupper():
            captured_white_pieces.append(captured_piece)
        else:
            captured_black_pieces.append(captured_piece)

    # Determine if the move is an en passant capture
    is_en_passant = False
    if piece.lower() == 'p' and from_col != to_col and board[to_row][to_col] == ' ':
        # En passant capture condition
        if en_passant_target == (to_row, to_col):
            is_en_passant = True

    # Update the board
    board[to_row][to_col] = piece
    board[from_row][from_col] = ' '

    if is_en_passant:
        # Remove the captured pawn for en passant
        capture_row = to_row + (1 if piece.isupper() else -1)
        captured_piece = board[capture_row][to_col]
        board[capture_row][to_col] = ' '
        if captured_piece.isupper():
            captured_white_pieces.append(captured_piece)
        else:
            captured_black_pieces.append(captured_piece)

    # Generate standard chess notation
    move_notation = generate_move_notation(piece, from_pos, to_pos)

    # Print move to the console
    print_move_to_console(stdscr, move_notation)

    # Handle en passant target setting
    if piece.lower() == 'p' and abs(to_row - from_row) == 2:
        # Set en passant target
        en_passant_target = ((from_row + to_row) // 2, from_col)
    else:
        en_passant_target = None

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
    # Display captured pieces
    display_captured_pieces(stdscr)
    # Display check statuses
    stdscr.addstr(len(board) + 4, 0, f"White Status: {'In Check!' if in_check_white else 'Safe'}", curses.color_pair(6 if in_check_white else 3))
    stdscr.addstr(len(board) + 5, 0, f"Black Status: {'In Check!' if in_check_black else 'Safe'}", curses.color_pair(6 if in_check_black else 3))

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

def handle_enter_key(stdscr, row, col):
    global selection_mode, selected_piece
    piece = board[row][col]
    if selection_mode == 'select_piece':
        if (player_side == 'white' and piece.isupper()) or (player_side == 'black' and piece.islower()):
            selection_mode = 'select_move'
            selected_piece = (row, col)
        else:
            flash_error(stdscr, row, col)
    elif selection_mode == 'select_move':
        if is_legal_move(selected_piece, (row, col)):
            move_notation = generate_move_notation(board[selected_piece[0]][selected_piece[1]], selected_piece, (row, col))
            # Check for pawn promotion
            if board[selected_piece[0]][selected_piece[1]].lower() == 'p':
                if (player_side == 'white' and row == 0) or (player_side == 'black' and row == 7):
                    promotion_piece = prompt_promotion(stdscr, player_side)
                    if promotion_piece:
                        move_notation += promotion_piece.upper()
            move_piece(selected_piece, (row, col), stdscr)
            selection_mode = 'select_piece'
            selected_piece = None
            return move_notation  # Return the move notation
        else:
            flash_error(stdscr, row, col)
    return None

def handle_surrender(stdscr, conn):
    # Ask for confirmation to surrender
    confirmation = prompt_user(stdscr, "Are you sure you want to surrender? (y/n): ")
    if confirmation.lower() != 'y':
        return  # Cancel surrender

    # Ask if the user changed their mind
    changed_mind = prompt_user(stdscr, "Did you change your mind? (y/n): ")
    if changed_mind.lower() == 'y':
        return  # Cancel surrender

    # Proceed to surrender
    # Send the surrender message to the opponent
    conn.sendall('surrender'.encode('utf-8'))
    
    # Update the board to show surrender
    global last_move
    last_move = "You surrendered."
    update_board(stdscr, -1, -1, last_move)  # -1, -1 to indicate no selection
    
    # Inform the player and exit
    stdscr.addstr(len(board) + 5, 0, "You have surrendered. Game over.", curses.color_pair(6))
    stdscr.refresh()
    time.sleep(2)
    conn.close()
    exit()

def handle_escape_key(selection_mode, selected_piece):
    if selection_mode == 'select_move':
        selection_mode = 'select_piece'
        selected_piece = None
    return selection_mode, selected_piece

def setup_network():
    def get_local_ip():
        try:
            # Use a dummy connection to retrieve the local network IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"Unable to determine local IP: {e}")
            return "127.0.0.1"  # Fallback to localhost

    mode = input("Enter 'server' to host or 'client' to connect: ").strip().lower()
    port_server = 5050
    buffer_size = 1024

    if mode == 'server':
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", port_server))
        server_socket.listen(1)

        # Get and display server's local IP address
        local_ip = get_local_ip()
        print(f"Server IP address: {local_ip}")
        print(f"Server listening on port {port_server}...")
        
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")
        player_side = 'white'  # Server plays white
    elif mode == 'client':
        server_ip = input("Enter the server's IP address: ").strip()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((server_ip, port_server))
        except socket.error as e:
            print(f"Failed to connect to {server_ip}:{port_server} - {e}")
            exit()
        print(f"Connected to server at {server_ip}:{port_server}")
        player_side = 'black'  # Client plays black
    else:
        print("Invalid mode.")
        exit()
    return conn, player_side

# Updated board rendering with three-character-wide tiles
def main(stdscr, conn, player_side):
    initialize_colors()
    curses.curs_set(0)   # Hide the cursor
    stdscr.nodelay(1)    # Non-blocking input
    stdscr.timeout(100)  # Refresh rate for blinking effect

    global selection_mode, selected_piece, last_move, in_check_white, in_check_black, en_passant_target
    row, col = 0, 0  # Initial selection position
    turn = 'white'  # White starts first

    while True:
        update_board(stdscr, row, col, last_move)  # Always update the board

        if turn != player_side:
            # Wait for opponent's move
            try:
                move_data = conn.recv(1024).decode('utf-8')
                if not move_data:
                    print("Connection closed.")
                    conn.close()
                    break
                if move_data == 'surrender':
                    last_move = "Opponent has surrendered. You win!"
                    update_board(stdscr, -1, -1, last_move)
                    stdscr.addstr(len(board) + 5, 0, "Opponent has surrendered. You win!", curses.color_pair(5))
                    stdscr.refresh()
                    time.sleep(2)
                    conn.close()
                    break
                from_pos, to_pos, promotion_piece = parse_move_data(move_data)
                move_piece(from_pos, to_pos, stdscr)
                if promotion_piece:
                    board[to_pos[0]][to_pos[1]] = promotion_piece if player_side == 'white' else promotion_piece.lower()
                last_move = generate_move_notation(board[from_pos[0]][from_pos[1]], from_pos, to_pos)
                turn = player_side  # Your turn now

                # After receiving and applying the move, update check statuses
                in_check_white = is_in_check('white')
                in_check_black = is_in_check('black')

                # Check if you are in check or checkmate
                if player_side == 'white':
                    if in_check_white:
                        if is_checkmate('white'):
                            last_move += " (Checkmate!)"
                            update_board(stdscr, row, col, last_move)
                            stdscr.addstr(len(board) + 5, 0, "Checkmate! You lose!", curses.color_pair(5))
                            stdscr.refresh()
                            time.sleep(2)
                            conn.close()
                            break
                        else:
                            last_move += " (Check!)"
                else:
                    if in_check_black:
                        if is_checkmate('black'):
                            last_move += " (Checkmate!)"
                            update_board(stdscr, row, col, last_move)
                            stdscr.addstr(len(board) + 5, 0, "Checkmate! You lose!", curses.color_pair(5))
                            stdscr.refresh()
                            time.sleep(2)
                            conn.close()
                            break
                        else:
                            last_move += " (Check!)"

            except socket.error:
                pass  # Handle socket errors if necessary
        else:
            key = stdscr.getch()

            # Handle key inputs for selection and movement
            if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                row, col = handle_movement_keys(key, row, col)
            elif key in [ord('\n'), curses.KEY_ENTER]:
                move_notation = handle_enter_key(stdscr, row, col)
                if move_notation:
                    update_board(stdscr, row, col, move_notation)  # Show the move on the board
                    conn.sendall(move_notation.encode('utf-8'))
                    last_move = move_notation
                    turn = 'black' if player_side == 'white' else 'white'  # Switch turn

                    # After making the move, update check statuses
                    in_check_white = is_in_check('white')
                    in_check_black = is_in_check('black')

                    # Check if the opponent is in check or checkmate
                    if player_side == 'white':
                        if in_check_black:
                            if is_checkmate('black'):
                                last_move += " (Checkmate!)"
                                update_board(stdscr, row, col, last_move)
                                stdscr.addstr(len(board) + 5, 0, "Checkmate! You win!", curses.color_pair(5))
                                stdscr.refresh()
                                time.sleep(2)
                                conn.close()
                                break
                            else:
                                last_move += " (Check!)"
                    else:
                        if in_check_white:
                            if is_checkmate('white'):
                                last_move += " (Checkmate!)"
                                update_board(stdscr, row, col, last_move)
                                stdscr.addstr(len(board) + 5, 0, "Checkmate! You win!", curses.color_pair(5))
                                stdscr.refresh()
                                time.sleep(2)
                                conn.close()
                                break
                            else:
                                last_move += " (Check!)"

            elif key == ord('s'):
                handle_surrender(stdscr, conn)
            elif key == 27:  # Escape key
                selection_mode, selected_piece = handle_escape_key(selection_mode, selected_piece)
            elif key == ord('q'):
                conn.close()
                break

def parse_move_data(move_data):
    col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    
    # Check if the move includes promotion (e.g., e7e8Q)
    if len(move_data) == 5:
        promotion_piece = move_data[4].upper()
        to_promotion = True
    else:
        promotion_piece = ''
        to_promotion = False

    from_col = col_map[move_data[0]]
    from_row = 8 - int(move_data[1])
    to_col = col_map[move_data[2]]
    to_row = 8 - int(move_data[3])

    # Reset en passant target unless the last move was a two-square pawn move
    piece_moved = board[to_row][to_col]
    if not (piece_moved.lower() == 'p' and abs(to_row - from_row) == 2):
        en_passant_target = None

    return (from_row, from_col), (to_row, to_col), promotion_piece if to_promotion else None

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

def prompt_user(stdscr, prompt_text):
    stdscr.addstr(len(board) + 4, 0, prompt_text)
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in [ord('y'), ord('Y'), ord('n'), ord('N')]:
            # Clear the prompt after receiving input
            stdscr.addstr(len(board) + 4, 0, " " * (len(prompt_text) + 10))
            stdscr.refresh()
            return chr(key)
        
def display_captured_pieces(stdscr):
    # Convert captured pieces to their Unicode symbols
    captured_white = ' '.join([pieces[p] for p in captured_white_pieces])
    captured_black = ' '.join([pieces[p] for p in captured_black_pieces])
    
    # Display captured pieces
    stdscr.addstr(len(board) + 4, 0, f"Captured White Pieces: {captured_white}")
    stdscr.addstr(len(board) + 5, 0, f"Captured Black Pieces: {captured_black}")

conn, player_side = setup_network()
curses.wrapper(main, conn, player_side)
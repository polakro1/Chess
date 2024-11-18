import curses
import time

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
selection_mode = 'select_piece'  # Modes: 'select_piece', 'select_move', 'error'
selected_piece = None  # Tuple (row, col) of selected piece

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

    # Generate standard chess notation
    move_notation = generate_move_notation(piece, from_pos, to_pos)
    
    # Print move to the console
    print_move_to_console(stdscr, move_notation)

def flash_error(stdscr, row, col):
    global selection_mode
    selection_mode = 'error'

    # Display the yellow error blink for a short duration
    for _ in range(3):  # Loop for a short duration to create the blink effect
        display_board(stdscr, row, col)
        stdscr.refresh()
        curses.napms(100)  # Pause for 100 milliseconds

    # Reset to the previous mode
    selection_mode = 'select_piece' if selected_piece is None else 'select_move'

def display_board(stdscr, sel_row, sel_col):
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

    stdscr.refresh()
    
# Updated board rendering with three-character-wide tiles
def main(stdscr):
    initialize_colors()
    curses.curs_set(0)   # Hide the cursor
    stdscr.nodelay(1)    # Non-blocking input
    stdscr.timeout(100)  # Refresh rate for blinking effect

    global selection_mode, selected_piece
    row, col = 0, 0  # Initial selection position
    last_move = ""  # Variable to keep track of the last move

    while True:
        display_board(stdscr, row, col)  # Draw the board

        # Print the last move below the board
        stdscr.addstr(len(board) + 3, 0, f"Last move: {last_move}")  # Display the move text
        stdscr.refresh()

        key = stdscr.getch()

        # Handle key inputs for selection and movement
        if key == curses.KEY_UP:
            row = (row - 1) % 8
        elif key == curses.KEY_DOWN:
            row = (row + 1) % 8
        elif key == curses.KEY_LEFT:
            col = (col - 1) % 8
        elif key == curses.KEY_RIGHT:
            col = (col + 1) % 8
        elif key == ord('\n') or key == curses.KEY_ENTER:
            if selection_mode == 'select_piece':
                # Logic to select a piece
                piece = board[row][col]
                if (player_side == 'white' and piece.isupper()) or (player_side == 'black' and piece.islower()):
                    selection_mode = 'select_move'
                    selected_piece = (row, col)
                else:
                    flash_error(stdscr, row, col)  # Invalid selection
            elif selection_mode == 'select_move':
                if is_legal_move(selected_piece, (row, col)):
                    move_notation = generate_move_notation(board[selected_piece[0]][selected_piece[1]], selected_piece, (row, col))
                    last_move = move_notation  # Update the last move
                    move_piece(selected_piece, (row, col), stdscr)  # Make the move
                    selection_mode = 'select_piece'
                    selected_piece = None
                else:
                    flash_error(stdscr, row, col)  # Invalid move
        elif key == 27:  # Escape key
            if selection_mode == 'select_move':
                selection_mode = 'select_piece'
                selected_piece = None

def generate_move_notation(piece, from_pos, to_pos):
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Convert column index to letter (a-h)
    col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
    from_square = f"{col_map[from_col]}{8 - from_row}"
    to_square = f"{col_map[to_col]}{8 - to_row}"

    # Generate move notation
    if piece.lower() == 'p':  # Pawn move
        if from_col != to_col and board[to_row][to_col] != ' ':  # Capture
            return f"{col_map[from_col]}x{to_square}"
        return to_square  # Regular move
    else:
        notation_piece = piece.upper() if piece.islower() else piece
        capture_indicator = 'x' if board[to_row][to_col] != ' ' else ''
        return f"{notation_piece}{capture_indicator}{to_square}"

def print_move_to_console(stdscr, move_notation):
    stdscr.addstr(len(board) + 3, 0, f"Last move: {move_notation}                    ")  # Display the move with padding to clear previous text
    stdscr.refresh()

curses.wrapper(main)
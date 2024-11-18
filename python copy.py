import curses
import time

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

# Updated board rendering with three-character-wide tiles
def main(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(100) # Refresh rate for blinking effect

    # Initialize color pairs
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)     # Red tile
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Black tile
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_BLUE)    # Blue for blinking selection
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)  # Brown for board outline

    # Initial selection position
    row, col = 0, 0

    # Function to render the board with selection
    def display_board():
        stdscr.clear()

        # Top border
        for x in range(26):  # Each tile now takes up 3 characters
            stdscr.addstr(0, x, "▀", curses.color_pair(4))

        # Display board with left and right borders, each tile is 3 characters wide
        for i, board_row in enumerate(board):
            # Left border for each row
            stdscr.addstr(i + 1, 0, " ", curses.color_pair(4))
            
            for j, piece in enumerate(board_row):
                tile_color = curses.color_pair(1) if (i + j) % 2 == 0 else curses.color_pair(2)
                piece_char = pieces[piece]
                # Blink blue if the tile is selected
                if i == row and j == col:
                    tile_color = curses.color_pair(3) if int(time.time() * 2) % 2 == 0 else tile_color
                # Draw each tile with a three-character width
                stdscr.addstr(i + 1, 1 + j * 3, f" {piece_char} ", tile_color)
            
            # Right border for each row
            stdscr.addstr(i + 1, 1 + 8 * 3, " ", curses.color_pair(4))

        # Bottom border
        for x in range(26):
            stdscr.addstr(len(board) + 1, x, "▄", curses.color_pair(4))

        stdscr.refresh()

    # Main loop to capture keyboard input and update selection
    while True:
        display_board()
        key = stdscr.getch()

        # Arrow key controls for selection
        if key == curses.KEY_UP:
            row = (row - 1) % 8
        elif key == curses.KEY_DOWN:
            row = (row + 1) % 8
        elif key == curses.KEY_LEFT:
            col = (col - 1) % 8
        elif key == curses.KEY_RIGHT:
            col = (col + 1) % 8
        elif key == ord('q'):  # Quit on 'q' key
            break

curses.wrapper(main)
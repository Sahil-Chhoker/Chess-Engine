import streamlit as st
from PIL import Image
import os
from main import Board

base_path = os.path.dirname(__file__)


def load_chess_assets(base_path: str):
    """
    Load chess board and piece images with alpha channel enabled.

    Args:
        base_path (str): The root directory where assets are stored.

    Returns:
        tuple: (board_image, pieces_dict)
            - board_image: PIL.Image of the chess board
            - pieces_dict: dict mapping piece symbols to PIL.Images
    """
    board_path = os.path.join(base_path, "assets", "board.png")
    board = Image.open(board_path).convert("RGBA")

    piece_files = {
        "p": "black-pawn.png",
        "r": "black-rook.png",
        "n": "black-knight.png",
        "b": "black-bishop.png",
        "q": "black-queen.png",
        "k": "black-king.png",
        "P": "white-pawn.png",
        "R": "white-rook.png",
        "N": "white-knight.png",
        "B": "white-bishop.png",
        "Q": "white-queen.png",
        "K": "white-king.png",
    }

    pieces = {}
    for key, filename in piece_files.items():
        path = os.path.join(base_path, "assets", "pieces-png", filename)
        pieces[key] = Image.open(path).convert("RGBA").resize((90, 90))

    return board, pieces


def create_board_image(board: Board):
    board_img, pieces_img = load_chess_assets(base_path)
    board_copy = board_img.copy()
    x_padding, y_padding = 10, 12  # For boundries
    x_offset, y_offset = 96, 96  # For each square

    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece != " ":
                x = j * x_offset + x_padding
                y = i * y_offset + y_padding
                board_copy.paste(pieces_img[piece], (x, y), pieces_img[piece])
    return board_copy


st.write("""# Chess Engine""")

board = (
    ("r", "n", "b", "q", "k", "b", "n", "r"),  # 8
    ("p", "p", "p", "p", "p", "p", "p", "p"),  # 7
    (" ", " ", " ", " ", " ", " ", " ", " "),  # 6
    (" ", " ", " ", " ", " ", " ", " ", " "),  # 5
    (" ", " ", " ", " ", " ", " ", " ", " "),  # 4
    (" ", " ", " ", " ", " ", " ", "P", " "),  # 3
    ("P", "P", "P", "P", "P", "P", " ", "P"),  # 2
    ("R", "N", "B", "Q", "K", "B", "N", "R"),  # 1
    # a    b    c    d    e    f    g    h
)


def hide_buttons():
    st.markdown(
        """
        <style>
        .stButton > button {
            visibility: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.title("Clickable Button Grid")


def create_clickable_grid(rows, cols):
    st.title("Clickable Grid Example")
    clicked_cell = None

    for r in range(rows):
        # Create a row of columns
        row_cols = st.columns(cols)
        for c in range(cols):
            with row_cols[c]:
                # Create a button for each cell
                button_label = f"Cell ({r},{c})"
                # Use a unique key for each button
                if st.button(button_label, width=400, type="tertiary"):
                    clicked_cell = (r, c)

    if clicked_cell:
        st.write(f"You clicked on: Cell ({clicked_cell[0]},{clicked_cell[1]})")


# Create a 3x3 clickable grid
create_clickable_grid(8, 8)

st.image(create_board_image(board))

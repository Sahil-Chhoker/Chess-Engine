import streamlit as st
from PIL import Image, ImageDraw
import os
from main import ChessEngine  # Assumes your engine is in engine.py
from streamlit_image_coordinates import streamlit_image_coordinates


# --- Asset Loading (can be cached for performance) ---
@st.cache_data
def load_chess_assets(base_path: str):
    """Loads and resizes chess assets."""
    board_path = os.path.join(base_path, "assets", "board.png")
    board_img = Image.open(board_path).convert("RGBA")

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
    pieces_img = {}
    for key, filename in piece_files.items():
        path = os.path.join(base_path, "assets", "pieces-png", filename)
        pieces_img[key] = Image.open(path).convert("RGBA").resize((90, 90))
    return board_img, pieces_img


# --- Image Generation with Highlights ---
def create_board_image(board_state, selected_square=None, legal_moves=None):
    base_path = os.path.dirname(__file__)
    board_img, pieces_img = load_chess_assets(base_path)
    highlight_layer = Image.new("RGBA", board_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(highlight_layer)
    x_padding, y_padding, square_size = 10, 12, 96

    if legal_moves:
        for move in legal_moves:
            end_row, end_col = engine._from_algebraic(move[2:4])
            x0, y0 = (
                end_col * square_size + x_padding,
                end_row * square_size + y_padding,
            )
            draw.rectangle([x0, y0, x0 + 90, y0 + 90], fill=(255, 255, 0, 80))

    if selected_square:
        row, col = engine._from_algebraic(selected_square)
        x0, y0 = col * square_size + x_padding, row * square_size + y_padding
        draw.rectangle([x0, y0, x0 + 90, y0 + 90], fill=(0, 128, 255, 100))

    board_with_highlights = Image.alpha_composite(board_img, highlight_layer)
    for i in range(8):
        for j in range(8):
            piece = board_state[i][j]
            if piece != " ":
                x, y = j * square_size + x_padding, i * square_size + y_padding
                board_with_highlights.paste(
                    pieces_img[piece], (x, y), pieces_img[piece]
                )
    return board_with_highlights


# --- Coordinate Conversion ---
def pixel_to_algebraic(x, y):
    x_padding, y_padding, square_size = 10, 12, 96
    if x < x_padding or y < y_padding:
        return None
    col = (x - x_padding) // square_size
    row = (y - y_padding) // square_size
    if 0 <= row < 8 and 0 <= col < 8:
        return engine._to_algebraic(row, col)
    return None


# --- Streamlit App ---
st.set_page_config(page_title="Chess", layout="wide")
st.title("Chess Engine with Image Board")

# Initialize state
if "engine" not in st.session_state:
    st.session_state.engine = ChessEngine()
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None
if "legal_moves" not in st.session_state:
    st.session_state.legal_moves = []
# This state variable helps prevent reprocessing the same click
if "last_click" not in st.session_state:
    st.session_state.last_click = None

engine = st.session_state.engine
col1, col2 = st.columns([2, 1])

with col1:
    board_image = create_board_image(
        engine.current_state.board,
        st.session_state.selected_square,
        st.session_state.legal_moves,
    )
    # The component call now simply returns the value
    value = streamlit_image_coordinates(board_image, key="board_click")

    # The processing logic now happens *after* the component is called
    if value and value != st.session_state.last_click:
        st.session_state.last_click = value  # Record the click
        clicked_square = pixel_to_algebraic(value["x"], value["y"])

        if clicked_square:
            selected = st.session_state.selected_square
            turn = engine.current_state.turn
            piece_on_square = engine._get_piece_at_algebraic(clicked_square)
            is_piece_of_current_turn = (
                piece_on_square.isupper() if turn == "w" else piece_on_square.islower()
            )

            if not selected:
                if piece_on_square != " " and is_piece_of_current_turn:
                    st.session_state.selected_square = clicked_square
                    all_legal_moves = engine.get_all_legal_moves(engine.current_state)
                    st.session_state.legal_moves = [
                        m for m in all_legal_moves if m.startswith(clicked_square)
                    ]
            else:
                move = selected + clicked_square
                if (
                    piece_on_square != " "
                    and is_piece_of_current_turn
                    and selected != clicked_square
                ):
                    st.session_state.selected_square = clicked_square
                    all_legal_moves = engine.get_all_legal_moves(engine.current_state)
                    st.session_state.legal_moves = [
                        m for m in all_legal_moves if m.startswith(clicked_square)
                    ]
                elif move in st.session_state.legal_moves:
                    engine.make_move(move)
                    st.session_state.selected_square = None
                    st.session_state.legal_moves = []
                elif f"{move}q" in st.session_state.legal_moves:
                    engine.make_move(f"{move}q")
                    st.session_state.selected_square = None
                    st.session_state.legal_moves = []
                else:
                    st.session_state.selected_square = None
                    st.session_state.legal_moves = []

            # This is the crucial part: force a rerun after processing the click
            st.rerun()

# --- Game Info and Controls ---
with col2:
    turn_color = "White" if engine.current_state.turn == "w" else "Black"
    st.header("Game Info")
    st.write(f"**Turn:** {turn_color}")

    if engine.is_checkmate(engine.current_state):
        st.success(
            f"**Checkmate!** {'Black' if engine.current_state.turn == 'w' else 'White'} wins."
        )
    elif engine.is_stalemate(engine.current_state):
        st.warning("**Stalemate!**")

    st.subheader("Controls")
    if st.button("New Game", use_container_width=True):
        # Clear all relevant session state variables
        for key in ["engine", "selected_square", "legal_moves", "last_click"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    if st.button("Undo Move", use_container_width=True):
        engine.undo_move()
        st.session_state.selected_square = None
        st.session_state.legal_moves = []
        st.session_state.last_click = None  # Reset last click on undo
        st.rerun()

    st.subheader("Move History")
    move_history = engine.get_move_history()
    history_str = ""
    for i in range(0, len(move_history), 2):
        white_move = move_history[i]
        black_move = move_history[i + 1] if i + 1 < len(move_history) else ""
        history_str += f"{i // 2 + 1}. {white_move} {black_move}\n"
    st.text_area("", value=history_str, height=400, disabled=True)

# app.py - Flask backend
from flask import Flask, render_template, jsonify, request
from main import ChessEngine
import json

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

# Global game instance (in production, use sessions or database)
game_engine = ChessEngine()


@app.route("/")
def index():
    return render_template("chess.html")


@app.route("/api/board_state")
def get_board_state():
    """Get current board state and game info"""
    state = game_engine.current_state
    return jsonify(
        {
            "board": state.board,
            "turn": state.turn,
            "is_checkmate": game_engine.is_checkmate(state),
            "is_stalemate": game_engine.is_stalemate(state),
            "move_history": game_engine.get_move_history(),
        }
    )


@app.route("/api/legal_moves")
def get_legal_moves():
    """Get legal moves for a piece at given square"""
    square = request.args.get("square")
    if not square:
        return jsonify({"moves": []})

    all_moves = game_engine.get_all_legal_moves(game_engine.current_state)
    piece_moves = [move for move in all_moves if move.startswith(square)]
    return jsonify({"moves": piece_moves})


@app.route("/api/make_move", methods=["POST"])
def make_move():
    """Make a move and return updated game state"""
    data = request.get_json()
    move = data.get("move")

    try:
        # Check if it's a promotion move
        all_moves = game_engine.get_all_legal_moves(game_engine.current_state)
        if move in all_moves:
            game_engine.make_move(move)
        elif f"{move}q" in all_moves:  # Auto-promote to queen
            game_engine.make_move(f"{move}q")
        else:
            return jsonify({"success": False, "error": "Invalid move"})

        state = game_engine.current_state
        return jsonify(
            {
                "success": True,
                "board": state.board,
                "turn": state.turn,
                "is_checkmate": game_engine.is_checkmate(state),
                "is_stalemate": game_engine.is_stalemate(state),
                "move_history": game_engine.get_move_history(),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/undo_move", methods=["POST"])
def undo_move():
    """Undo the last move"""
    try:
        game_engine.undo_move()
        state = game_engine.current_state
        return jsonify(
            {
                "success": True,
                "board": state.board,
                "turn": state.turn,
                "is_checkmate": game_engine.is_checkmate(state),
                "is_stalemate": game_engine.is_stalemate(state),
                "move_history": game_engine.get_move_history(),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/new_game", methods=["POST"])
def new_game():
    """Start a new game"""
    global game_engine
    game_engine = ChessEngine()
    state = game_engine.current_state
    return jsonify(
        {
            "success": True,
            "board": state.board,
            "turn": state.turn,
            "is_checkmate": False,
            "is_stalemate": False,
            "move_history": [],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)

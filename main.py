from dataclasses import dataclass

@dataclass(frozen=True)
class GameState:
    board: tuple[tuple[str, ...], ...]
    turn: str
    casteling_right: str
    en_passant_target: str | None
    halfmove_clock: int
    fullmove_number: int

class ChessEngine:
    def __init__(self):
        self.current_state = self._get_initial_state()
        self.history = [self.current_state]

        self.move_calculators = {
            'r': self.get_rook_moves,
            'n': self.get_knight_moves,
            # TODO: Add entries for 'p', 'b', 'q', 'k'
        }

    def _get_initial_state(self) -> GameState:
        board = (
            ('r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'), # 8
            ('p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'), # 7
            (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '), # 6
            (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '), # 5
            (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '), # 4
            (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '), # 3
            ('P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'), # 2
            ('R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R')  # 1
            # a    b    c    d    e    f    g    h
        )
        return GameState(
            board=board, 
            turn='w', 
            casteling_right='KQkq', # KQ tracks for white and kq tracks for black
            en_passant_target=None, 
            halfmove_clock=0, 
            fullmove_number=1, 
        )

    def make_move(self, move: str):
        ...

    def get_all_legal_moves(self, state: GameState) -> list[str]:
        all_moves = []
        is_white_turn = state.turn == 'w'

        for r in range(8):
            for c in range(8):
                piece = state.board[r][c]
                if piece == ' ':
                    continue
                is_white_piece = piece.isupper()

                if is_white_turn == is_white_piece:
                    piece_type = piece.lower()
                    if piece_type in self.move_calculators:
                        pseudo_moves = self.move_calculators[piece_type](state.board, r, c)
                        # TODO: Add check validation here
                        for move in pseudo_moves:
                            all_moves.append(move)
        return all_moves
    
    def get_rook_moves(self, board, r, c):
        moves = []
        start_square_notation = self._to_algebraic(r, c)
        
        rook_char = board[r][c]
        is_white_rook = rook_char.isupper()

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] # Up, Down, Left, Right

        for dr, dc in directions:
            row, col = r, c
            while True:
                row += dr
                col += dc

                if not (0 <= row < 8 and 0 <= col < 8):
                    break

                target_piece = board[row][col]
                target_square_notation = self._to_algebraic(row, col)
                move_notation = start_square_notation + target_square_notation

                if target_piece == ' ':
                    moves.append(move_notation)
                else:
                    is_white_target = target_piece.isupper()
                    if is_white_rook != is_white_target:
                        moves.append(move_notation)
                    break
        
        return moves

    def get_knight_moves(self, board, r, c):
        return []

    def _create_new_state_from_move(self, current_state: GameState, move: str) -> GameState:
        ...
    
    def _to_algebraic(self, row, col) -> str:
        """Helper to convert (row, col) to algebraic notation like 'a1'."""
        file = chr(ord('a') + col)
        rank = str(8 - row)
        return file + rank
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
        """Generate all legal moves for the current game state."""
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
        """Generate all possible rook moves from position (r, c)."""
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
        """Generate all possible knight moves from position (r, c)."""
        moves = []
        start_square_notation = self._to_algebraic(r, c)

        knight_char = board[r][c]
        is_white_knight = knight_char.isupper()

        # All 8 possible knight jumps
        directions = [
            (-2, -1), (-2, 1),
            (-1, -2), (-1, 2),
            (1, -2),  (1, 2),
            (2, -1),  (2, 1),
        ]

        for dr, dc in directions:
            row, col = r + dr, c + dc

            # Stay inside the board
            if not (0 <= row < 8 and 0 <= col < 8):
                continue

            target_piece = board[row][col]
            target_square_notation = self._to_algebraic(row, col)
            move_notation = start_square_notation + target_square_notation

            if target_piece == ' ':
                moves.append(move_notation)  # empty square
            else:
                is_white_target = target_piece.isupper()
                if is_white_knight != is_white_target:
                    moves.append(move_notation)  # capture enemy

        return moves

    def get_bishop_moves(self, board, r, c):
        """Generate all possible bishop moves from position (r, c)."""
        moves = []
        start_square_notation = self._to_algebraic(r, c)
        
        bishop_char = board[r][c]
        is_white_bishop = bishop_char.isupper()

        directions = [(-1, -1), (-1, 1), (1, 1), (1, -1)] # Up-left, Up-right, Down-right, Down-left

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
                    if is_white_bishop != is_white_target:
                        moves.append(move_notation)
                    break
        
        return moves

    def get_queen_moves(self, board, r, c):
        """Generate all possible queen moves from position (r, c)."""
        moves = self.get_rook_moves(board, r, c) + self.get_bishop_moves(board, r, c)
        return moves

    def get_king_moves(self, board, r, c):
        """Generate all possible king moves from position (r, c)."""
        moves = []
        start_square_notation = self._to_algebraic(r, c)
        
        king_char = board[r][c]
        is_white_king = king_char.isupper()

        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1)
        ]
        for dr, dc in directions:
            row, col = r, c
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
                if is_white_king != is_white_target:
                    moves.append(move_notation)
        return moves

    def get_pawn_moves(self, board, r, c):
        moves = []
        start_square_notation = self._to_algebraic(r, c)

        pawn_char = board[r][c]
        is_white_pawn = pawn_char.isupper()

        rank = int(start_square_notation[1])

        # Forward movement
        direction = -1 if is_white_pawn else 1
        one_step_row, one_step_col = r + direction, c
        if 0 <= one_step_row < 8 and board[one_step_row][one_step_col] == ' ':
            move_notation = start_square_notation + self._to_algebraic(one_step_row, one_step_col)
            moves.append(move_notation)

            # Two-step move from starting rank
            start_rank = 2 if is_white_pawn else 7
            if rank == start_rank:
                two_step_row = r + 2 * direction
                if 0 <= two_step_row < 8 and board[two_step_row][c] == ' ':
                    move_notation = start_square_notation + self._to_algebraic(two_step_row, c)
                    moves.append(move_notation)

        # Attacks
        attack_directions = [(direction, -1), (direction, 1)]
        for dr, dc in attack_directions:
            row, col = r + dr, c + dc
            if not (0 <= row < 8 and 0 <= col < 8):
                continue
            target_piece = board[row][col]
            if target_piece != ' ':
                is_white_target = target_piece.isupper()
                if is_white_pawn != is_white_target:
                    move_notation = start_square_notation + self._to_algebraic(row, col)
                    moves.append(move_notation)

        return moves

    def _create_new_state_from_move(self, current_state: GameState, move: str) -> GameState:
        ...
    
    def _to_algebraic(self, row, col) -> str:
        """Helper to convert (row, col) to algebraic notation like 'a1'."""
        file = chr(ord('a') + col)
        rank = str(8 - row)
        return file + rank
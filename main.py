from dataclasses import dataclass

@dataclass(frozen=True)
class GameState:
    board: tuple[tuple[str, ...], ...]
    turn: str
    castling_rights: str
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
            'b': self.get_bishop_moves,
            'q': self.get_queen_moves,
            'k': self.get_king_moves,
            'p': self.get_pawn_moves
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
            castling_rights='KQkq', # KQ tracks for white and kq tracks for black
            en_passant_target=None, 
            halfmove_clock=0, 
            fullmove_number=1, 
        )

    def make_move(self, move: str):
        legal_moves = self.get_all_legal_moves(self.current_state)

        if move not in legal_moves:
            raise ValueError(f"Move {move} is not legal.")

        # If the move is legal, generate the next state
        new_state = self._create_new_state_from_move(self.current_state, move)

        # Update the engine's state
        self.current_state = new_state
        self.history.append(new_state)
        print(f"Successfully made move: {move}")

    def _create_new_state_from_move(self, current_state: GameState, move: str) -> GameState:
        """
        The core logic for generating the next GameState.
        """
        start_pos, end_pos = move[:2], move[2:]
        start_row, start_col = self._from_algebraic(start_pos)
        
        # Get the new board layout
        new_board = self._get_next_board_state(current_state.board, move)
        
        new_turn = 'b' if current_state.turn == 'w' else 'w'
        
        piece = current_state.board[start_row][start_col]
        new_castling_rights = current_state.castling_rights

        if piece == 'K':
            new_castling_rights = new_castling_rights.replace('K', '').replace('Q', '')
        elif piece == 'k':
            new_castling_rights = new_castling_rights.replace('k', '').replace('q', '')
        elif piece == 'R' and start_pos == 'h1':
            new_castling_rights = new_castling_rights.replace('K', '')
        elif piece == 'R' and start_pos == 'a1':
            new_castling_rights = new_castling_rights.replace('Q', '')
        elif piece == 'r' and start_pos == 'h8':
            new_castling_rights = new_castling_rights.replace('k', '')
        elif piece == 'r' and start_pos == 'a8':
            new_castling_rights = new_castling_rights.replace('q', '')

        new_en_passant = None
        piece = current_state.board[start_row][start_col]
        end_row, end_col = self._from_algebraic(end_pos)

        if piece.lower() == 'p' and abs(start_row - end_row) == 2:
            # It was a two-square pawn move, so the en passant target is the square it skipped
            skipped_row = (start_row + end_row) // 2
            new_en_passant = self._to_algebraic(skipped_row, start_col)

        piece = current_state.board[start_row][start_col]
        end_row, end_col = self._from_algebraic(end_pos)
        is_capture = current_state.board[end_row][end_col] != ' '

        new_halfmove_clock = current_state.halfmove_clock + 1
        if piece.lower() == 'p' or is_capture:
            new_halfmove_clock = 0

        new_fullmove_number = current_state.fullmove_number
        if current_state.turn == 'b':
            new_fullmove_number += 1

        return GameState(
            board=new_board,
            turn=new_turn,
            castling_rights=new_castling_rights,
            en_passant_target=new_en_passant,
            halfmove_clock=new_halfmove_clock,
            fullmove_number=new_fullmove_number
        )

    def get_all_legal_moves(self, state: GameState) -> list[str]:
        """Generate all legal moves for the current game state."""
        legal_moves = []
        is_white_turn = state.turn == 'w'

        for r in range(8):
            for c in range(8):
                piece = state.board[r][c]
                if piece == ' ':
                    continue
                
                is_white_piece = piece.isupper()

                if is_white_turn == is_white_piece:
                    pseudo_moves = self.move_calculators[piece.lower()](state.board, r, c)
                    
                    for move in pseudo_moves:
                        # Create a temporary board to test the move
                        temp_board = self._get_next_board_state(state.board, move)
                        
                        # Check if the king is vulnerable on this temporary board
                        if not self._is_king_in_check(temp_board, is_white_turn):
                            # If the king is NOT in check, the move is legal
                            legal_moves.append(move)
                            
        return legal_moves
    
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
                continue

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
        """Generate all possible pawn moves from position (r, c)."""
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

    def _is_square_attacked(self, board, row: int, col: int, is_attacked_by_white: bool) -> bool:
        """
        Checks if a specific square (row, col) is under attack by the given side.
        """
        # Define the characters for the attacking pieces
        enemy_pawn = 'P' if is_attacked_by_white else 'p'
        enemy_knight = 'N' if is_attacked_by_white else 'n'
        enemy_rook = 'R' if is_attacked_by_white else 'r'
        enemy_bishop = 'B' if is_attacked_by_white else 'b'
        enemy_queen = 'Q' if is_attacked_by_white else 'q'
        enemy_king = 'K' if is_attacked_by_white else 'k'

        # Check for pawn attacks
        direction = 1 if is_attacked_by_white else -1
        pawn_attacks = [(row + direction, col - 1), (row + direction, col + 1)]
        for r, c in pawn_attacks:
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == enemy_pawn:
                return True

        # Check for knight attacks
        knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, dc in knight_moves:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == enemy_knight:
                return True

        # Check for straight-line attacks (Rooks and Queens)
        straight_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in straight_directions:
            r, c = row, col
            for _ in range(8):
                r, c = r + dr, c + dc
                if not (0 <= r < 8 and 0 <= c < 8): break
                target_piece = board[r][c]
                if target_piece != ' ':
                    if target_piece == enemy_rook or target_piece == enemy_queen:
                        return True
                    break # Path is blocked

        # Check for diagonal attacks (Bishops and Queens)
        diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in diagonal_directions:
            r, c = row, col
            for _ in range(8):
                r, c = r + dr, c + dc
                if not (0 <= r < 8 and 0 <= c < 8): break
                target_piece = board[r][c]
                if target_piece != ' ':
                    if target_piece == enemy_bishop or target_piece == enemy_queen:
                        return True
                    break # Path is blocked

        # Check for king attacks (proximity)
        king_moves = [(-1, -1),(-1, 0),(-1, 1),(0, -1),(0, 1),(1, -1),(1, 0),(1, 1)]
        for dr, dc in king_moves:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == enemy_king:
                return True

        return False

    def _is_king_in_check(self, board, is_white_king: bool) -> bool:
        """Checks if the specified king is under attack on the given board."""
        king_char = 'K' if is_white_king else 'k'
        king_pos = None

        for r in range(8):
            for c in range(8):
                if board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if king_pos is None: return False # Should not happen in a real game
        
        return self._is_square_attacked(board, king_pos[0], king_pos[1], not is_white_king)
    
    def _to_algebraic(self, row, col) -> str:
        """Helper to convert (row, col) to algebraic notation like 'a1'."""
        file = chr(ord('a') + col)
        rank = str(8 - row)
        return file + rank
    
    def _from_algebraic(self, notation: str) -> tuple[int, int]:
        """Helper to convert 'a1' to (row, col)."""
        file = notation[0]
        rank = notation[1]
        col = ord(file) - ord('a')
        row = 8 - int(rank)
        return row, col

    def _get_next_board_state(self, board, move: str) -> tuple[tuple[str, ...], ...]:
        """Creates a new board tuple with a move applied."""
        start_pos, end_pos = move[:2], move[2:]
        start_row, start_col = self._from_algebraic(start_pos)
        end_row, end_col = self._from_algebraic(end_pos)

        piece = board[start_row][start_col]
        
        # Create a mutable list of lists from the board tuple
        new_board = [list(row) for row in board]
        
        # Make the move
        new_board[start_row][start_col] = ' '
        new_board[end_row][end_col] = piece
        
        # Convert back to a tuple of tuples to be stored in a GameState
        return tuple(tuple(row) for row in new_board)
    
    def print_board(self):
        """Prints the current board state to the console."""
        board = self.current_state.board
        for r in range(8):
            # Print rank number
            print(f"{8 - r} | ", end="")
            for c in range(8):
                print(f"{board[r][c]} ", end="")
            print() # Newline for the next rank
        print("  +-----------------")
        print("    a b c d e f g h")

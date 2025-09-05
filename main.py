from dataclasses import dataclass

Board = tuple[tuple[str, ...], ...]

@dataclass(frozen=True)
class GameState:
    board: Board
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
        """Get starting state."""
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

    # Main move execution methods
    def make_move(self, move: str) -> None:
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
        pseudo_legal_moves = []
        is_white_turn = state.turn == 'w'

        # Generate standard piece moves
        for r in range(8):
            for c in range(8):
                piece = state.board[r][c]
                if piece == ' ':
                    continue
                
                is_white_piece = piece.isupper()

                if is_white_turn == is_white_piece:
                    # Add standard moves
                    pseudo_legal_moves.extend(self.move_calculators[piece.lower()](state.board, r, c))
                    
                    # Add en passant moves specifically for pawns
                    if piece.lower() == 'p':
                        pseudo_legal_moves.extend(self.get_en_passant_moves(state, r, c))

        # Add castling moves
        pseudo_legal_moves.extend(self.get_casteling_moves(state))
        
        # Filter all generated moves for legality
        legal_moves = []
        for move in pseudo_legal_moves:
            temp_board = self._get_next_board_state(state.board, move) 
            
            if not self._is_king_in_check(temp_board, is_white_turn):
                legal_moves.append(move)
                
        return legal_moves

    # Piece move generation methods
    def get_rook_moves(self, board: Board, r: int, c: int) -> list[str]:
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

    def get_knight_moves(self, board: Board, r: int, c: int) -> list[str]:
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

    def get_bishop_moves(self, board: Board, r: int, c: int) -> list[str]:
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

    def get_queen_moves(self, board: Board, r: int, c: int) -> list[str]:
        """Generate all possible queen moves from position (r, c)."""
        moves = self.get_rook_moves(board, r, c) + self.get_bishop_moves(board, r, c)
        return moves

    def get_king_moves(self, board: Board, r: int, c: int) -> list[str]:
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

    def get_pawn_moves(self, board: Board, r: int, c: int) -> list[str]:
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

        # Include promotion moves
        final_moves = []
        for move in moves:
            for promotion_piece in ['r', 'n', 'b', 'q']:
                final_moves.append(self.handle_promotion(move, promotion_piece))

        return final_moves

    def get_casteling_moves(self, state: GameState) -> list[str]:
        """Generate castling moves if legal."""
        moves = []
        board = state.board
        is_white = state.turn == 'w'

        if is_white:
            if 'K' in state.castling_rights and board[7][5] == ' ' and board[7][6] == ' ':
                # Check if squares are not under attack
                if not self._is_king_in_check(board, True):
                    if not self._is_square_attacked(board, 7, 5, False):
                        if not self._is_square_attacked(board, 7, 6, False):
                            moves.append('e1g1')
            
            if 'Q' in state.castling_rights and board[7][3] == ' ' and board[7][2] == ' ' and board[7][1] == ' ':
                if not self._is_king_in_check(board, True):
                    if not self._is_square_attacked(board, 7, 3, False):
                        if not   self._is_square_attacked(board, 7, 2, False):
                            moves.append('e1c1')
        
        else:
            if 'k' in state.castling_rights and board[0][5] == ' ' and board[0][6] == ' ':
                if not self._is_king_in_check(board, False):
                    if not self._is_square_attacked(board, 0, 5, True):
                        if not self._is_square_attacked(board, 0, 6, True):
                            moves.append('e8g8')
            
            if 'q' in state.castling_rights and board[0][3] == ' ' and board[0][2] == ' ' and board[0][1] == ' ':
                if not self._is_king_in_check(board, False):
                    if not self._is_square_attacked(board, 0, 3, True):
                        if not self._is_square_attacked(board, 0, 2, True):
                            moves.append('e8c8')
        
        return moves

    def get_en_passant_moves(self, state: GameState, r: int, c: int) -> list[str]:
        """Generate en passant capture if available."""
        moves = []
        if state.en_passant_target is None:
            return moves

        board = state.board
        piece = board[r][c]
        if piece.lower() != 'p':
            return moves
        
        is_white_pawn = piece.isupper()
        ep_row, ep_col = self._from_algebraic(state.en_passant_target)
    
        # Check if pawn is on correct rank for en passant
        if (is_white_pawn and r == 3) or (not is_white_pawn and r == 4):
            # Check if pawn is adjacent to en passant target
            if abs(c - ep_col) == 1:
                start = self._to_algebraic(r, c)
                moves.append(start + state.en_passant_target)
        
        return moves

    def handle_promotion(self, move: str, promotion_piece: str = 'q') -> str:
        """Add promotion piece to move notation if pawn reaches last rank."""
        start_row, start_col = self._from_algebraic(move[:2])
        end_row, end_col = self._from_algebraic(move[2:4])
        piece = self.current_state.board[start_row][start_col]
        
        if piece.lower() == 'p':
            if (piece.isupper() and end_row == 0) or (piece.islower() and end_row == 7):
                return move + promotion_piece.lower()
        return move

    # Game state checkin2g
    def is_checkmate(self, state: GameState) -> bool:
        """Check if the current position is checkmate."""
        is_white = state.turn == 'w'
        if not self._is_king_in_check(state.board, is_white):
            return False
        
        # If in check and no legal moves, it's checkmate
        return len(self.get_all_legal_moves(state)) == 0

    def is_stalemate(self, state: GameState) -> bool:
        """Check if the current position is stalemate."""
        is_white = state.turn == 'w'
        if self._is_king_in_check(state.board, is_white):
            return False
        
        # If not in check and no legal moves, it's stalemate
        return len(self.get_all_legal_moves(state)) == 0

    def is_draw_by_insufficient_material(self, state: GameState) -> bool:
        """Check if the position is a draw due to insufficient material."""
        pieces = []
        for row in state.board:
            for piece in row:
                if piece != ' ':
                    pieces.append(piece.lower())
        
        # Remove kings
        pieces = [p for p in pieces if p != 'k']
        
        # Draw conditions
        if len(pieces) == 0:  # Only kings
            return True
        if len(pieces) == 1 and pieces[0] in ['b', 'n']:  # King + bishop or knight
            return True
        if len(pieces) == 2 and all(p == 'b' for p in pieces):
            # Check if bishops are on same color
            bishops = []
            for r in range(8):
                for c in range(8):
                    if state.board[r][c].lower() == 'b':
                        bishops.append((r + c) % 2)
            if len(set(bishops)) == 1:  # Same color bishops
                return True
        
        return False

    def is_fifty_move_rule(self, state: GameState) -> bool:
        """Check if 50 moves have been made without pawn move or capture."""
        return state.halfmove_clock >= 100  # 50 moves = 100 half-moves

    # Check detection methods
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

    # Board manipulation methods
    def _get_next_board_state(self, board, move: str) -> Board:
        """Creates a new board tuple with a move applied."""
        start_pos, end_pos = move[:2], move[2:]
        start_row, start_col = self._from_algebraic(start_pos)
        end_row, end_col = self._from_algebraic(end_pos)

        piece = board[start_row][start_col]
        
        # Create a mutable list of lists from the board tuple
        new_board = [list(row) for row in board]
        
        # Standard move
        new_board[start_row][start_col] = ' '
        new_board[end_row][end_col] = piece

        # Handle special moves
        if piece.lower() == 'p':
            # Pawn Promotion (e.g., 'e7e8q')
            if len(move) == 5:
                promotion_piece = move[4]
                new_board[end_row][end_col] = promotion_piece.upper() if piece.isupper() else promotion_piece.lower()
            # En Passant
            elif start_col != end_col and board[end_row][end_col] == ' ':
                captured_pawn_row = start_row
                captured_pawn_col = end_col
                new_board[captured_pawn_row][captured_pawn_col] = ' '

        elif piece.lower() == 'k':
            # Castling
            if abs(start_col - end_col) == 2:
                # Kingside castling
                if end_col > start_col:
                    rook_start_col, rook_end_col = 7, 5
                # Queenside castling
                else:
                    rook_start_col, rook_end_col = 0, 3
                
                rook = new_board[start_row][rook_start_col]
                new_board[start_row][rook_end_col] = rook
                new_board[start_row][rook_start_col] = ' '
                
        return tuple(tuple(row) for row in new_board)

    # Utility methods
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
    
    def _find_move_between_states(self, prev: GameState, curr: GameState) -> str:
        """Find what move was made between two states."""
        for r in range(8):
            for c in range(8):
                if prev.board[r][c] != curr.board[r][c]:
                    if prev.board[r][c] != ' ' and curr.board[r][c] == ' ':
                        # This is the source square
                        start = self._to_algebraic(r, c)
                        # Find destination
                        for r2 in range(8):
                            for c2 in range(8):
                                if prev.board[r2][c2] != curr.board[r2][c2]:
                                    if r2 != r or c2 != c:
                                        if curr.board[r2][c2] == prev.board[r][c]:
                                            end = self._to_algebraic(r2, c2)
                                            return start + end
        return ""
    
    def undo_move(self) -> bool:
        """Undo the last move."""
        if len(self.history) <= 1:
            return False
        
        self.history.pop()
        self.current_state = self.history[-1]
        return True

    def get_move_history(self) -> list[str]:
        """Get list of moves played."""
        moves = []
        for i in range(1, len(self.history)):
            prev_state = self.history[i-1]
            curr_state = self.history[i]
            # Find the move that was made by comparing boards
            move = self._find_move_between_states(prev_state, curr_state)
            if move:
                moves.append(move)
        return moves
    
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

    def print_board_unicode(self):
        """Print board using Unicode chess symbols."""
        unicode_pieces = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
            ' ': '·'
        }
        
        board = self.current_state.board
        print("\n  ╔══════════════════════════╗")
        for r in range(8):
            print(f"{8-r} ║ ", end="")
            for c in range(8):
                piece = unicode_pieces[board[r][c]]
                # Alternate background colors
                if (r + c) % 2 == 0:
                    print(f" {piece} ", end="")
                else:
                    print(f" {piece} ", end="")
            print(" ║")
        print("  ╚══════════════════════════╝")
        print("      a  b  c  d  e  f  g  h")
        print(f"\nTurn: {'White' if self.current_state.turn == 'w' else 'Black'}")
        print(f"Castling: {self.current_state.castling_rights or 'None'}")
        print(f"En passant: {self.current_state.en_passant_target or 'None'}")
        print(f"Halfmove clock: {self.current_state.halfmove_clock}")
        print(f"Move: {self.current_state.fullmove_number}")


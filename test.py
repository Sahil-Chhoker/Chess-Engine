from main import ChessEngine

if __name__ == '__main__':
    engine = ChessEngine()
    
    while True:
        engine.print_board_unicode()
        print(f"Turn: {engine.current_state.turn}")

        try:
            if engine.is_checkmate(engine.current_state):
                if engine.history[-2].turn == 'w':
                    print("White Win!")
                else:
                    print("Black Win!")
                break
                
            move = input("Enter your move in UCI format (e.g., e2e4): ")
            
            engine.make_move(move)

        except ValueError as e:
            print(f"Invalid move: {e}")
        except KeyboardInterrupt:
            print("\nExiting game.")
            break
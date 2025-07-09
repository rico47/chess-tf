# chess_logic.py

import chess
import random

try:
    import tensorflow as tf
    import numpy as np

    print("TensorFlow załadowany.")
    _TENSORFLOW_AVAILABLE = True
except ImportError:
    print("TensorFlow nie jest zainstalowany. AI będzie używać losowych ruchów.")
    _TENSORFLOW_AVAILABLE = False
except Exception as e:
    print(f"Błąd podczas ładowania TensorFlow/modelu: {e}")
    print("AI będzie używać losowych ruchów.")
    _TENSORFLOW_AVAILABLE = False


class ChessAIPlayer:
    # ... (reszta kodu ChessAIPlayer bez zmian) ...
    def __init__(self, use_tensorflow=False):
        self.use_tensorflow = use_tensorflow and _TENSORFLOW_AVAILABLE
        self.tf_model = None
        if self.use_tensorflow:
            print("AI użyje symbolicznego TensorFlow.")
            self.tf_model = lambda board_representation: np.random.rand() * 2 - 1
        else:
            print("AI użyje prostego losowego algorytmu.")

    def _board_to_input_representation(self, board):
        fen_string = board.fen().split(' ')[0]
        return np.array([ord(c) for c in fen_string])

    def get_best_move(self, board, depth=2):
        if self.use_tensorflow and self.tf_model:
            best_move = None
            best_score = -float('inf') if board.turn == chess.WHITE else float('inf')

            for move in board.legal_moves:
                board.push(move)
                score = self._minimax(board, depth - 1, not board.turn)
                board.pop()

                if board.turn == chess.WHITE:
                    if score > best_score:
                        best_score = score
                        best_move = move
                else:
                    if score < best_score:
                        best_score = score
                        best_move = move

            return best_move if best_move else self._get_random_move(board)

        else:
            return self._get_random_move(board)

    def _minimax(self, board, current_depth, maximizing_player):
        if current_depth == 0 or board.is_game_over():
            if board.is_checkmate():
                return -1000000 if board.turn == chess.WHITE else 1000000
            elif board.is_stalemate():
                return 0
            return self.tf_model(self._board_to_input_representation(board))

        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self._minimax(board, current_depth - 1, False)
                board.pop()
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self._minimax(board, current_depth - 1, True)
                board.pop()
                min_eval = min(min_eval, eval)
            return min_eval

    def _get_random_move(self, board):
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)
        return None

    def quit_engine(self):
        print("Symboliczny model TensorFlow nie wymaga zamykania.")


class ChessGameLogic:
    def __init__(self):
        self.board = chess.Board()
        self.players = {
            chess.WHITE: 'HUMAN',
            chess.BLACK: 'HUMAN'
        }
        self.ai_engine = None
        self.ai_depth = 2

    def set_player_type(self, color, player_type):
        if player_type not in ['HUMAN', 'AI_RANDOM', 'AI_TF']:
            raise ValueError("Typ gracza musi być 'HUMAN', 'AI_RANDOM' lub 'AI_TF'")
        self.players[color] = player_type

    def initialize_ai(self, ai_type, skill_level=None):
        if self.ai_engine:
            self.ai_engine.quit_engine()
            self.ai_engine = None

        if ai_type == 'AI_TF':
            self.ai_engine = ChessAIPlayer(use_tensorflow=True)
            self.ai_depth = skill_level if skill_level is not None else 2
        elif ai_type == 'AI_RANDOM':
            self.ai_engine = ChessAIPlayer(use_tensorflow=False)
            self.ai_depth = 1
        # Jeśli ai_type to None, ai_engine pozostaje None, co oznacza brak AI.

    def get_ai_move(self):
        current_player_type = self.players[self.board.turn]
        if self.ai_engine and (current_player_type == 'AI_TF' or current_player_type == 'AI_RANDOM'):
            return self.ai_engine.get_best_move(self.board, depth=self.ai_depth)
        return None

    def get_current_player_type(self):
        return self.players[self.board.turn]

    def get_fen(self):
        return self.board.fen()

    def get_turn_color(self):
        return 'white' if self.board.turn == chess.WHITE else 'black'

    def make_move(self, start_square_name, end_square_name):
        try:
            start_square = chess.parse_square(start_square_name)
            end_square = chess.parse_square(end_square_name)
            move = chess.Move(start_square, end_square)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except ValueError:
            return False

    def make_move_object(self, move_obj):
        if move_obj and move_obj in self.board.legal_moves:
            self.board.push(move_obj)
            return True
        return False

    def is_game_over(self):
        return self.board.is_game_over()

    def get_game_result(self):
        return self.board.result()

    def is_check(self):
        return self.board.is_check()

    def is_checkmate(self):
        return self.board.is_checkmate()

    def is_stalemate(self):
        return self.board.is_stalemate()

    def get_piece_at(self, square_name):
        square = chess.parse_square(square_name)
        return self.board.piece_at(square)

    def reset_game(self):
        """
        Resetuje szachownicę do pozycji początkowej.
        Usunięto resetowanie typów graczy, ponieważ są one konfigurowane przez GUI.
        """
        self.board.reset()
        # Usunięto:
        # self.players = {
        #     chess.WHITE: 'HUMAN',
        #     chess.BLACK: 'HUMAN'
        # }

    def get_board_state(self):
        state = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                state[chess.square_name(square)] = piece.symbol()
            else:
                state[chess.square_name(square)] = None
        return state

    def get_legal_moves(self, square_name):
        legal_destinations = []
        try:
            source_square = chess.parse_square(square_name)
            for move in self.board.legal_moves:
                if move.from_square == source_square:
                    legal_destinations.append(chess.square_name(move.to_square))
        except ValueError:
            pass
        return legal_destinations

    def __del__(self):
        if self.ai_engine:
            self.ai_engine.quit_engine()
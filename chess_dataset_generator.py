import chess
import numpy as np
import random
import pickle


def create_board_representation(board):
    """
    Tworzy uproszczoną wektorową reprezentację szachownicy dla sieci neuronowej.
    Dla każdej figury (6 typów * 2 kolory = 12) tworzymy warstwę 8x8,
    a także warstwę dla tury. Sumarycznie 13x8x8.
    """
    representation = np.zeros((13, 8, 8), dtype=np.float32)

    piece_to_index = {
        chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2,
        chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row, col = chess.square_rank(square), chess.square_file(square)
            piece_idx = piece_to_index[piece.piece_type]

            # Warstwy dla białych figur (0-5)
            if piece.color == chess.WHITE:
                representation[piece_idx, row, col] = 1.0
            # Warstwy dla czarnych figur (6-11)
            else:
                representation[piece_idx + 6, row, col] = 1.0

    # Warstwa dla tury (12)
    if board.turn == chess.WHITE:
        representation[12, :, :] = 1.0  # Cała warstwa na 1 jeśli białe
    else:
        representation[12, :, :] = 0.0  # Cała warstwa na 0 jeśli czarne

    return representation.flatten()  # Spłaszczamy do jednowymiarowego wektora


def generate_synthetic_data(num_samples=1000):
    """
    Generuje syntetyczne dane: pozycje na szachownicy i ich "losowe" oceny.
    To jest tylko dla celów DEMONSTRACYJNYCH.
    W PRAWDZIWEJ aplikacji:
    - używałbyś prawdziwych partii PGN
    - ocena byłaby wynikiem głębokiej analizy Stockfisha lub samogrania AlphaZero.
    """
    data_X = []
    data_y = []

    board = chess.Board()

    for _ in range(num_samples):
        # Wykonaj losową liczbę ruchów, aby uzyskać różne pozycje
        for _ in range(random.randint(1, 20)):
            if board.legal_moves:
                move = random.choice(list(board.legal_moves))
                board.push(move)
            else:
                break  # Gra skończona

        # Zapisz reprezentację pozycji
        data_X.append(create_board_representation(board))

        # Przypisz "ocenę" pozycji - tym razem symulujemy, że białe mają 1, czarne -1, remis 0
        # TO JEST BARDZO UPROSZCZONA I NIEREALISTYCZNA OCENA DLA CELÓW DEMONSTRACYJNYCH
        if board.is_checkmate():
            # Jeśli białe matują, to +1; jeśli czarne matują, to -1.
            score = 1.0 if board.turn == chess.BLACK else -1.0  # Wygrywa ten, kto matuje
        elif board.is_stalemate():
            score = 0.0
        elif board.is_insufficient_material():
            score = 0.0
        else:
            # Losowa ocena dla pozycji w trakcie gry - ZUPEŁNIE LOSOWA!
            # W PRAWDZIE: Ocena jest generowana przez silnik szachowy lub sieć neuronową.
            score = random.uniform(-1.0, 1.0)

        data_y.append(score)

        board.reset()  # Resetuj szachownicę dla kolejnej próbki

    X = np.array(data_X)
    y = np.array(data_y)

    # Zapisz dane do pliku
    with open('chess_data.pkl', 'wb') as f:
        pickle.dump({'X': X, 'y': y}, f)

    print(f"Wygenerowano {num_samples} syntetycznych próbek danych.")
    print(f"Kształt X: {X.shape}, Kształt y: {y.shape}")


if __name__ == '__main__':
    generate_synthetic_data(num_samples=5000)  # Możesz zwiększyć tę liczbę, jeśli chcesz
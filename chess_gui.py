import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QLabel, QMessageBox, QHBoxLayout, QComboBox,
                             QLineEdit, QFormLayout)
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QTimer
import chess
from chess_logic import ChessGameLogic


class ChessBoardWidget(QWidget):
    game_state_changed = pyqtSignal()
    ai_move_requested = pyqtSignal()

    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.selected_square = None
        self.piece_images = self.load_piece_images()
        self.setMinimumSize(480, 480)
        self.setMouseTracking(True)
        self.highlighted_legal_moves = []

    def load_piece_images(self):
        images = {}
        piece_map = {
            'r': 'black-rook', 'n': 'black-knight', 'b': 'black-bishop', 'q': 'black-queen', 'k': 'black-king',
            'p': 'black-pawn',
            'R': 'white-rook', 'N': 'white-knight', 'B': 'white-bishop', 'Q': 'white-queen', 'K': 'white-king',
            'P': 'white-pawn',
        }
        for piece_char, file_name in piece_map.items():
            path = f'./img/chess_pieces/{file_name}.png'
            try:
                images[piece_char] = QPixmap(path)
                if images[piece_char].isNull():
                    print(f"Błąd: Nie udało się załadować obrazka: {path}")
            except Exception as e:
                print(f"Wyjątek podczas ładowania obrazka {path}: {e}")
        return images

    def paintEvent(self, event):
        painter = QPainter(self)
        board_size = min(self.width(), self.height())
        square_size = board_size // 8

        # Rysowanie pól szachownicy
        for row_idx in range(8):
            for col_idx in range(8):
                color = QColor("#f0d9b5") if (row_idx + col_idx) % 2 == 0 else QColor("#b58863")
                painter.fillRect(col_idx * square_size, row_idx * square_size, square_size, square_size, color)

        # Podświetlenie zaznaczonego pola
        if self.selected_square:
            s_col, s_row_logic = self.get_coords_from_square_name(self.selected_square)
            s_row_gui = 7 - s_row_logic  # Odwrócenie rzędów dla GUI
            painter.fillRect(s_col * square_size, s_row_gui * square_size, square_size, square_size,
                             QColor(255, 255, 0, 150))  # Żółty z przezroczystością

        # Podświetlanie legalnych ruchów
        for move_square_name in self.highlighted_legal_moves:
            m_col, m_row_logic = self.get_coords_from_square_name(move_square_name)
            m_row_gui = 7 - m_row_logic  # Odwrócenie rzędów dla GUI
            painter.fillRect(m_col * square_size, m_row_gui * square_size, square_size, square_size,
                             QColor(0, 255, 0, 80))  # Zielony z przezroczystością

        # Rysowanie figur
        for square_name, piece_symbol in self.game_logic.get_board_state().items():
            if piece_symbol:
                col_idx, row_logic_idx = self.get_coords_from_square_name(square_name)
                row_gui_idx = 7 - row_logic_idx  # Odwrócenie rzędów dla GUI

                image = self.piece_images.get(piece_symbol)
                if image and not image.isNull():
                    target_rect = QRect(col_idx * square_size, row_gui_idx * square_size, square_size, square_size)
                    scaled_image = image.scaled(square_size, square_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    painter.drawPixmap(target_rect.center() - scaled_image.rect().center(), scaled_image)

    def mousePressEvent(self, event):
        # W trybie AI vs AI, kliknięcia myszy są ignorowane
        if self.game_logic.get_current_player_type() != 'HUMAN' or self.game_logic.is_game_over():
            return

        if event.button() == Qt.LeftButton:
            board_size = min(self.width(), self.height())
            square_size = board_size // 8

            col_idx = event.x() // square_size
            row_gui_idx = event.y() // square_size

            clicked_square_name = self.get_square_name(col_idx, row_gui_idx)

            if self.selected_square:
                # Drugie kliknięcie: spróbuj wykonać ruch
                if self.game_logic.make_move(self.selected_square, clicked_square_name):
                    self.selected_square = None
                    self.highlighted_legal_moves = []
                    self.game_state_changed.emit()  # Wyślij sygnał o zmianie stanu
                    # Jeśli gra się nie zakończyła i teraz jest tura AI, poproś o ruch AI
                    if not self.game_logic.is_game_over() and self.game_logic.get_current_player_type() != 'HUMAN':
                        self.ai_move_requested.emit()
                else:
                    # Jeśli ruch nielegalny, ale kliknięto własną figurę, zmień zaznaczenie
                    piece_at_clicked = self.game_logic.get_piece_at(clicked_square_name)
                    if piece_at_clicked and (piece_at_clicked.color == self.game_logic.board.turn):
                        self.selected_square = clicked_square_name
                        self.highlighted_legal_moves = self.game_logic.get_legal_moves(self.selected_square)
                    else:
                        self.selected_square = None  # Usuń zaznaczenie
                        self.highlighted_legal_moves = []
            else:
                # Pierwsze kliknięcie: zaznacz figurę
                piece = self.game_logic.get_piece_at(clicked_square_name)
                if piece and (piece.color == self.game_logic.board.turn):
                    self.selected_square = clicked_square_name
                    self.highlighted_legal_moves = self.game_logic.get_legal_moves(self.selected_square)
                else:
                    self.selected_square = None
                    self.highlighted_legal_moves = []

            self.update()  # Odśwież widok szachownicy

    def get_square_name(self, col_idx, row_gui_idx):
        """Konwertuje indeksy kolumny i rzędu GUI na nazwę pola (np. 'a1', 'h8')."""
        file_char = chr(ord('a') + col_idx)
        rank_num = 8 - row_gui_idx  # Odwrócenie rzędów dla logicznej numeracji (1-8)
        return f"{file_char}{rank_num}"

    def get_coords_from_square_name(self, square_name):
        """Konwertuje nazwę pola (np. 'e4') na indeksy kolumny i rzędu logicznego."""
        col_idx = ord(square_name[0]) - ord('a')
        row_logic_idx = int(square_name[1]) - 1  # 0-7
        return col_idx, row_logic_idx


class ChessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Szachy PyQt5 z AI (TensorFlow - Symbolicznie)")
        self.setGeometry(100, 100, 600, 750)  # Zwiększona wysokość na opcje

        self.game_logic = ChessGameLogic()  # Tworzymy instancję logiki gry

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Sekcja wyboru graczy AI
        self.player_selection_layout = QFormLayout()

        # Opcje dla białych
        self.white_player_combo = QComboBox()
        self.white_player_combo.addItems(["Człowiek", "AI (Losowe)", "AI (TensorFlow - Symbolicznie)"])
        self.white_player_combo.setCurrentIndex(0)  # Domyślnie człowiek
        self.player_selection_layout.addRow("Białe:", self.white_player_combo)

        # Opcje dla czarnych
        self.black_player_combo = QComboBox()
        self.black_player_combo.addItems(["Człowiek", "AI (Losowe)", "AI (TensorFlow - Symbolicznie)"])
        self.black_player_combo.setCurrentIndex(0)  # Domyślnie człowiek
        self.player_selection_layout.addRow("Czarne:", self.black_player_combo)

        self.skill_level_input = QLineEdit("2")  # Domyślna głębokość dla Minimax
        self.skill_level_input.setPlaceholderText("Głębokość Minimax dla AI (np. 1-3)")
        self.player_selection_layout.addRow("Głębokość AI:", self.skill_level_input)

        # Nowy przycisk do trybu AI vs AI
        self.ai_vs_ai_button = QPushButton("AI (TF) vs AI (TF)")
        self.ai_vs_ai_button.clicked.connect(self.start_ai_vs_ai_game)
        self.layout.addWidget(self.ai_vs_ai_button)

        self.layout.addLayout(self.player_selection_layout)

        self.chessboard_widget = ChessBoardWidget(self.game_logic, self)  # Przekazujemy logikę do widgetu
        self.chessboard_widget.game_state_changed.connect(self.update_game_status)  # Podłącz sygnał
        self.chessboard_widget.ai_move_requested.connect(self.make_ai_move_delayed)  # Podłącz sygnał
        self.layout.addWidget(self.chessboard_widget)

        self.status_label = QLabel("Tura: Białe")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; margin-top: 10px;")
        self.layout.addWidget(self.status_label)

        self.new_game_button = QPushButton("Nowa Gra")
        self.new_game_button.clicked.connect(self.start_new_game)
        self.layout.addWidget(self.new_game_button)

        # Timer do opóźniania ruchów AI
        self.ai_timer = QTimer(self)
        self.ai_timer.setSingleShot(True)  # Timer uruchamia się tylko raz
        self.ai_timer.timeout.connect(self.make_ai_move)

        self.update_game_status()  # Ustaw początkowy status

    def _get_player_type_from_combo(self, combo_box):
        """Pomocnicza funkcja do mapowania tekstu z ComboBoxa na typ gracza."""
        text = combo_box.currentText()
        if "Człowiek" in text:
            return 'HUMAN'
        elif "Losowe" in text:
            return 'AI_RANDOM'
        elif "TensorFlow" in text:
            return 'AI_TF'
        return 'HUMAN'  # Domyślne w razie błędu

    def start_new_game(self):
        """Rozpoczyna nową grę na podstawie wyborów użytkownika."""
        self.ai_timer.stop()  # Zatrzymanie timera AI, jeśli był aktywny

        white_player_type = self._get_player_type_from_combo(self.white_player_combo)
        black_player_type = self._get_player_type_from_combo(self.black_player_combo)

        self._configure_and_start_game(white_player_type, black_player_type)

    def start_ai_vs_ai_game(self):
        """Rozpoczyna grę AI (TF) vs AI (TF)."""
        self.ai_timer.stop()  # Zatrzymanie timera AI, jeśli był aktywny
        # Ustawienie ComboBoxów na AI (TensorFlow)
        self.white_player_combo.setCurrentIndex(2)
        self.black_player_combo.setCurrentIndex(2)
        self._configure_and_start_game('AI_TF', 'AI_TF')

    def _configure_and_start_game(self, white_player_type, black_player_type):
        """Wspólna logika uruchamiania nowej gry."""
        self.game_logic.set_player_type(chess.WHITE, white_player_type)
        self.game_logic.set_player_type(chess.BLACK, black_player_type)

        skill_level = int(self.skill_level_input.text() or '2')  # Domyślnie 2 jeśli puste

        # Inicjalizacja AI, jeśli któryś z graczy to AI
        if white_player_type != 'HUMAN' or black_player_type != 'HUMAN':
            if white_player_type == 'AI_TF' or black_player_type == 'AI_TF':
                self.game_logic.initialize_ai('AI_TF', skill_level)
            else:  # Oznacza, że ktoś wybrał "Losowe"
                self.game_logic.initialize_ai('AI_RANDOM', skill_level)
        else:
            self.game_logic.initialize_ai(None)  # Brak AI

        self.game_logic.reset_game()
        self.chessboard_widget.selected_square = None
        self.chessboard_widget.highlighted_legal_moves = []
        self.chessboard_widget.update()
        self.update_game_status()
        QMessageBox.information(self, "Nowa Gra", "Rozpoczęto nową grę!")

        # Sprawdź, czy pierwszy ruch powinien należeć do AI
        if self.game_logic.get_current_player_type() != 'HUMAN':
            self.make_ai_move_delayed()

    def update_game_status(self):
        """Aktualizuje etykietę statusu gry i odświeża szachownicę."""
        board = self.game_logic.board
        turn_color_str = self.game_logic.get_turn_color()
        current_player_type = self.game_logic.get_current_player_type()

        # Wyświetlanie bardziej szczegółowego typu gracza
        display_player_type = "Człowiek"
        if current_player_type == 'AI_RANDOM':
            display_player_type = "AI (Losowe)"
        elif current_player_type == 'AI_TF':
            display_player_type = "AI (TensorFlow)"

        status_text = f"Tura: {turn_color_str.capitalize()} ({display_player_type})"

        if self.game_logic.is_checkmate():
            status_text = f"Szach-mat! Wygrały {'Czarne' if board.turn == chess.WHITE else 'Białe'}."
            self.ai_timer.stop()  # Zakończ timer, bo gra się skończyła
        elif self.game_logic.is_stalemate():
            status_text = "Pat! Remis."
            self.ai_timer.stop()
        elif self.game_logic.is_game_over():  # Generalne sprawdzenie zakończenia
            status_text = f"Gra zakończona! Wynik: {self.game_logic.get_game_result()}"
            self.ai_timer.stop()
        elif self.game_logic.is_check():
            status_text += " (Szach!)"

        self.status_label.setText(status_text)
        self.chessboard_widget.update()  # **Odśwież szachownicę!**

    def make_ai_move_delayed(self):
        """Opóźnia ruch AI, żeby było widać co się dzieje."""
        self.status_label.setText(f"Tura: {self.game_logic.get_turn_color().capitalize()} (AI myśli...)")
        self.ai_timer.start(500)  # Opóźnienie 0.5 sekundy

    def make_ai_move(self):
        """Wykonuje ruch AI i aktualizuje GUI."""
        if self.game_logic.is_game_over():
            return

        # Upewnij się, że to faktycznie tura AI
        if self.game_logic.get_current_player_type() == 'HUMAN':
            return  # Nie wykonuj ruchu AI, jeśli to tura człowieka

        ai_move = self.game_logic.get_ai_move()  # Pobierz ruch od AI

        if ai_move:
            print(f"AI ({self.game_logic.get_turn_color()}) wykonuje ruch: {ai_move.uci()}")  # Wypisz w konsoli
            self.game_logic.make_move_object(ai_move)  # Wykonaj ruch AI
            self.update_game_status()  # Zaktualizuj status i odśwież szachownicę
            # self.chessboard_widget.update() # Już wywoływane przez update_game_status()

            # Jeśli gra się nie skończyła i teraz jest tura kolejnego AI, poproś o kolejny ruch
            if not self.game_logic.is_game_over() and self.game_logic.get_current_player_type() != 'HUMAN':
                self.make_ai_move_delayed()
        else:
            QMessageBox.warning(self, "Błąd AI",
                                "AI nie mogło znaleźć legalnego ruchu! (Wykonywanie losowego ruchu awaryjnie)")
            # Awaryjnie wykonaj losowy legalny ruch, żeby gra się nie zawiesiła
            if not self.game_logic.is_game_over() and self.game_logic.board.legal_moves:
                self.game_logic.make_move_object(
                    list(self.game_logic.board.legal_moves)[0])  # Wybierz pierwszy legalny ruch
                self.update_game_status()
                # self.chessboard_widget.update() # Już wywoływane przez update_game_status()
                if self.game_logic.get_current_player_type() != 'HUMAN':
                    self.make_ai_move_delayed()

    def __del__(self):
        """Zamyka silnik AI przy zamykaniu aplikacji."""
        print("Zamykanie aplikacji, zamykam silnik AI...")
        if self.game_logic.ai_engine:
            self.game_logic.ai_engine.quit_engine()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChessApp()
    window.show()
    sys.exit(app.exec_())
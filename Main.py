import sys
import os
import sqlite3
import configparser
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QComboBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Wordle(QWidget):
    def __init__(self):
        super().__init__()
        self.currentRow = 0
        self.compWord = ""
        self.initUI()

    def initUI(self):
        self.setGeometry(50, 50, 600, 500)
        self.setWindowTitle("Wordle")
        icon_path = resource_path("images/Python.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.getRandomWord()

        grid = QGridLayout()
        grid.setRowMinimumHeight(0, 30)
        grid.setRowMinimumHeight(7, 30)
        grid.setColumnMinimumWidth(0, 30)
        grid.setColumnMinimumWidth(6, 30)
        self.setLayout(grid)

        self.titleLabel = QLabel("Wordle")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("""
            font-size: 40px;
            font-weight: bold;
            font-family: "DejaVu Sans Mono", monospace;
            margin: 30px;
        """)
        grid.addWidget(self.titleLabel, 0, 0, 1, 7)

        self.userTextBoxes = [[] for _ in range(5)]
        for row in range(5):
            for col in range(5):
                line_edit = QLineEdit()
                line_edit.setMaxLength(1)
                line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                line_edit.setMinimumSize(100, 100)
                self.userTextBoxes[row].append(line_edit)
                grid.addWidget(line_edit, row + 1, col + 1)

        self.updateRowStyles()

        self.userMessage = QLabel(" ")
        self.userMessage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.userMessage.setStyleSheet("font-size: 16px;")
        grid.addWidget(self.userMessage, 7, 0, 1, 7)

        self.buttonReset = QPushButton("START AGAIN")
        self.buttonReset.setStyleSheet("""
            QPushButton {
                border: 2px solid black;
                font-weight: bold;
                font-size: 18px;
                padding: 15px 25px;
                margin: 0 0 30px 0;
                color: black;
                background: red;
            }
            QPushButton:hover {
                background: darkred;
                color: white;
            }
        """)
        self.buttonReset.clicked.connect(self.buttonResetClicked)
        grid.addWidget(self.buttonReset, 8, 2, 1, 3)
        self.buttonReset.hide()

        self.buttonGuess = QPushButton("GUESS")
        self.buttonGuess.setStyleSheet("""
            QPushButton {
                border: 2px solid black;
                font-weight: bold;
                font-size: 18px;
                padding: 15px 25px;
                margin: 0 0 30px 0;
                color: black;
                background: lightgreen;
            }
            QPushButton:hover {
                background: darkgreen;
                color: white;
            }
        """)
        self.buttonGuess.clicked.connect(self.buttonGuessClicked)
        grid.addWidget(self.buttonGuess, 8, 2, 1, 3)
    
        self.settings = QPushButton()
        self.settings.setIcon(QIcon(resource_path('images/Gear.png')))
        self.settings.setIconSize(QSize(32, 32))
        self.settings.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 30);
            }
        """)
        self.settings.clicked.connect(self.show_settings)
        grid.addWidget(self.settings, 0, 6, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

    def updateRowStyles(self):
        for row_idx, row in enumerate(self.userTextBoxes):
            if row_idx < self.currentRow:
                continue
            elif row_idx == self.currentRow:
                for box in row:
                    box.setReadOnly(False)
                    box.setStyleSheet("""
                        border: 2px solid black;
                        font-size: 30px;
                        margin: 10px;
                        background: white;
                        color: black;
                    """)
            else:
                for box in row:
                    box.setReadOnly(True)
                    box.setStyleSheet("""
                        border: 2px solid black;
                        font-size: 30px;
                        margin: 10px;
                        background: lightgrey;
                        color: black;
                    """)

    def get_word_mode(self):
        config = configparser.ConfigParser()
        config_path = resource_path("config.ini")
        try:
            config.read(config_path)
            return config.get("Settings", "word_mode", fallback="Default")
        except Exception:
            return "Default"

    def getRandomWord(self):
        mode = self.get_word_mode()
        table = "user_words" if mode == "Custom" else "words"
        db_path = resource_path("words.db")

        if mode == "Custom":
            try:
                with sqlite3.connect(db_path) as conn_check:
                    cursor = conn_check.cursor()
                    cursor.execute("SELECT COUNT(*) FROM user_words")
                    if cursor.fetchone()[0] == 0:
                        self.userMessage.setText("No custom words! Using default.")
                        table = "words"
            except Exception:
                table = "words"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT word FROM {table} ORDER BY RANDOM() LIMIT 1")
            result = cursor.fetchone()
            if result:
                self.compWord = result[0].lower()
            else:
                self.compWord = "error"
            conn.close()
        except Exception as e:
            print("DB error:", e)
            self.compWord = "error"

    def is_word_in_dictionary(self, word):
        db_path = resource_path("words.db")
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM words WHERE word = ?", (word,))
                return cursor.fetchone() is not None
        except Exception as e:
            print("Dictionary check error:", e)
            return True

    def buttonResetClicked(self):
        self.currentRow = 0
        self.getRandomWord()
        for row in self.userTextBoxes:
            for box in row:
                box.clear()
        self.userMessage.setText(" ")
        self.buttonSwap()
        self.updateRowStyles()

    def buttonGuessClicked(self):
        if not self.checkInputsValid():
            self.userMessage.setText("Please enter English letters only")
            return

        user_word = "".join(box.text().lower() for box in self.userTextBoxes[self.currentRow])

        if not self.is_word_in_dictionary(user_word):
            self.userMessage.setText("Word not found in dictionary!")
            return

        if self.checkWin():
            return

        self.colourActiveRow()
        if self.currentRow < 4:
            self.currentRow += 1
            self.updateRowStyles()
        else:
            self.userMessage.setText(f"Game over! Word was: {self.compWord}")
            self.buttonSwap()

    def colourActiveRow(self):
        user_word = "".join(box.text().lower() for box in self.userTextBoxes[self.currentRow])
        comp_word = self.compWord.lower()

        from collections import Counter
        remaining = Counter(comp_word)

        colors = [None] * 5
        for i in range(5):
            if user_word[i] == comp_word[i]:
                colors[i] = "green"
                remaining[user_word[i]] -= 1

        for i in range(5):
            if colors[i] is None:
                if remaining[user_word[i]] > 0:
                    colors[i] = "yellow"
                    remaining[user_word[i]] -= 1
                else:
                    colors[i] = "darkgrey"

        for i, box in enumerate(self.userTextBoxes[self.currentRow]):
            box.setReadOnly(True)
            bg = colors[i]
            text_color = "white" if bg in ("green", "darkgrey") else "black"
            box.setStyleSheet(f"""
                border: 2px solid black;
                font-size: 30px;
                margin: 10px;
                background: {bg};
                color: {text_color};
            """)

    def checkWin(self):
        current_word = "".join(box.text().lower() for box in self.userTextBoxes[self.currentRow])
        if current_word == self.compWord.lower():
            for box in self.userTextBoxes[self.currentRow]:
                box.setStyleSheet("""
                    border: 2px solid black;
                    font-size: 30px;
                    margin: 10px;
                    background: green;
                    color: white;
                """)
                box.setReadOnly(True)
            self.userMessage.setText("WINNER!")
            self.buttonSwap()
            return True
        return False

    def buttonSwap(self):
        if self.buttonGuess.isVisible():
            self.buttonGuess.hide()
            self.buttonReset.show()
        else:
            self.buttonReset.hide()
            self.buttonGuess.show()

    def checkInputsValid(self):
        for box in self.userTextBoxes[self.currentRow]:
            text = box.text()
            if len(text) != 1 or not text.isalpha() or not text.isascii():
                return False
        return True

    def show_settings(self):
        self.w2 = Settings()
        self.w2.show()


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_words_from_db()

    def initUI(self):
        self.setGeometry(50, 50, 600, 500)
        self.setWindowTitle("Settings")
        icon_path = resource_path("images/Gear.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #1e1e1e;
                color: white;
            }
            QLineEdit {
                border: 2px solid #444;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 14px;
                min-width: 300px;
                background-color: #2d2d2d;
                color: white;
            }
            QLineEdit:hover {
                border: 2px solid #0078d7;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #0078d7;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 2px solid #444;
                border-radius: 8px;
                padding: 5px;
                margin-top: 10px;
                color: white;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 2px solid #444;
                border-radius: 6px;
                padding: 5px;
                color: white;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 2px solid #0078d7;
            }
        """)

        self.titleLabel = QLabel("Custom Words")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.titleLabel.setStyleSheet("""
            font-size: 40px;
            font-weight: bold;
            font-family: "DejaVu Sans Mono", monospace;
            margin: 20px 0;
        """)

        row1_layout = QHBoxLayout()
        self.word_input1 = QLineEdit()
        self.word_input1.setPlaceholderText("Enter 5-letter word to delete")
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_word)
        row1_layout.addWidget(self.word_input1)
        row1_layout.addWidget(self.delete_button)

        row2_layout = QHBoxLayout()
        self.word_input2 = QLineEdit()
        self.word_input2.setPlaceholderText("Enter 5-letter English word (e.g. 'apple')")
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_word_from_input)
        row2_layout.addWidget(self.word_input2)
        row2_layout.addWidget(self.add_button)

        self.words_list_widget = QListWidget()
        self.words_list_widget.setMinimumHeight(200)

        self.userMessage = QLabel("")
        self.userMessage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.userMessage.setStyleSheet("color: #ff6666; font-size: 13px; margin: 5px 0;")

        self.mode_label = QLabel("Use words:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Default", "Custom"])
        self.mode_combo.setCurrentText(self.load_word_mode())
        self.mode_combo.currentTextChanged.connect(self.save_word_mode)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addLayout(row1_layout)
        main_layout.addLayout(row2_layout)
        main_layout.addWidget(QLabel("Added words:"))
        main_layout.addWidget(self.words_list_widget)
        main_layout.addWidget(self.userMessage)
        main_layout.addSpacing(10)
        main_layout.addLayout(mode_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def get_config_path(self):
        return resource_path("config.ini")

    def load_word_mode(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.get_config_path())
            return config.get("Settings", "word_mode", fallback="Default")
        except Exception:
            return "Default"

    def save_word_mode(self, mode):
        config = configparser.ConfigParser()
        config.read(self.get_config_path())
        if not config.has_section("Settings"):
            config.add_section("Settings")
        config.set("Settings", "word_mode", mode)
        try:
            with open(self.get_config_path(), "w") as f:
                config.write(f)
        except Exception as e:
            print("Error saving config:", e)

    def load_words_from_db(self):
        self.words_list_widget.clear()
        self.userMessage.setText("")
        db_path = resource_path("words.db")
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT word FROM user_words ORDER BY word")
                words = cursor.fetchall()
                for (word,) in words:
                    self.words_list_widget.addItem(word)
        except Exception as e:
            error_msg = "Error loading words from DB"
            print(error_msg, e)
            self.userMessage.setText(error_msg)

    def add_word_from_input(self):
        word = self.word_input2.text().strip()

        if not word:
            self.userMessage.setText("Please enter a word.")
            return

        if len(word) != 5:
            self.userMessage.setText(f"Word must be exactly 5 letters long! ({len(word)} given)")
            self.word_input2.selectAll()
            return

        if not word.isalpha():
            self.userMessage.setText("Word must contain only letters (no numbers or symbols)!")
            self.word_input2.selectAll()
            return

        if not word.isascii():
            self.userMessage.setText("Word must contain only English letters (A–Z)!")
            self.word_input2.selectAll()
            return

        self.add_word_to_db(word.lower())
        self.word_input2.clear()
        self.load_words_from_db()

    def delete_word(self):
        word = self.word_input1.text().strip()
        if not word:
            self.userMessage.setText("Please enter a word to delete.")
            return

        if len(word) != 5:
            self.userMessage.setText(f"Word to delete must be exactly 5 letters long! ({len(word)} given)")
            self.word_input1.selectAll()
            return

        if not word.isalpha():
            self.userMessage.setText("Word to delete must contain only letters (no numbers or symbols)!")
            self.word_input1.selectAll()
            return

        if not word.isascii():
            self.userMessage.setText("Word to delete must contain only English letters (A–Z)!")
            self.word_input1.selectAll()
            return

        db_path = resource_path("words.db")
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_words WHERE word = ?", (word.lower(),))
                deleted = cursor.rowcount
                if deleted == 0:
                    self.userMessage.setText(f'Word "{word}" not found in custom list.')
                else:
                    self.userMessage.setText(f'Word "{word}" deleted.')
        except Exception as e:
            print("Error deleting word:", e)
            self.userMessage.setText("Error deleting word.")
        finally:
            self.word_input1.clear()
            self.load_words_from_db()

    def add_word_to_db(self, word):
        db_path = resource_path("words.db")
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO user_words (word) VALUES (?)", (word,))
                if cursor.rowcount == 0:
                    self.userMessage.setText(f'Word "{word}" already exists.')
                else:
                    self.userMessage.setText(f'Word "{word}" added successfully.')
        except Exception as e:
            print("Error adding word:", e)
            self.userMessage.setText("Error adding word.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Wordle()
    ex.show()
    sys.exit(app.exec())
import sys
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


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

    def updateRowStyles(self):
        """Apply correct styles to all rows based on currentRow."""
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

    def getRandomWord(self):
        db_path = resource_path("words.db")
        if not os.path.exists(db_path):
            self.compWord = ""
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM words ORDER BY RANDOM() LIMIT 1")
            result = cursor.fetchone()
            if result:
                self.compWord = result[0].lower()
            conn.close()
        except Exception:
            self.compWord = "hello"

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
            self.userMessage.setText("Please enter letters only")
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
            if not box.text().isalpha() or len(box.text()) != 1:
                return False
        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Wordle()
    ex.show()
    sys.exit(app.exec())
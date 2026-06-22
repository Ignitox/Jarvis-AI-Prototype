import sys
import random

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QLineEdit,
    QLabel,
    QHBoxLayout
)

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor, QFont

from main import process_command, speak, listen


class VoiceBars(QWidget):
    def __init__(self):
        super().__init__()
        self.bars = [20] * 18

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(120)

        self.setMinimumHeight(180)

    def animate(self):
        self.bars = [
            random.randint(20, 140)
            for _ in self.bars
        ]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(0, 140, 255))
        painter.setPen(Qt.PenStyle.NoPen)

        width = self.width()
        spacing = width // len(self.bars)

        x = 10

        for bar in self.bars:
            painter.drawRoundedRect(
                x,
                self.height() - bar,
                14,
                bar,
                8,
                8
            )
            x += spacing


class JarvisGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jarvis")
        self.setGeometry(250, 100, 700, 850)

        self.setStyleSheet("""
            QWidget {
                background-color: black;
                color: white;
            }

            QTextEdit {
                background-color: #0a0a0a;
                border: 2px solid #008cff;
                border-radius: 10px;
                padding: 10px;
                font-size: 15px;
            }

            QLineEdit {
                background-color: #101010;
                border: 2px solid #008cff;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #008cff;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #00aaff;
            }
        """)

        self.layout = QVBoxLayout()

        self.title = QLabel("JARVIS")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Arial", 28))

        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)

        self.voice_visualizer = VoiceBars()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Type your command..."
        )
        self.input_box.returnPressed.connect(
            self.send_text_command
        )

        self.buttons_layout = QHBoxLayout()

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(
            self.send_text_command
        )

        self.voice_btn = QPushButton("Voice")
        self.voice_btn.clicked.connect(
            self.voice_command
        )

        self.buttons_layout.addWidget(self.send_btn)
        self.buttons_layout.addWidget(self.voice_btn)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.chat_box)
        self.layout.addWidget(self.voice_visualizer)
        self.layout.addWidget(self.input_box)
        self.layout.addLayout(self.buttons_layout)

        self.setLayout(self.layout)

        self.chat_box.append("Jarvis: Jarvis online.")

    # =========================
    # TEXT COMMAND
    # =========================

    def send_text_command(self):
        command = self.input_box.text().strip()

        if not command:
            return

        self.chat_box.append(f"You: {command}")

        reply = process_command(command)

        self.chat_box.append(f"Jarvis: {reply}")

        speak(reply)

        self.input_box.clear()

    # =========================
    # VOICE COMMAND
    # =========================

    def voice_command(self):
        self.chat_box.append("Listening...")

        command = listen()

        if not command:
            self.chat_box.append(
                "Jarvis: I could not hear you."
            )
            return

        self.chat_box.append(f"You: {command}")

        reply = process_command(command)

        self.chat_box.append(f"Jarvis: {reply}")

        speak(reply)


# =========================
# RUN APP
# =========================

def run_gui():
    app = QApplication(sys.argv)

    window = JarvisGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
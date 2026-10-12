
import sys
import math
import os
import webbrowser
from datetime import datetime

from openai import OpenAI

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


MODEL_NAME = "gpt-5.5"

SYSTEM_INSTRUCTIONS = """
You are ORION, a personal AI desktop assistant.

Personality:
- Be helpful, intelligent, friendly, and clear.
- Explain technical topics in beginner-friendly language.
- Give practical, step-by-step instructions when appropriate.
- Use concise answers unless the user needs more detail.
- You are running inside a Windows desktop application.
- Never claim you performed a computer action unless the application did it.
- You cannot directly inspect the user's computer or files unless a feature
  explicitly provides that information.
"""


class AIWorker(QThread):
    """Runs the online AI request outside the UI thread."""

    answer_ready = Signal(str)
    error_ready = Signal(str)

    def __init__(self, conversation):
        super().__init__()
        self.conversation = conversation

    def run(self):
        try:
            client = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY")
            )

            response = client.responses.create(
                model=MODEL_NAME,
                instructions=SYSTEM_INSTRUCTIONS,
                input=self.conversation,
            )

            answer = response.output_text.strip()

            if not answer:
                answer = "I received an empty response. Please try again."

            self.answer_ready.emit(answer)

        except Exception as error:
            self.error_ready.emit(
                f"AI request failed: {error}"
            )


class Waveform(QWidget):
    """Animated decorative waveform."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.phase = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)

    def animate(self):
        self.phase += 0.10
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()
        center_y = height / 2

        for wave in range(3):
            color = QColor(
                0,
                225 - wave * 25,
                255,
                150 - wave * 35,
            )

            painter.setPen(
                QPen(color, 2 if wave == 0 else 1)
            )

            points = []

            for x in range(width):
                normalized = x / max(width, 1)
                envelope = math.sin(normalized * math.pi) ** 0.7
                frequency = 0.035 + wave * 0.008
                amplitude = (12 + wave * 8) * envelope

                y = (
                    center_y
                    + math.sin(
                        x * frequency + self.phase + wave
                    ) * amplitude
                )

                points.append((x, int(y)))

            for index in range(1, len(points)):
                painter.drawLine(
                    points[index - 1][0],
                    points[index - 1][1],
                    points[index][0],
                    points[index][1],
                )

        painter.end()


class OrionWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ORION | Personal AI")
        self.resize(1000, 700)
        self.setMinimumSize(720, 540)

        self.ai_worker = None
        self.conversation_history = []

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #080d14;
                color: #e6f7ff;
                font-family: 'Segoe UI';
                font-size: 14px;
            }

            QFrame#sidebar {
                background-color: #0b121c;
                border-right: 1px solid #18303e;
            }

            QLabel#brand {
                color: #00e5ff;
                font-size: 27px;
                font-weight: bold;
                letter-spacing: 5px;
            }

            QLabel#subtitle {
                color: #7296a8;
                font-size: 11px;
                letter-spacing: 2px;
            }

            QLabel#status {
                color: #00e5a0;
                font-size: 12px;
            }

            QLabel#message {
                background-color: #101d2a;
                border: 1px solid #1b394a;
                border-radius: 12px;
                padding: 14px;
            }

            QLineEdit {
                background-color: #0e1924;
                border: 1px solid #244657;
                border-radius: 12px;
                padding: 13px;
                color: #ffffff;
            }

            QLineEdit:focus {
                border: 1px solid #00cfe8;
            }

            QLineEdit:disabled {
                color: #68808e;
            }

            QPushButton {
                background-color: #00bfd5;
                color: #031016;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #52edff;
            }

            QPushButton:disabled {
                background-color: #29404b;
                color: #8ba0aa;
            }

            QPushButton#secondary {
                background-color: #132331;
                color: #a9dbea;
                border: 1px solid #254353;
                text-align: left;
                padding: 12px;
            }

            QPushButton#secondary:hover {
                background-color: #1b3445;
                color: #ffffff;
            }

            QFrame#topbar {
                background-color: #0b121c;
                border-bottom: 1px solid #18303e;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                background: #0b121c;
                width: 8px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #244657;
                border-radius: 4px;
                min-height: 25px;
            }
        """)

        self.build_ui()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 28, 18, 20)
        side_layout.setSpacing(14)

        brand = QLabel("ORION")
        brand.setObjectName("brand")

        subtitle = QLabel("PERSONAL AI SYSTEM")
        subtitle.setObjectName("subtitle")

        side_layout.addWidget(brand)
        side_layout.addWidget(subtitle)
        side_layout.addSpacing(25)

        for text in [
            "⌂   Home",
            "◉   Assistant",
            "▤   Tasks",
            "⚙   Settings",
        ]:
            button = QPushButton(text)
            button.setObjectName("secondary")
            side_layout.addWidget(button)

        side_layout.addStretch()

        status = QLabel("●  SYSTEM ONLINE")
        status.setObjectName("status")
        side_layout.addWidget(status)

        version = QLabel("ORION CORE  •  v0.2")
        version.setStyleSheet(
            "color: #536b7a; font-size: 10px;"
        )
        side_layout.addWidget(version)

        # Main panel
        main_panel = QWidget()
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(28, 0, 28, 24)
        main_layout.setSpacing(18)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(64)

        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(0, 0, 0, 0)

        page_title = QLabel("COMMAND CENTER")
        page_title.setStyleSheet(
            "color: #a8d9e8; font-size: 12px;"
            "letter-spacing: 3px;"
        )

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: #00e5ff;")

        top_layout.addWidget(page_title)
        top_layout.addStretch()
        top_layout.addWidget(self.clock_label)

        self.update_clock()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        heading = QLabel("How can I help you?")
        heading.setFont(
            QFont("Segoe UI", 25, QFont.Weight.DemiBold)
        )

        description = QLabel(
            "Your personal workspace. Your commands. Your ORION."
        )
        description.setStyleSheet("color: #7793a4;")

        waveform_title = QLabel("ORION SIGNAL")
        waveform_title.setStyleSheet(
            "color: #00d9f5; font-size: 10px;"
            "letter-spacing: 3px;"
        )

        waveform = Waveform()

        # Scrollable chat
        self.chat_area = QVBoxLayout()
        self.chat_area.setSpacing(12)
        self.chat_area.setContentsMargins(4, 4, 4, 4)
        self.chat_area.addStretch()

        chat_content = QWidget()
        chat_content.setLayout(self.chat_area)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setWidget(chat_content)

        self.add_message(
            "ORION",
            "Systems initialized. Local commands are ready. "
            "Ask me a question to use the AI brain.",
        )

        # Input
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText(
            "Ask ORION anything, or type help..."
        )
        self.command_input.returnPressed.connect(
            self.send_command
        )

        self.send_button = QPushButton("SEND  ➤")
        self.send_button.clicked.connect(self.send_command)

        input_row.addWidget(self.command_input, 1)
        input_row.addWidget(self.send_button)

        main_layout.addWidget(topbar)
        main_layout.addSpacing(10)
        main_layout.addWidget(heading)
        main_layout.addWidget(description)
        main_layout.addWidget(waveform_title)
        main_layout.addWidget(waveform)
        main_layout.addWidget(self.chat_scroll, 1)
        main_layout.addLayout(input_row)

        layout.addWidget(sidebar)
        layout.addWidget(main_panel, 1)

    def update_clock(self):
        self.clock_label.setText(
            datetime.now().strftime("%d %b %Y  |  %H:%M:%S")
        )

    def add_message(self, sender, message):
        label = QLabel(f"{sender}\n{message}")
        label.setObjectName("message")
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        if sender == "YOU":
            label.setStyleSheet("""
                QLabel {
                    background-color: #102b35;
                    border: 1px solid #176477;
                    border-radius: 12px;
                    padding: 14px;
                }
            """)

        self.chat_area.insertWidget(
            self.chat_area.count() - 1,
            label,
        )

        QTimer.singleShot(
            0,
            lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()
            ),
        )

    def clear_conversation(self):
        while self.chat_area.count() > 1:
            item = self.chat_area.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.conversation_history.clear()

        self.add_message(
            "ORION",
            "Conversation cleared. What would you like to discuss?",
        )

    def send_command(self):
        if self.ai_worker is not None:
            return

        command = self.command_input.text().strip()

        if not command:
            return

        self.command_input.clear()
        self.add_message("YOU", command)

        # Always check local commands before using online AI.
        local_answer = self.process_local_command(command)

        if local_answer is not None:
            if local_answer == "__CLEAR__":
                self.clear_conversation()
            else:
                self.add_message("ORION", local_answer)
            return

        # AI needs an API key and an internet connection.
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            self.add_message(
                "ORION",
                "The online AI is not configured yet.\n\n"
                "Set OPENAI_API_KEY in your PowerShell session, "
                "then restart ORION. Local commands still work.",
            )
            return

        # Keep recent conversational context.
        self.conversation_history.append({
            "role": "user",
            "content": command,
        })

        recent_conversation = self.conversation_history[-12:]

        self.command_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("THINKING...")

        self.ai_worker = AIWorker(recent_conversation)
        self.ai_worker.answer_ready.connect(self.on_ai_answer)
        self.ai_worker.error_ready.connect(self.on_ai_error)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.start()

    def on_ai_answer(self, answer):
        self.conversation_history.append({
            "role": "assistant",
            "content": answer,
        })

        self.add_message("ORION", answer)

    def on_ai_error(self, error):
        # Remove the unanswered user message from AI context.
        if (
            self.conversation_history
            and self.conversation_history[-1]["role"] == "user"
        ):
            self.conversation_history.pop()

        self.add_message(
            "ORION",
            error + "\n\n"
            "Check your API key, model access, internet connection, "
            "and API account usage limits, then try again.",
        )

    def on_ai_finished(self):
        self.command_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText("SEND  ➤")
        self.command_input.setFocus()
        self.ai_worker = None

    def process_local_command(self, command):
        text = command.lower().strip()

        if text in {"help", "commands"}:
            return (
                "Available local commands:\n"
                "• help — show this list\n"
                "• time — show the current time\n"
                "• date — show today's date\n"
                "• open google — open Google\n"
                "• open youtube — open YouTube\n"
                "• open github — open GitHub\n"
                "• clear — clear the conversation\n\n"
                "For other questions, I'll use the online AI."
            )

        if text in {"time", "what time is it", "current time"}:
            return (
                "Current time: "
                + datetime.now().strftime("%H:%M:%S")
            )

        if text in {"date", "today's date", "what is today's date"}:
            return (
                "Today's date: "
                + datetime.now().strftime("%d %B %Y")
            )

        websites = {
            "open google": "https://www.google.com",
            "open youtube": "https://www.youtube.com",
            "open github": "https://github.com",
        }

        if text in websites:
            try:
                opened = webbrowser.open(websites[text])

                if opened:
                    return (
                        "Sent the request to open "
                        + text.replace("open ", "").title()
                        + " in your browser."
                    )

                return (
                    "I couldn't confirm that your browser opened. "
                    "Please check your default browser."
                )

            except Exception as error:
                return f"Couldn't open the website: {error}"

        if text in {"clear", "clear chat", "clear conversation"}:
            return "__CLEAR__"

        return None

    def closeEvent(self, event):
        if self.ai_worker is not None and self.ai_worker.isRunning():
            self.ai_worker.wait(3000)

        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = OrionWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

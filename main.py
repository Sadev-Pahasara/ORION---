import sys
import os


import json

import urllib.request

import urllib.error


import math


import time


import webbrowser


from datetime import datetime


import psutil
import speech_recognition as sr


from PySide6.QtCore import Qt, QTimer, QThread, Signal


from PySide6.QtGui import QPainter, QPen, QColor, QFont


from PySide6.QtWidgets import (


    QApplication, QMainWindow, QWidget, QFrame, QLabel,


    QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,


    QScrollArea, QProgressBar, QSizePolicy, QMessageBox


)
# =========================================================# ORION CONFIGURATION# =========================================================
MODEL_NAME = "llama3.2:1b"

OLLAMA_API_URL = "http://localhost:11434/api/chat"


SYSTEM_INSTRUCTIONS = """


You are ORION, a personal AI desktop assistant.


Be helpful, intelligent, friendly, and clear.


Explain technical topics in beginner-friendly language.


Never claim you performed an action unless it actually happened.


You cannot inspect the computer unless the application provides that data.


"""


START_TIME = time.time()


BG = "#070d13"


PANEL = "#0a121a"


PANEL_HEADER = "#0e202c"


BORDER = "#173b4e"


CYAN = "#38dafa"


TEXT = "#c9edf7"


MUTED = "#7299a9"


GREEN = "#32d889"
# =========================================================# ONLINE AI WORKER# =========================================================
class AIWorker(QThread):

    answer_ready = Signal(str)

    error_ready = Signal(str)


    def __init__(self, conversation):

        super().__init__()

        self.conversation = conversation


    def run(self):

        try:

            messages = [

                {"role": "system", "content": SYSTEM_INSTRUCTIONS},

                *self.conversation,

            ]

            payload = json.dumps({

                "model": MODEL_NAME,

                "messages": messages,

                "stream": False,

            }).encode("utf-8")


            request = urllib.request.Request(

                OLLAMA_API_URL,

                data=payload,

                headers={"Content-Type": "application/json"},

                method="POST",

            )


            with urllib.request.urlopen(request, timeout=180) as response:

                result = json.loads(response.read().decode("utf-8"))


            answer = result.get("message", {}).get("content", "").strip()

            self.answer_ready.emit(answer or "I received an empty response.")


        except urllib.error.URLError as error:

            self.error_ready.emit(

                "Could not connect to Ollama. Make sure Ollama is running "

                "and the llama3.2:1b model is installed. Details: " + str(error)

            )

        except Exception as error:

            self.error_ready.emit(str(error))
class VoiceInputWorker(QThread):
    transcript_ready = Signal(str)
    error_ready = Signal(str)

    def run(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)
            try:
                transcript = recognizer.recognize_google(audio, language="en-US")
            except sr.UnknownValueError:
                self.error_ready.emit("I couldn't understand that. Please try speaking clearly.")
                return
            except sr.RequestError as error:
                self.error_ready.emit("Speech recognition needs an internet connection. Details: " + str(error))
                return
            if transcript.strip():
                self.transcript_ready.emit(transcript.strip())
            else:
                self.error_ready.emit("I didn't detect any speech. Please try again.")
        except sr.WaitTimeoutError:
            self.error_ready.emit("I didn't hear anything. Click the microphone and try again.")
        except Exception as error:
            self.error_ready.emit(
                "Microphone could not start. Check that a microphone is connected and allowed in Windows. "
                "Details: " + str(error)
            )


# REUSABLE DASHBOARD COMPONENTS# =========================================================
def make_label(text, size=12, color=TEXT, bold=False):


    label = QLabel(text)


    label.setStyleSheet(


        f"color: {color}; font-size: {size}px;"


        f"font-weight: {'bold' if bold else 'normal'};"


        "background: transparent; border: none;"


    )


    return label


def make_panel(title, icon_text=""):


    panel = QFrame()


    panel.setObjectName("panel")


    layout = QVBoxLayout(panel)


    layout.setContentsMargins(11, 0, 11, 11)


    layout.setSpacing(9)


    header = QFrame()


    header.setObjectName("panelHeader")


    header.setFixedHeight(40)


    header_layout = QHBoxLayout(header)


    header_layout.setContentsMargins(2, 0, 2, 0)


    title_label = make_label(


        f"{icon_text}  {title}", 12, CYAN, True


    )


    header_layout.addWidget(title_label)


    header_layout.addStretch()


    layout.addWidget(header)


    return panel, layout


def make_progress(label_text):


    row = QVBoxLayout()


    row.setSpacing(4)


    line = QHBoxLayout()


    name = make_label(label_text, 10, TEXT)


    value = make_label("--", 10, CYAN, True)


    line.addWidget(name)


    line.addStretch()


    line.addWidget(value)


    bar = QProgressBar()


    bar.setRange(0, 100)


    bar.setValue(0)


    bar.setTextVisible(False)


    bar.setFixedHeight(5)


    row.addLayout(line)


    row.addWidget(bar)


    return row, value, bar


def make_metric(title, value="--"):


    frame = QFrame()


    frame.setObjectName("metric")


    layout = QVBoxLayout(frame)


    layout.setContentsMargins(4, 7, 4, 7)


    layout.setSpacing(3)


    name_label = make_label(title, 9, MUTED)


    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


    value_label = make_label(value, 11, CYAN, True)


    value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


    layout.addWidget(name_label)


    layout.addWidget(value_label)


    return frame, value_label
# =========================================================# ANIMATED ORION CORE# =========================================================
class OrionCore(QWidget):


    def __init__(self):


        super().__init__()


        self.phase = 0.0


        self.setMinimumSize(250, 250)


        self.setSizePolicy(


            QSizePolicy.Policy.Expanding,


            QSizePolicy.Policy.Expanding,


        )


        self.timer = QTimer(self)


        self.timer.timeout.connect(self.animate)


        self.timer.start(35)


    def animate(self):


        self.phase += 0.035


        self.update()


    def paintEvent(self, event):


        painter = QPainter(self)


        painter.setRenderHint(


            QPainter.RenderHint.Antialiasing


        )


        center_x = self.width() / 2


        center_y = self.height() / 2


        radius = min(self.width(), self.height()) * 0.31
# Outer radar rings
        for index in range(4):


            pulse = math.sin(self.phase * 1.5 + index) * 3


            ring_radius = radius * (1.0 + index * 0.22) + pulse


            color = QColor(34, 157, 211, 90 - index * 12)


            painter.setPen(QPen(color, 1.5))


            painter.setBrush(Qt.BrushStyle.NoBrush)


            painter.drawEllipse(


                int(center_x - ring_radius),


                int(center_y - ring_radius),


                int(ring_radius * 2),


                int(ring_radius * 2),


            )
# Main core
        painter.setPen(QPen(QColor("#245a73"), 1.5))


        painter.setBrush(QColor("#102c3c"))


        painter.drawEllipse(


            int(center_x - radius * 0.66),


            int(center_y - radius * 0.66),


            int(radius * 1.32),


            int(radius * 1.32),


        )


        painter.setPen(QPen(QColor("#2d7894"), 1))


        painter.setBrush(QColor("#153c50"))


        painter.drawEllipse(


            int(center_x - radius * 0.48),


            int(center_y - radius * 0.48),


            int(radius * 0.96),


            int(radius * 0.96),


        )
# Animated center signal
        for index in range(5):


            height = 7 + (


                math.sin(self.phase * 3 + index * 0.8) + 1


            ) * 5


            x = center_x + (index - 2) * 10


            painter.setPen(


                QPen(QColor("#08c9f5"), 4,


                     Qt.PenStyle.SolidLine,


                     Qt.PenCapStyle.RoundCap)


            )


            painter.drawLine(


                int(x), int(center_y - height / 2),


                int(x), int(center_y + height / 2),


            )


        painter.end()
# =========================================================# MAIN APPLICATION# =========================================================
class OrionWindow(QMainWindow):


    def __init__(self):


        super().__init__()


        self.setWindowTitle("ORION | AI COMMAND CENTER")


        self.resize(1600, 900)


        self.setMinimumSize(1100, 680)


        self.ai_worker = None
        self.voice_worker = None


        self.conversation_history = []


        self.command_count = 0


        self.session_count = 1


        self.setStyleSheet("""


            QMainWindow, QWidget {


                background-color: #070d13;


                color: #c9edf7;


                font-family: 'Segoe UI';


                font-size: 12px;


            }


            QFrame#panel {


                background-color: #0a121a;


                border: 1px solid #173b4e;


                border-radius: 15px;


            }


            QFrame#panelHeader {


                background-color: #0e202c;


                border-bottom: 1px solid #173b4e;


                border-top-left-radius: 14px;


                border-top-right-radius: 14px;


            }


            QFrame#metric {


                background-color: #0d1922;


                border: none;


                border-radius: 4px;


            }


            QFrame#topbar {


                background-color: #080f16;


                border-bottom: 1px solid #173b4e;


            }


            QLabel#brand {


                color: #45dff8;


                font-size: 22px;


                font-weight: bold;


                letter-spacing: 5px;


            }


            QLabel#online {


                color: #32d889;


                background-color: #102b26;


                border-radius: 10px;


                padding: 5px 10px;


            }


            QLabel#bubble {


                background-color: #112631;


                border: 1px solid #244958;


                border-radius: 15px;


                padding: 13px;


                color: #c9edf7;


            }


            QLineEdit {


                background-color: #08121b;


                color: #d5f5ff;


                border: 1px solid #235267;


                border-radius: 10px;


                padding: 12px;


                selection-background-color: #146b84;


            }


            QLineEdit:focus {


                border: 1px solid #38dafa;


            }


            QPushButton {


                background-color: #112733;


                color: #c9edf7;


                border: 1px solid #235267;


                border-radius: 10px;


                padding: 9px 12px;


            }


            QPushButton:hover {


                background-color: #194052;


                border-color: #38dafa;


            }


            QPushButton:disabled {


                color: #66818d;


                background-color: #101b23;


            }


            QPushButton#send {


                background-color: #246b87;


                border-top-left-radius: 0;


                border-bottom-left-radius: 0;


                font-size: 16px;


            }


            QPushButton#send:hover {


                background-color: #328ca8;


            }


            QProgressBar {


                background-color: #253543;


                border: none;


                border-radius: 2px;


            }


            QProgressBar::chunk {


                background-color: #16c6dc;


                border-radius: 2px;


            }


            QScrollArea {


                background-color: transparent;


                border: none;


            }


            QScrollBar:vertical {


                width: 6px;


                background: #09121a;


            }


            QScrollBar::handle:vertical {


                background: #244657;


                border-radius: 3px;


            }


        """)


        self.build_ui()


        self.stats_timer = QTimer(self)


        self.stats_timer.timeout.connect(self.update_stats)


        self.stats_timer.start(2000)


        self.update_stats()


    def build_ui(self):


        root = QWidget()


        self.setCentralWidget(root)


        root_layout = QVBoxLayout(root)


        root_layout.setContentsMargins(0, 0, 0, 0)


        root_layout.setSpacing(0)
# -------------------------------------------------# TOP BAR# -------------------------------------------------
        topbar = QFrame()


        topbar.setObjectName("topbar")


        topbar.setFixedHeight(64)


        top_layout = QHBoxLayout(topbar)


        top_layout.setContentsMargins(18, 0, 18, 0)


        brand = QLabel("O.R.I.O.N")


        brand.setObjectName("brand")


        online = QLabel("● Online")


        online.setObjectName("online")


        self.top_clock = make_label("", 12, TEXT, True)


        self.system_button = QPushButton("⚙")


        self.system_button.setFixedSize(38, 38)


        self.system_button.clicked.connect(self.show_about)


        top_layout.addWidget(brand)


        top_layout.addSpacing(12)


        top_layout.addWidget(online)


        top_layout.addStretch()


        top_layout.addWidget(self.top_clock)


        top_layout.addSpacing(20)


        top_layout.addWidget(self.system_button)


        root_layout.addWidget(topbar)
# -------------------------------------------------# THREE-COLUMN BODY# -------------------------------------------------
        body = QHBoxLayout()


        body.setContentsMargins(16, 16, 16, 16)


        body.setSpacing(16)


        root_layout.addLayout(body, 1)
# LEFT COLUMN
        left_scroll = QScrollArea()


        left_scroll.setWidgetResizable(True)


        left_scroll.setFixedWidth(340)


        left_content = QWidget()


        left_layout = QVBoxLayout(left_content)


        left_layout.setContentsMargins(0, 0, 0, 0)


        left_layout.setSpacing(13)


        left_scroll.setWidget(left_content)


        self.build_system_panel(left_layout)


        self.build_weather_panel(left_layout)


        self.build_camera_panel(left_layout)


        self.build_uptime_panel(left_layout)


        left_layout.addStretch()


        body.addWidget(left_scroll)
# CENTER COLUMN
        center = QWidget()


        center_layout = QVBoxLayout(center)


        center_layout.setContentsMargins(0, 0, 0, 0)


        center_layout.setSpacing(10)


        center_layout.addStretch(1)


        self.core = OrionCore()


        center_layout.addWidget(self.core, 3)


        core_name = make_label(


            "O.R.I.O.N", 25, TEXT, True


        )


        core_name.setAlignment(Qt.AlignmentFlag.AlignCenter)


        center_layout.addWidget(core_name)


        self.core_status = QLabel("●  SYSTEM READY")


        self.core_status.setAlignment(


            Qt.AlignmentFlag.AlignCenter


        )


        self.core_status.setStyleSheet("""


            QLabel {


                color: #38dafa;


                background-color: #0d1e29;


                border-radius: 12px;


                padding: 10px;


            }


        """)


        center_layout.addWidget(self.core_status, 0,


                                Qt.AlignmentFlag.AlignHCenter)


        center_layout.addStretch(1)


        action_row = QHBoxLayout()


        action_row.setSpacing(18)


        self.camera_action = QPushButton("▣")


        self.mic_action = QPushButton("🎙")


        self.keyboard_action = QPushButton("⌨")


        for button in (


            self.camera_action,


            self.mic_action,


            self.keyboard_action,


        ):


            button.setFixedSize(54, 54)


            button.setStyleSheet("""


                QPushButton {


                    background-color: #09131c;


                    border: 1px solid #20516a;


                    border-radius: 14px;


                    font-size: 20px;


                }


                QPushButton:hover {


                    background-color: #153244;


                    border-color: #38dafa;


                }


            """)


            action_row.addWidget(button)


        self.camera_action.clicked.connect(self.camera_notice)


        self.mic_action.clicked.connect(self.start_voice_input)


        self.keyboard_action.clicked.connect(


            lambda: self.command_input.setFocus()


        )


        center_layout.addLayout(action_row)


        center_layout.addSpacing(5)


        body.addWidget(center, 1)
# RIGHT COLUMN: CONVERSATION
        self.build_conversation_panel(body)


        self.clock_timer = QTimer(self)


        self.clock_timer.timeout.connect(self.update_clock)


        self.clock_timer.start(1000)


        self.update_clock()
# =====================================================# LEFT: SYSTEM STATS# =====================================================
    def build_system_panel(self, parent_layout):


        panel, layout = make_panel("System Stats", "▦")


        self.cpu_row, self.cpu_value, self.cpu_bar = (


            make_progress("CPU Usage")


        )


        self.ram_row, self.ram_value, self.ram_bar = (


            make_progress("RAM Usage")


        )


        layout.addLayout(self.cpu_row)


        layout.addLayout(self.ram_row)


        metrics = QHBoxLayout()


        metrics.setSpacing(6)


        cpu_metric, self.cpu_metric_value = make_metric("CPU")


        mem_metric, self.mem_metric_value = make_metric("Memory")


        disk_metric, self.disk_metric_value = make_metric("Disk")


        for widget in (cpu_metric, mem_metric, disk_metric):


            metrics.addWidget(widget)


        layout.addLayout(metrics)


        parent_layout.addWidget(panel)
# =====================================================# LEFT: WEATHER# =====================================================
    def build_weather_panel(self, parent_layout):


        panel, layout = make_panel("Weather", "☁")


        row = QHBoxLayout()


        weather_info = QVBoxLayout()


        weather_info.setSpacing(4)


        weather_info.addWidget(


            make_label("-- °C", 24, TEXT)


        )


        weather_info.addWidget(


            make_label("Weather not configured", 11, CYAN)


        )


        weather_info.addWidget(


            make_label(


                "Connect a weather service to enable live data.",


                9, MUTED


            )


        )


        weather_icon = make_label("☁", 34, TEXT)


        weather_icon.setAlignment(


            Qt.AlignmentFlag.AlignCenter


        )


        row.addLayout(weather_info, 1)


        row.addWidget(weather_icon)


        layout.addLayout(row)


        metrics = QHBoxLayout()


        for title, value in (


            ("Humidity", "--"),


            ("Wind", "--"),


            ("Feels Like", "--"),


        ):


            widget, _ = make_metric(title, value)


            metrics.addWidget(widget)


        layout.addLayout(metrics)


        parent_layout.addWidget(panel)
# =====================================================# LEFT: CAMERA# =====================================================
    def build_camera_panel(self, parent_layout):


        panel, layout = make_panel("Camera", "▣")


        self.camera_preview = QFrame()


        self.camera_preview.setMinimumHeight(125)


        self.camera_preview.setStyleSheet("""


            QFrame {


                background-color: #080f16;


                border: 1px solid #173b4e;


                border-radius: 7px;


            }


        """)


        preview_layout = QVBoxLayout(self.camera_preview)


        icon = make_label("▰", 28, "#317ca7")


        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)


        camera_text = make_label("Camera Off", 12, "#317ca7")


        camera_text.setAlignment(Qt.AlignmentFlag.AlignCenter)


        preview_layout.addStretch()


        preview_layout.addWidget(icon)


        preview_layout.addWidget(camera_text)


        preview_layout.addStretch()


        layout.addWidget(self.camera_preview)


        note = make_label(


            "Camera integration is not enabled yet.", 9, MUTED


        )


        note.setAlignment(Qt.AlignmentFlag.AlignCenter)


        layout.addWidget(note)


        parent_layout.addWidget(panel)
# =====================================================# LEFT: UPTIME# =====================================================
    def build_uptime_panel(self, parent_layout):


        panel, layout = make_panel("System Uptime", "ⓘ")


        self.uptime_label = make_label("00:00:00", 20, TEXT, True)


        self.uptime_label.setAlignment(


            Qt.AlignmentFlag.AlignRight


        )


        layout.addWidget(


            make_label("System Running For:", 10, MUTED)


        )


        layout.addWidget(self.uptime_label)


        metrics = QHBoxLayout()


        session, _ = make_metric("Session", "1")


        self.command_metric, self.command_metric_value = (


            make_metric("Commands", "0")


        )


        metrics.addWidget(session)


        metrics.addWidget(self.command_metric)


        layout.addLayout(metrics)


        layout.addWidget(


            make_label("System Load", 10, MUTED)


        )


        self.load_bar = QProgressBar()


        self.load_bar.setRange(0, 100)


        self.load_bar.setTextVisible(False)


        self.load_bar.setFixedHeight(5)


        layout.addWidget(self.load_bar)


        self.load_label = make_label("Monitoring", 9, CYAN)


        layout.addWidget(self.load_label)


        parent_layout.addWidget(panel)
# =====================================================# RIGHT: CONVERSATION PANEL# =====================================================
    def build_conversation_panel(self, parent_layout):


        panel = QFrame()


        panel.setObjectName("panel")


        panel.setMinimumWidth(310)


        panel.setMaximumWidth(430)


        panel.setSizePolicy(


            QSizePolicy.Policy.Preferred,


            QSizePolicy.Policy.Expanding,


        )


        layout = QVBoxLayout(panel)


        layout.setContentsMargins(0, 0, 0, 0)


        layout.setSpacing(0)


        header = QFrame()


        header.setObjectName("panelHeader")


        header.setFixedHeight(54)


        header_layout = QHBoxLayout(header)


        header_layout.setContentsMargins(12, 0, 12, 0)


        header_layout.addWidget(


            make_label("Conversation", 15, TEXT, True)


        )


        header_layout.addStretch()


        clear_button = QPushButton("Clear")


        clear_button.clicked.connect(self.clear_conversation)


        header_layout.addWidget(clear_button)


        layout.addWidget(header)


        self.chat_area = QVBoxLayout()


        self.chat_area.setContentsMargins(12, 12, 12, 12)


        self.chat_area.setSpacing(12)


        self.chat_area.addStretch()


        chat_content = QWidget()


        chat_content.setLayout(self.chat_area)


        self.chat_scroll = QScrollArea()


        self.chat_scroll.setWidgetResizable(True)


        self.chat_scroll.setWidget(chat_content)


        layout.addWidget(self.chat_scroll, 1)


        input_container = QWidget()


        input_layout = QHBoxLayout(input_container)


        input_layout.setContentsMargins(12, 12, 12, 12)


        input_layout.setSpacing(0)


        self.command_input = QLineEdit()


        self.command_input.setPlaceholderText("Type a message...")


        self.command_input.returnPressed.connect(


            self.send_command


        )


        self.send_button = QPushButton("➤")


        self.send_button.setObjectName("send")


        self.send_button.setFixedWidth(48)


        self.send_button.clicked.connect(self.send_command)


        input_layout.addWidget(self.command_input, 1)


        input_layout.addWidget(self.send_button)


        layout.addWidget(input_container)


        parent_layout.addWidget(panel)


        self.add_message(


            "ORION",


            "Hello! I'm ORION, your personal assistant. "


            "My local commands and Ollama-powered AI are ready. "


            "Click the microphone button to speak to me.",


        )
# =====================================================# LIVE SYSTEM MONITORING# =====================================================
    def update_clock(self):


        self.top_clock.setText(


            "◷  " + datetime.now().strftime(


                "%I:%M:%S %p   |   %B %d, %Y"


            )


        )


    def update_stats(self):


        try:


            cpu = psutil.cpu_percent(interval=None)


            memory = psutil.virtual_memory()


            disk_root = os.environ.get("SystemDrive", "C:") + "\\\\\\\\"


            disk = psutil.disk_usage(disk_root)


            self.cpu_value.setText(f"{cpu:.0f}%")


            self.cpu_bar.setValue(int(cpu))


            self.ram_value.setText(f"{memory.used / (1024**3):.1f} GB")


            self.ram_bar.setValue(int(memory.percent))


            self.cpu_metric_value.setText(f"{cpu:.0f}%")


            self.mem_metric_value.setText(f"{memory.percent:.0f}%")


            used = disk.used / (1024**3)


            total = disk.total / (1024**3)


            self.disk_metric_value.setText(


                f"{used:.0f}/{total:.0f} GB"


            )


            elapsed = int(time.time() - START_TIME)


            hours, remainder = divmod(elapsed, 3600)


            minutes, seconds = divmod(remainder, 60)


            self.uptime_label.setText(


                f"{hours:02}:{minutes:02}:{seconds:02}"


            )


            self.command_metric_value.setText(


                str(self.command_count)


            )


            load = min(100, int((cpu + memory.percent) / 2))


            self.load_bar.setValue(load)


            self.load_label.setText(


                f"System activity: {load}%"


            )


        except Exception:


            self.load_label.setText(


                "System metrics unavailable"


            )
# =====================================================# CHAT# =====================================================
    def add_message(self, sender, message):


        bubble = QLabel(f"{sender}\n\n{message}")


        bubble.setWordWrap(True)


        bubble.setTextInteractionFlags(


            Qt.TextInteractionFlag.TextSelectableByMouse


        )


        bubble.setMaximumWidth(340)


        bubble.setStyleSheet("""


            QLabel {


                background-color: #112631;


                border: 1px solid #244958;


                border-radius: 15px;


                padding: 13px;


                color: #c9edf7;


            }


        """)


        row = QHBoxLayout()


        row.setContentsMargins(4, 0, 4, 0)


        if sender == "YOU":


            row.addStretch()


            row.addWidget(bubble)


        else:


            row.addWidget(bubble)


            row.addStretch()


        wrapper = QWidget()


        wrapper.setLayout(row)


        self.chat_area.insertWidget(


            self.chat_area.count() - 1,


            wrapper,


        )


        QTimer.singleShot(


            0,


            lambda: self.chat_scroll.verticalScrollBar().setValue(


                self.chat_scroll.verticalScrollBar().maximum()


            ),


        )


    def clear_conversation(self):


        if self.ai_worker is not None:


            return


        while self.chat_area.count() > 1:


            item = self.chat_area.takeAt(0)


            widget = item.widget()


            if widget:


                widget.deleteLater()


        self.conversation_history.clear()


        self.add_message(


            "ORION",


            "Conversation cleared. Ready for your next command.",


        )
# =====================================================# LOCAL COMMANDS + AI# =====================================================
    def send_command(self):


        if self.ai_worker is not None:


            return


        command = self.command_input.text().strip()


        if not command:


            return


        self.command_input.clear()


        self.command_count += 1


        self.update_stats()


        self.add_message("YOU", command)


        local_answer = self.process_local_command(command)


        if local_answer is not None:


            if local_answer == "__CLEAR__":


                self.clear_conversation()


            else:


                self.add_message("ORION", local_answer)


            return


        self.conversation_history.append({


            "role": "user",


            "content": command,


        })


        self.command_input.setEnabled(False)


        self.send_button.setEnabled(False)


        self.send_button.setText("…")


        self.core_status.setText("●  PROCESSING REQUEST")


        self.ai_worker = AIWorker(


            self.conversation_history[-12:]


        )


        self.ai_worker.answer_ready.connect(self.on_ai_answer)


        self.ai_worker.error_ready.connect(self.on_ai_error)


        self.ai_worker.finished.connect(self.on_ai_finished)


        self.ai_worker.start()


    def process_local_command(self, command):


        text = command.lower().strip()


        if text in {"help", "commands"}:


            return (


                "LOCAL COMMANDS\n\n"


                "• help — list commands\n"


                "• time — current time\n"


                "• date — current date\n"


                "• open google — open Google\n"


                "• open youtube — open YouTube\n"


                "• open github — open GitHub\n"


                "• clear — clear conversation\n\n"


                "Other questions are answered by local AI using Ollama."


            )


        if text in {"time", "current time", "what time is it"}:


            return datetime.now().strftime(


                "Current time: %I:%M:%S %p"


            )


        if text in {"date", "today's date", "what is today's date"}:


            return datetime.now().strftime(


                "Today's date: %d %B %Y"


            )


        websites = {


            "open google": "https://www.google.com",


            "open youtube": "https://www.youtube.com",


            "open github": "https://github.com",


        }


        if text in websites:


            try:


                webbrowser.open(websites[text])


                return (


                    "Sent a request to open "


                    + text.replace("open ", "").title()


                    + " in your browser."


                )


            except Exception as error:


                return f"Couldn't open the website: {error}"


        if text in {"clear", "clear chat", "clear conversation"}:


            return "__CLEAR__"


        return None


    def on_ai_answer(self, answer):


        self.conversation_history.append({


            "role": "assistant",


            "content": answer,


        })


        self.add_message("ORION", answer)


    def on_ai_error(self, error):


        if (


            self.conversation_history


            and self.conversation_history[-1]["role"] == "user"


        ):


            self.conversation_history.pop()


        self.add_message(


            "ORION",


            "AI request failed:\n" + error


            + "\n\nCheck that Ollama is running and llama3.2:1b is installed.",


        )


    def on_ai_finished(self):


        self.ai_worker = None


        self.command_input.setEnabled(True)


        self.send_button.setEnabled(True)


        self.send_button.setText("➤")


        self.command_input.setFocus()


        self.core_status.setText("●  SYSTEM READY")
# =====================================================# ACTION BUTTONS# =====================================================
    def camera_notice(self):


        QMessageBox.information(


            self,


            "ORION Camera",


            "Camera support is not implemented yet. "


            "We can add real camera access in a later phase.",


        )


    def start_voice_input(self):
        if self.voice_worker is not None and self.voice_worker.isRunning():
            return
        if self.ai_worker is not None:
            self.add_message("ORION", "Please wait until I finish the current AI response.")
            return

        self.mic_action.setEnabled(False)
        self.core_status.setText("●  LISTENING — SPEAK NOW")
        self.mic_action.setText("…")
        self.voice_worker = VoiceInputWorker()
        self.voice_worker.transcript_ready.connect(self.on_voice_transcript)
        self.voice_worker.error_ready.connect(self.on_voice_error)
        self.voice_worker.finished.connect(self.on_voice_finished)
        self.voice_worker.start()

    def on_voice_transcript(self, transcript):
        self.command_input.setText(transcript)
        self.add_message("ORION", "I heard: " + transcript)
        self.send_command()

    def on_voice_error(self, message):
        self.add_message("ORION", "Voice input: " + message)

    def on_voice_finished(self):
        self.mic_action.setEnabled(True)
        self.mic_action.setText("🎙")
        if self.ai_worker is None:
            self.core_status.setText("●  SYSTEM READY")
        self.voice_worker = None

    def show_about(self):


        QMessageBox.information(


            self,


            "About ORION",


            "ORION Personal AI Assistant\n"


            "Version 0.3\n\n"


            "PySide6 desktop interface\n"


            "Local system monitoring\n"


            "Local commands and Ollama-powered local AI",


        )


    def closeEvent(self, event):


        if self.ai_worker is not None and self.ai_worker.isRunning():
            self.ai_worker.wait(3000)
        if self.voice_worker is not None and self.voice_worker.isRunning():
            self.voice_worker.wait(3000)
        event.accept()
# =========================================================# APPLICATION ENTRY POINT# =========================================================
def main():


    app = QApplication(sys.argv)


    app.setStyle("Fusion")


    window = OrionWindow()


    window.show()


    sys.exit(app.exec())


if __name__ == "__main__":


    main()

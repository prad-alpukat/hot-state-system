import cv2
import numpy as np
from datetime import datetime, timedelta
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap, QPainter, QColor, QPen
import pyqtgraph as pg

from ..utils.config import Config


class CameraWidget(QWidget):
    """Camera view dengan overlay info"""

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()

        self._capture = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_frame)
        self._is_running = False
        self._is_recording = False

        # Recording timer
        self._record_start_time = None
        self._record_timer = QTimer()
        self._record_timer.timeout.connect(self._update_record_time)

        # Overlay data
        self._temperature = 0
        self._set_point = 100
        self._descalation = 150
        self._perlambatan = 50

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header row
        header_layout = QHBoxLayout()
        cam_label = QLabel("Camera")
        cam_label.setFont(QFont("Segoe UI", 11))
        cam_label.setStyleSheet("color: #2C3E50;")

        self._timer_label = QLabel("0:00")
        self._timer_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._timer_label.setStyleSheet("""
            QLabel {
                background-color: #E74C3C;
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
            }
        """)
        self._timer_label.setVisible(False)

        header_layout.addWidget(cam_label)
        header_layout.addStretch()
        header_layout.addWidget(self._timer_label)

        # Video frame
        self._video_frame = QFrame()
        self._video_frame.setMinimumSize(400, 280)
        self._video_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 5px;
            }
        """)

        video_layout = QVBoxLayout(self._video_frame)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setStyleSheet("background: transparent;")
        video_layout.addWidget(self._video_label)

        layout.addLayout(header_layout)
        layout.addWidget(self._video_frame, 1)

        # Show placeholder initially
        self._show_placeholder()

    def start_camera(self):
        if self._is_running:
            return

        self._capture = cv2.VideoCapture(self.config.CAMERA_INDEX)
        if not self._capture.isOpened():
            self._show_placeholder()
            return

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)

        self._is_running = True
        self._timer.start(1000 // self.config.CAMERA_FPS)

    def stop_camera(self):
        self._timer.stop()
        self._is_running = False
        if self._capture:
            self._capture.release()
            self._capture = None
        self._show_placeholder()

    def start_recording(self):
        self._is_recording = True
        self._record_start_time = datetime.now()
        self._timer_label.setVisible(True)
        self._record_timer.start(1000)
        self._update_record_time()

    def stop_recording(self):
        self._is_recording = False
        self._record_timer.stop()
        self._timer_label.setVisible(False)
        self._record_start_time = None

    def _update_record_time(self):
        if self._record_start_time:
            elapsed = datetime.now() - self._record_start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self._timer_label.setText(f"{minutes}:{seconds:02d}")

    def update_overlay_data(self, temp: float, set_point: float, descalation: float, perlambatan: float):
        self._temperature = temp
        self._set_point = set_point
        self._descalation = descalation
        self._perlambatan = perlambatan

    def _update_frame(self):
        if not self._capture or not self._is_running:
            return

        ret, frame = self._capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self._add_overlay(frame)

            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                self._video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._video_label.setPixmap(scaled_pixmap)
        else:
            self._show_placeholder()

    def _add_overlay(self, frame):
        """Add info overlay to frame"""
        h, w = frame.shape[:2]

        # === LEFT OVERLAY - Temperature Info ===
        left_box_x = 15
        left_box_y = h - 130
        left_box_w = 200
        left_box_h = 115

        # Semi-transparent background for left overlay
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (left_box_x, left_box_y),
            (left_box_x + left_box_w, left_box_y + left_box_h),
            (40, 40, 40), -1
        )
        # Add border
        cv2.rectangle(
            overlay,
            (left_box_x, left_box_y),
            (left_box_x + left_box_w, left_box_y + left_box_h),
            (80, 80, 80), 2
        )
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        # Text content
        overlay_data = [
            ("Temperature:", f"{int(self._temperature)}"),
            ("Set point:", f"{int(self._set_point)}"),
            ("Descalation:", f"{int(self._descalation)}"),
            ("Perlambatan:", f"{int(self._perlambatan)}")
        ]

        y_offset = left_box_y + 25
        for label, value in overlay_data:
            # Label (smaller, dimmer)
            cv2.putText(
                frame, label,
                (left_box_x + 10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA
            )
            # Value (brighter, same line)
            cv2.putText(
                frame, value,
                (left_box_x + 120, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA
            )
            y_offset += 25

        # === RIGHT OVERLAY - Date & Duration ===
        right_box_w = 160
        right_box_h = 55
        right_box_x = w - right_box_w - 15
        right_box_y = h - right_box_h - 15

        # Semi-transparent background for right overlay
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (right_box_x, right_box_y),
            (right_box_x + right_box_w, right_box_y + right_box_h),
            (40, 40, 40), -1
        )
        cv2.rectangle(
            overlay,
            (right_box_x, right_box_y),
            (right_box_x + right_box_w, right_box_y + right_box_h),
            (80, 80, 80), 2
        )
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        # Date
        now = datetime.now()
        date_str = now.strftime("%d %B %Y")
        cv2.putText(
            frame, date_str,
            (right_box_x + 10, right_box_y + 22),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA
        )

        # Duration
        if self._record_start_time:
            elapsed = now - self._record_start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            duration_str = f"Duration: {minutes}:{seconds:02d}"
        else:
            duration_str = "Duration: 0:00"

        cv2.putText(
            frame, duration_str,
            (right_box_x + 10, right_box_y + 45),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA
        )

        return frame

    def _show_placeholder(self):
        placeholder = np.zeros((self.config.CAMERA_HEIGHT, self.config.CAMERA_WIDTH, 3), dtype=np.uint8)
        placeholder[:] = (44, 62, 80)

        # Add placeholder overlay
        placeholder = self._add_overlay(placeholder)

        cv2.putText(placeholder, "Camera Preview", (placeholder.shape[1] // 2 - 80, placeholder.shape[0] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        h, w, ch = placeholder.shape
        bytes_per_line = ch * w
        q_image = QImage(placeholder.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        scaled_pixmap = QPixmap.fromImage(q_image).scaled(
            self._video_frame.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._video_label.setPixmap(scaled_pixmap)

    def capture_frame(self) -> QPixmap:
        """Capture current frame as pixmap"""
        return self._video_label.pixmap()


class ActionButton(QPushButton):
    """Action button dengan icon"""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(110, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 9))
        self.setStyleSheet("""
            QPushButton {
                background-color: #4A7C8C;
                color: white;
                border: none;
                border-radius: 8px;
                padding-top: 25px;
            }
            QPushButton:hover {
                background-color: #5A8C9C;
            }
            QPushButton:pressed {
                background-color: #3A6C7C;
            }
        """)


class TemperatureChart(QWidget):
    """Temperature chart untuk History"""

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()

        self._times = deque(maxlen=self.config.CHART_MAX_POINTS)
        self._temps = deque(maxlen=self.config.CHART_MAX_POINTS)
        self._start_time = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        pg.setConfigOptions(antialias=True)

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground('w')
        self._plot_widget.setLabel('left', 'TEMPERATURE')
        self._plot_widget.setLabel('bottom', 'TIME')
        self._plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self._plot_widget.setYRange(0, 400)
        self._plot_widget.setXRange(0, 8)

        # Style the axes
        self._plot_widget.getAxis('left').setStyle(tickFont=QFont("Segoe UI", 8))
        self._plot_widget.getAxis('bottom').setStyle(tickFont=QFont("Segoe UI", 8))

        # Create plot line with orange color
        self._temp_line = self._plot_widget.plot(
            pen=pg.mkPen(color='#E8913A', width=2),
            fillLevel=0,
            brush=pg.mkBrush(232, 145, 58, 50)
        )

        layout.addWidget(self._plot_widget)

    def add_data_point(self, temp: float):
        if self._start_time is None:
            self._start_time = datetime.now()

        elapsed = (datetime.now() - self._start_time).total_seconds() / 60  # In minutes

        self._times.append(elapsed)
        self._temps.append(temp)

        times_arr = np.array(self._times)
        temps_arr = np.array(self._temps)

        self._temp_line.setData(times_arr, temps_arr)

    def clear_data(self):
        self._times.clear()
        self._temps.clear()
        self._start_time = None
        self._temp_line.setData([], [])


class DataVisualizationPanel(QWidget):
    """Panel Data Visualisasi sesuai desain"""

    record_camera_clicked = Signal()
    capture_screen_clicked = Signal()
    save_data_clicked = Signal()
    stop_clear_clicked = Signal()

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.config.COLOR_PANEL_BG};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(35)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config.COLOR_PRIMARY};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        header_label = QLabel("Data visualisasi")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(header_label)

        # Content
        content = QWidget()
        content.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Camera widget
        self._camera = CameraWidget(self.config)

        # History & Action section
        history_label = QLabel("History & Action")
        history_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        history_label.setStyleSheet("color: #2C3E50;")

        # Chart and buttons row
        chart_action_layout = QHBoxLayout()
        chart_action_layout.setSpacing(15)

        # Chart
        self._chart = TemperatureChart(self.config)
        self._chart.setMinimumHeight(180)

        # Action buttons grid
        action_widget = QWidget()
        action_widget.setFixedWidth(240)
        action_layout = QGridLayout(action_widget)
        action_layout.setSpacing(10)
        action_layout.setContentsMargins(0, 0, 0, 0)

        self._record_btn = ActionButton("RECORD CAMERA")
        self._capture_btn = ActionButton("CAPTURE SCREEN")
        self._save_btn = ActionButton("SAVE DATA")
        self._stop_btn = ActionButton("STOP & CLEAR")

        self._record_btn.clicked.connect(self.record_camera_clicked.emit)
        self._capture_btn.clicked.connect(self.capture_screen_clicked.emit)
        self._save_btn.clicked.connect(self.save_data_clicked.emit)
        self._stop_btn.clicked.connect(self.stop_clear_clicked.emit)

        action_layout.addWidget(self._record_btn, 0, 0)
        action_layout.addWidget(self._capture_btn, 0, 1)
        action_layout.addWidget(self._save_btn, 1, 0)
        action_layout.addWidget(self._stop_btn, 1, 1)

        chart_action_layout.addWidget(self._chart, 1)
        chart_action_layout.addWidget(action_widget)

        content_layout.addWidget(self._camera, 1)
        content_layout.addWidget(history_label)
        content_layout.addLayout(chart_action_layout)

        layout.addWidget(header)
        layout.addWidget(content, 1)

    @property
    def camera(self) -> CameraWidget:
        return self._camera

    @property
    def chart(self) -> TemperatureChart:
        return self._chart

    def start_camera(self):
        self._camera.start_camera()

    def stop_camera(self):
        self._camera.stop_camera()

    def add_chart_data(self, temp: float):
        self._chart.add_data_point(temp)

    def clear_chart(self):
        self._chart.clear_data()

    def update_camera_overlay(self, temp: float, set_point: float, descalation: float, perlambatan: float):
        self._camera.update_overlay_data(temp, set_point, descalation, perlambatan)

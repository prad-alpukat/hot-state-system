from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray

from ..utils.config import Config


class OperationMode(Enum):
    HEATING = "HEATING"
    PURGE = "PURGE"
    COOLING = "COOLING"


class ModeButton(QPushButton):
    """Custom button untuk mode selection"""

    def __init__(self, text: str, icon_svg: str, color: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._icon_svg = icon_svg
        self._color = color
        self._is_active = False
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(120, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        border_color = self._color if self._is_active else "transparent"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #4A7C8C;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding-bottom: 8px;
            }}
            QPushButton:hover {{
                background-color: #5A8C9C;
            }}
            QPushButton:pressed {{
                background-color: #3A6C7C;
            }}
        """)

    def set_active(self, active: bool):
        self._is_active = active
        self._update_style()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw indicator bar at bottom
        if self._is_active:
            painter.setBrush(QColor(self._color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(10, self.height() - 6, self.width() - 20, 4, 2, 2)


class SettingSlider(QWidget):
    """Custom slider widget dengan label dan value"""

    value_changed = Signal(float)

    def __init__(self, label: str, min_val: float, max_val: float, default_val: float, parent=None):
        super().__init__(parent)
        self._label = label
        self._min_val = min_val
        self._max_val = max_val
        self._setup_ui(default_val)

    def _setup_ui(self, default_val: float):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)

        # Label
        label = QLabel(self._label)
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: #2C3E50;")

        # Slider row
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(10)

        # Minus button
        minus_btn = QPushButton("-")
        minus_btn.setFixedSize(24, 24)
        minus_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #B0BEC5;
                border-radius: 4px;
                color: #4A90A4;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8F4F8;
            }
        """)
        minus_btn.clicked.connect(self._decrease)

        # Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(int(self._min_val), int(self._max_val))
        self._slider.setValue(int(default_val))
        self._slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #B0BEC5;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4A90A4;
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #5AA0B4;
            }
            QSlider::sub-page:horizontal {
                background: #4A90A4;
                border-radius: 3px;
            }
        """)
        self._slider.valueChanged.connect(self._on_slider_changed)

        # Plus button
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(24, 24)
        plus_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #B0BEC5;
                border-radius: 4px;
                color: #4A90A4;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8F4F8;
            }
        """)
        plus_btn.clicked.connect(self._increase)

        slider_layout.addWidget(minus_btn)
        slider_layout.addWidget(self._slider, 1)
        slider_layout.addWidget(plus_btn)

        # Value label
        self._value_label = QLabel(str(int(default_val)))
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setFont(QFont("Segoe UI", 12))
        self._value_label.setStyleSheet("color: #2C3E50;")

        layout.addWidget(label)
        layout.addLayout(slider_layout)
        layout.addWidget(self._value_label)

    def _on_slider_changed(self, value: int):
        self._value_label.setText(str(value))
        self.value_changed.emit(float(value))

    def _decrease(self):
        self._slider.setValue(self._slider.value() - 10)

    def _increase(self):
        self._slider.setValue(self._slider.value() + 10)

    def value(self) -> float:
        return float(self._slider.value())

    def set_value(self, val: float):
        self._slider.setValue(int(val))


class StatusSettingPanel(QWidget):
    """Panel Status & Setting sesuai desain"""

    settings_applied = Signal(float, float, float)  # set_point, descalation, perlambatan
    mode_changed = Signal(OperationMode)

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()
        self._current_mode = OperationMode.HEATING
        self._current_temp = 25.0
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

        header_label = QLabel("Status & Setting")
        header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(header_label)

        # Content
        content = QWidget()
        content.setStyleSheet("background-color: white; border-radius: 0;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)

        # Current Temperature section
        temp_section = QWidget()
        temp_section.setStyleSheet("background-color: #F5F9FA; border-radius: 5px;")
        temp_layout = QVBoxLayout(temp_section)
        temp_layout.setContentsMargins(10, 10, 10, 10)

        temp_title = QLabel("Current Temperature")
        temp_title.setFont(QFont("Segoe UI", 10))
        temp_title.setStyleSheet("color: #7F8C8D; background: transparent;")

        self._temp_display = QLabel("25°Celcius")
        self._temp_display.setFont(QFont("Segoe UI", 36, QFont.Weight.Light))
        self._temp_display.setStyleSheet("color: #2C3E50; background: transparent;")

        temp_layout.addWidget(temp_title)
        temp_layout.addWidget(self._temp_display)

        # Setting section header
        setting_header = QFrame()
        setting_header.setFixedHeight(30)
        setting_header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config.COLOR_PRIMARY};
                border-radius: 3px;
            }}
        """)
        setting_header_layout = QHBoxLayout(setting_header)
        setting_header_layout.setContentsMargins(10, 0, 10, 0)
        setting_label = QLabel("Setting")
        setting_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        setting_label.setStyleSheet("color: white; background: transparent;")
        setting_header_layout.addWidget(setting_label)

        # Sliders
        self._set_point_slider = SettingSlider(
            "Set point", 0, 400, self.config.DEFAULT_TARGET_TEMP
        )
        self._descalation_slider = SettingSlider(
            "Descalation", 0, 400, self.config.DEFAULT_DESCALATION
        )
        self._perlambatan_slider = SettingSlider(
            "Perlambatan", 0, 200, self.config.DEFAULT_PERLAMBATAN
        )

        # Apply button
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setFixedHeight(35)
        self._apply_btn.setFont(QFont("Segoe UI", 11))
        self._apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.config.COLOR_PRIMARY};
                color: white;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #5AA0B4;
            }}
        """)
        self._apply_btn.clicked.connect(self._on_apply)

        # Mode buttons
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)

        self._heating_btn = ModeButton("HEATING", "", self.config.COLOR_ACCENT_ORANGE)
        self._heating_btn.setText("HEATING")
        self._heating_btn.clicked.connect(lambda: self._set_mode(OperationMode.HEATING))

        self._purge_btn = ModeButton("PURGE", "", self.config.COLOR_ACCENT_GREEN)
        self._purge_btn.setText("PURGE")
        self._purge_btn.clicked.connect(lambda: self._set_mode(OperationMode.PURGE))

        self._cooling_btn = ModeButton("COOLING", "", self.config.COLOR_PRIMARY)
        self._cooling_btn.setText("COOLING")
        self._cooling_btn.clicked.connect(lambda: self._set_mode(OperationMode.COOLING))

        mode_layout.addWidget(self._heating_btn)
        mode_layout.addWidget(self._purge_btn)
        mode_layout.addWidget(self._cooling_btn)

        # Set initial active
        self._heating_btn.set_active(True)

        # Add all to content layout
        content_layout.addWidget(temp_section)
        content_layout.addWidget(setting_header)
        content_layout.addWidget(self._set_point_slider)
        content_layout.addWidget(self._descalation_slider)
        content_layout.addWidget(self._perlambatan_slider)
        content_layout.addWidget(self._apply_btn)
        content_layout.addStretch()
        content_layout.addLayout(mode_layout)

        layout.addWidget(header)
        layout.addWidget(content, 1)

    def _on_apply(self):
        self.settings_applied.emit(
            self._set_point_slider.value(),
            self._descalation_slider.value(),
            self._perlambatan_slider.value()
        )

    def _set_mode(self, mode: OperationMode):
        self._current_mode = mode
        self._heating_btn.set_active(mode == OperationMode.HEATING)
        self._purge_btn.set_active(mode == OperationMode.PURGE)
        self._cooling_btn.set_active(mode == OperationMode.COOLING)
        self.mode_changed.emit(mode)

    def update_temperature(self, temp: float):
        self._current_temp = temp
        self._temp_display.setText(f"{int(temp)}°Celcius")

    def get_settings(self) -> tuple:
        return (
            self._set_point_slider.value(),
            self._descalation_slider.value(),
            self._perlambatan_slider.value()
        )

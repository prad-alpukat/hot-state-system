from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QFont, QScreen, QGuiApplication

from .widgets import StatusSettingPanel, DataVisualizationPanel, OperationMode
from .core import TemperatureSimulator, DataLogger
from .core.simulator import SystemState
from .utils.config import Config


class MainWindow(QMainWindow):
    """Main application window - Hot Stage System"""

    def __init__(self):
        super().__init__()
        self.config = Config()

        # Initialize core components
        self._simulator = TemperatureSimulator(self.config)
        self._logger = DataLogger(self.config)

        # Settings
        self._set_point = self.config.DEFAULT_TARGET_TEMP
        self._descalation = self.config.DEFAULT_DESCALATION
        self._perlambatan = self.config.DEFAULT_PERLAMBATAN

        self._setup_ui()
        self._connect_signals()

        # Start UI update timer
        self._ui_timer = QTimer()
        self._ui_timer.timeout.connect(self._update_ui)
        self._ui_timer.start(self.config.TEMP_UPDATE_INTERVAL_MS)

    def _setup_ui(self):
        self.setWindowTitle("HOT STAGE SYSTEM")
        self.setMinimumSize(1280, 800)

        # Remove default window frame for custom styling
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar / header
        header = self._create_header()

        # Content area
        content = QWidget()
        content.setStyleSheet(f"background-color: {self.config.COLOR_BACKGROUND};")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Left panel - Status & Setting
        self._status_panel = StatusSettingPanel(self.config)
        self._status_panel.setFixedWidth(380)

        # Right panel - Data Visualization
        self._data_panel = DataVisualizationPanel(self.config)

        content_layout.addWidget(self._status_panel)
        content_layout.addWidget(self._data_panel, 1)

        # Footer
        footer = self._create_footer()

        main_layout.addWidget(header)
        main_layout.addWidget(content, 1)
        main_layout.addWidget(footer)

        # Apply global stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.config.COLOR_BACKGROUND};
            }}
        """)

    def _create_header(self) -> QWidget:
        """Create custom header bar"""
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config.COLOR_HEADER};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("HOT STAGE SYSTEM")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")

        layout.addWidget(title)
        layout.addStretch()

        return header

    def _create_footer(self) -> QWidget:
        """Create footer bar"""
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config.COLOR_HEADER};
            }}
        """)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("HOT STAGE SYSTEM")
        title.setFont(QFont("Segoe UI", 10))
        title.setStyleSheet("color: white;")

        version = QLabel("VERSION 2026.1")
        version.setFont(QFont("Segoe UI", 10))
        version.setStyleSheet("color: white;")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(version)

        return footer

    def _connect_signals(self):
        # Simulator signals
        self._simulator.temperature_changed.connect(self._on_temperature_changed)
        self._simulator.state_changed.connect(self._on_state_changed)

        # Status panel signals
        self._status_panel.settings_applied.connect(self._on_settings_applied)
        self._status_panel.mode_changed.connect(self._on_mode_changed)

        # Data panel signals
        self._data_panel.record_camera_clicked.connect(self._on_record_camera)
        self._data_panel.capture_screen_clicked.connect(self._on_capture_screen)
        self._data_panel.save_data_clicked.connect(self._on_save_data)
        self._data_panel.stop_clear_clicked.connect(self._on_stop_clear)

    def _on_temperature_changed(self, temp: float):
        """Handle temperature update from simulator"""
        self._status_panel.update_temperature(temp)
        self._data_panel.add_chart_data(temp)
        self._data_panel.update_camera_overlay(
            temp, self._set_point, self._descalation, self._perlambatan
        )

        # Update logger data
        self._logger.update_data(
            temp,
            self._set_point,
            self._simulator.state
        )

    def _on_state_changed(self, state: SystemState):
        """Handle state change from simulator"""
        pass  # Can add state indicator updates here

    def _on_settings_applied(self, set_point: float, descalation: float, perlambatan: float):
        """Handle settings apply"""
        self._set_point = set_point
        self._descalation = descalation
        self._perlambatan = perlambatan
        self._simulator.target_temp = set_point

        # Start simulation if not running
        if not self._simulator.is_running:
            self._simulator.start()
            self._logger.start_logging()

    def _on_mode_changed(self, mode: OperationMode):
        """Handle mode change"""
        if mode == OperationMode.HEATING:
            self._simulator.start()
        elif mode == OperationMode.COOLING:
            self._simulator.stop()
        elif mode == OperationMode.PURGE:
            # Purge mode - can implement specific behavior
            pass

    def _on_record_camera(self):
        """Handle record camera button"""
        if self._data_panel.camera._is_recording:
            self._data_panel.camera.stop_recording()
        else:
            self._data_panel.camera.start_recording()
            # Also start camera if not running
            if not self._data_panel.camera._is_running:
                self._data_panel.start_camera()

    def _on_capture_screen(self):
        """Handle capture screen button"""
        # Capture the entire window
        screen = QGuiApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(self.winId())

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.config.DATA_DIR / f"capture_{timestamp}.png"
            self.config.DATA_DIR.mkdir(parents=True, exist_ok=True)

            pixmap.save(str(save_path))

            QMessageBox.information(
                self,
                "Capture Saved",
                f"Screenshot saved to:\n{save_path}",
                QMessageBox.StandardButton.Ok
            )

    def _on_save_data(self):
        """Handle save data button"""
        if self._logger.is_logging:
            self._logger.stop_logging()

            if self._logger.current_file:
                QMessageBox.information(
                    self,
                    "Data Saved",
                    f"Data saved to:\n{self._logger.current_file}",
                    QMessageBox.StandardButton.Ok
                )
        else:
            self._logger.start_logging()
            QMessageBox.information(
                self,
                "Logging Started",
                "Data logging has started.",
                QMessageBox.StandardButton.Ok
            )

    def _on_stop_clear(self):
        """Handle stop & clear button"""
        # Stop simulator
        self._simulator.emergency_stop()

        # Stop recording
        self._data_panel.camera.stop_recording()

        # Clear chart
        self._data_panel.clear_chart()

        # Stop logging
        self._logger.stop_logging()

        # Reset simulator
        self._simulator.reset()

    def _update_ui(self):
        """Periodic UI update"""
        self._status_panel.update_temperature(self._simulator.current_temp)

    def showEvent(self, event):
        """Handle window show - start camera"""
        super().showEvent(event)
        # Auto-start camera preview
        QTimer.singleShot(500, self._data_panel.start_camera)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close"""
        self._ui_timer.stop()
        self._simulator.emergency_stop()
        self._logger.stop_logging()
        self._data_panel.stop_camera()
        event.accept()

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer

from ..utils.config import Config
from .simulator import SystemState


class DataLogger(QObject):
    """Logger untuk menyimpan data ke CSV"""

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()

        self._file: Optional[Path] = None
        self._csv_writer = None
        self._file_handle = None
        self._is_logging = False

        self._timer = QTimer()
        self._timer.timeout.connect(self._log_data)

        self._current_temp = 0.0
        self._target_temp = 0.0
        self._state = SystemState.IDLE

        # Pastikan directory data ada
        self.config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def start_logging(self):
        """Mulai logging ke file baru"""
        if self._is_logging:
            return

        # Buat filename dengan timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._file = self.config.DATA_DIR / f"log_{timestamp}.csv"

        # Buka file dan tulis header
        self._file_handle = open(self._file, 'w', newline='', encoding='utf-8')
        self._csv_writer = csv.writer(self._file_handle)
        self._csv_writer.writerow([
            'timestamp',
            'current_temp',
            'target_temp',
            'state'
        ])

        self._is_logging = True
        self._timer.start(self.config.LOG_INTERVAL_MS)

    def stop_logging(self):
        """Stop logging dan tutup file"""
        if not self._is_logging:
            return

        self._timer.stop()
        self._is_logging = False

        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
            self._csv_writer = None

    def update_data(self, current_temp: float, target_temp: float, state: SystemState):
        """Update data yang akan di-log"""
        self._current_temp = current_temp
        self._target_temp = target_temp
        self._state = state

    def _log_data(self):
        """Tulis data ke CSV"""
        if not self._csv_writer:
            return

        self._csv_writer.writerow([
            datetime.now().isoformat(),
            f"{self._current_temp:.2f}",
            f"{self._target_temp:.2f}",
            self._state.value
        ])
        self._file_handle.flush()

    @property
    def is_logging(self) -> bool:
        return self._is_logging

    @property
    def current_file(self) -> Optional[Path]:
        return self._file

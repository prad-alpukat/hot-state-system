#!/usr/bin/env python3
"""
Hot Stage System - Drug Melting Equipment Controller

Aplikasi untuk mengontrol dan memonitor alat peleburan obat untuk riset.
Cross-platform: Windows, macOS, Linux (Ubuntu)
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.app import MainWindow


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Hot Stage System")
    app.setApplicationVersion("2026.1")
    app.setOrganizationName("Research Lab")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

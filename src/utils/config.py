from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Application configuration"""

    # Temperature settings
    MIN_TEMP: float = 0.0
    MAX_TEMP: float = 400.0
    DEFAULT_TARGET_TEMP: float = 100.0
    DEFAULT_DESCALATION: float = 150.0
    DEFAULT_PERLAMBATAN: float = 50.0

    # Simulation settings
    TEMP_UPDATE_INTERVAL_MS: int = 100
    HEATING_RATE: float = 2.0
    COOLING_RATE: float = 1.0
    AMBIENT_TEMP: float = 25.0

    # Chart settings
    CHART_MAX_POINTS: int = 600

    # Camera settings
    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480
    CAMERA_FPS: int = 30

    # Logging settings
    LOG_INTERVAL_MS: int = 1000
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"

    # UI Colors - sesuai desain
    COLOR_PRIMARY: str = "#4A90A4"       # Header bars blue
    COLOR_HEADER: str = "#2D4A5E"        # Dark header/footer
    COLOR_BACKGROUND: str = "#E8F4F8"    # Light blue background
    COLOR_PANEL_BG: str = "#FFFFFF"      # Panel background
    COLOR_BUTTON: str = "#4A7C8C"        # Button blue
    COLOR_BUTTON_HOVER: str = "#5A8C9C"  # Button hover
    COLOR_ACCENT_ORANGE: str = "#E8913A" # Orange accent
    COLOR_ACCENT_GREEN: str = "#4CAF50"  # Green accent
    COLOR_TEXT_DARK: str = "#2C3E50"     # Dark text
    COLOR_TEXT_LIGHT: str = "#FFFFFF"    # Light text
    COLOR_SLIDER_TRACK: str = "#B0BEC5"  # Slider track
    COLOR_SLIDER_HANDLE: str = "#4A90A4" # Slider handle

import random
from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer

from ..utils.config import Config


class SystemState(Enum):
    IDLE = "Idle"
    HEATING = "Heating"
    COOLING = "Cooling"
    MAINTAINING = "Maintaining"
    EMERGENCY_STOP = "Emergency Stop"


class TemperatureSimulator(QObject):
    """Simulator untuk menghasilkan data suhu dummy"""

    temperature_changed = Signal(float)
    state_changed = Signal(SystemState)

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()

        self._current_temp = self.config.AMBIENT_TEMP
        self._target_temp = self.config.DEFAULT_TARGET_TEMP
        self._state = SystemState.IDLE
        self._is_running = False

        self._timer = QTimer()
        self._timer.timeout.connect(self._update_temperature)

    @property
    def current_temp(self) -> float:
        return self._current_temp

    @property
    def target_temp(self) -> float:
        return self._target_temp

    @target_temp.setter
    def target_temp(self, value: float):
        self._target_temp = max(
            self.config.MIN_TEMP,
            min(value, self.config.MAX_TEMP)
        )

    @property
    def state(self) -> SystemState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self):
        """Mulai proses heating"""
        if self._state == SystemState.EMERGENCY_STOP:
            return

        self._is_running = True
        self._update_state()
        self._timer.start(self.config.TEMP_UPDATE_INTERVAL_MS)

    def stop(self):
        """Stop proses, mulai cooling"""
        self._is_running = False
        self._state = SystemState.COOLING
        self.state_changed.emit(self._state)

    def emergency_stop(self):
        """Emergency stop - hentikan semua"""
        self._timer.stop()
        self._is_running = False
        self._state = SystemState.EMERGENCY_STOP
        self.state_changed.emit(self._state)

    def reset(self):
        """Reset dari emergency stop"""
        if self._state == SystemState.EMERGENCY_STOP:
            self._state = SystemState.IDLE
            self.state_changed.emit(self._state)

    def _update_temperature(self):
        """Update suhu berdasarkan state"""
        dt = self.config.TEMP_UPDATE_INTERVAL_MS / 1000.0  # Convert to seconds
        noise = random.uniform(-0.1, 0.1)  # Small noise untuk realisme

        if self._state == SystemState.HEATING:
            # Heating menuju target
            diff = self._target_temp - self._current_temp
            if diff > 0.5:
                self._current_temp += self.config.HEATING_RATE * dt + noise
            else:
                self._state = SystemState.MAINTAINING
                self.state_changed.emit(self._state)

        elif self._state == SystemState.MAINTAINING:
            # Maintain suhu di target (dengan sedikit variasi)
            self._current_temp = self._target_temp + random.uniform(-0.3, 0.3)

        elif self._state == SystemState.COOLING:
            # Cooling menuju ambient
            if self._current_temp > self.config.AMBIENT_TEMP + 0.5:
                self._current_temp -= self.config.COOLING_RATE * dt + noise
            else:
                self._current_temp = self.config.AMBIENT_TEMP
                self._state = SystemState.IDLE
                self._timer.stop()
                self.state_changed.emit(self._state)

        # Clamp temperature
        self._current_temp = max(
            self.config.AMBIENT_TEMP - 1,
            min(self._current_temp, self.config.MAX_TEMP)
        )

        self.temperature_changed.emit(self._current_temp)

    def _update_state(self):
        """Update state berdasarkan kondisi"""
        if not self._is_running:
            if self._current_temp > self.config.AMBIENT_TEMP + 1:
                self._state = SystemState.COOLING
            else:
                self._state = SystemState.IDLE
        else:
            if abs(self._current_temp - self._target_temp) < 0.5:
                self._state = SystemState.MAINTAINING
            elif self._current_temp < self._target_temp:
                self._state = SystemState.HEATING
            else:
                self._state = SystemState.COOLING

        self.state_changed.emit(self._state)

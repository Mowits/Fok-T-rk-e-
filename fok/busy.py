import time


class BusyDetector:
    def __init__(self, window_sec: float = 45.0):
        self.window_sec = float(window_sec)
        self._busy_until = 0.0
        self._last_activity = 0.0

    def mark_activity(self):
        self._last_activity = time.time()

    def mark_busy_for(self, seconds: float):
        now = time.time()
        self._busy_until = max(self._busy_until, now + max(0.0, float(seconds)))
        self._last_activity = now

    def is_busy(self) -> bool:
        now = time.time()
        if now < self._busy_until:
            return True
        return (now - self._last_activity) < self.window_sec

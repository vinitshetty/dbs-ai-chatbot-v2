"""Rate limiting for safety checks"""
import time
from collections import defaultdict, deque
from typing import Optional
from threading import Lock
import os


class SafetyRateLimiter:
    """
    Rate limiter for safety check endpoints.

    Prevents:
    - Brute-force pattern discovery (trying many variants)
    - API abuse
    - DoS attacks on the safety system

    Uses sliding window algorithm with per-IP/user tracking.
    """

    def __init__(self):
        self._lock = Lock()
        self._windows = defaultdict(lambda: deque(maxlen=1000))
        self._violation_logs = defaultdict(lambda: deque(maxlen=1000))

        # Configuration
        self.max_requests_per_minute = int(
            os.getenv("SAFETY_RATE_LIMIT_PER_MIN", "30")
        )
        self.max_requests_per_hour = int(
            os.getenv("SAFETY_RATE_LIMIT_PER_HOUR", "200")
        )
        self.window_seconds = 60  # 1 minute window
        self.hour_window_seconds = 3600  # 1 hour window

    def _get_identifier(self, user_id: Optional[str], ip_address: Optional[str]) -> str:
        """Generate a unique identifier for rate limiting"""
        parts = []
        if user_id:
            parts.append(f"user:{user_id}")
        if ip_address:
            parts.append(f"ip:{ip_address}")

        if not parts:
            return "global"

        return "|".join(parts)

    def is_allowed(self, user_id: Optional[str] = None,
                   ip_address: Optional[str] = None) -> bool:
        """
        Check if a safety check is allowed for this user/IP.

        Args:
            user_id: The user identifier (optional)
            ip_address: The IP address (optional)

        Returns:
            True if request is allowed, False if rate limited
        """
        identifier = self._get_identifier(user_id, ip_address)
        current_time = time.time()

        with self._lock:
            # Clean old entries from minute window
            minute_key = f"{identifier}:min"
            while self._windows[minute_key] and \
                  current_time - self._windows[minute_key][0] > self.window_seconds:
                self._windows[minute_key].popleft()

            # Check minute limit
            if len(self._windows[minute_key]) >= self.max_requests_per_minute:
                return False

            # Clean old entries from hour window
            hour_key = f"{identifier}:hour"
            while self._windows[hour_key] and \
                  current_time - self._windows[hour_key][0] > self.hour_window_seconds:
                self._windows[hour_key].popleft()

            # Check hour limit
            if len(self._windows[hour_key]) >= self.max_requests_per_hour:
                return False

            # Add current request
            self._windows[minute_key].append(current_time)
            self._windows[hour_key].append(current_time)

            return True

    def get_remaining(self, user_id: Optional[str] = None,
                      ip_address: Optional[str] = None) -> dict:
        """
        Get remaining requests for this user/IP.

        Returns:
            Dict with remaining requests for minute and hour windows
        """
        identifier = self._get_identifier(user_id, ip_address)
        current_time = time.time()

        with self._lock:
            minute_key = f"{identifier}:min"
            hour_key = f"{identifier}:hour"

            # Count recent requests in minute window
            minute_count = sum(1 for t in self._windows[minute_key]
                              if current_time - t <= self.window_seconds)

            # Count recent requests in hour window
            hour_count = sum(1 for t in self._windows[hour_key]
                            if current_time - t <= self.hour_window_seconds)

            minute_reset = 0
            hour_reset = 0

            if self._windows[minute_key]:
                oldest_min = self._windows[minute_key][0]
                minute_reset = max(0, int(self.window_seconds - (current_time - oldest_min)))

            if self._windows[hour_key]:
                oldest_hour = self._windows[hour_key][0]
                hour_reset = max(0, int(self.hour_window_seconds - (current_time - oldest_hour)))

            return {
                "minute_remaining": max(0, self.max_requests_per_minute - minute_count),
                "hour_remaining": max(0, self.max_requests_per_hour - hour_count),
                "minute_reset": minute_reset,
                "hour_reset": hour_reset
            }

    def record_violation(self, user_id: Optional[str] = None,
                        ip_address: Optional[str] = None,
                        violation_type: str = "unknown"):
        """
        Record a safety violation for monitoring.

        Args:
            user_id: The user identifier
            ip_address: The IP address
            violation_type: Type of violation detected
        """
        identifier = self._get_identifier(user_id, ip_address)
        timestamp = time.time()

        with self._lock:
            violation_key = f"{identifier}:violations"
            self._windows[violation_key].append(timestamp)
            self._violation_logs[violation_key].append({
                "timestamp": timestamp,
                "type": violation_type
            })

    def get_violation_count(self, user_id: Optional[str] = None,
                           ip_address: Optional[str] = None) -> int:
        """Get the number of violations for a user/IP"""
        identifier = self._get_identifier(user_id, ip_address)
        violation_key = f"{identifier}:violations"
        
        with self._lock:
            return len(self._violation_logs.get(violation_key, []))

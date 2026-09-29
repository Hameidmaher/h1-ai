"""خدمة جمع الإحصائيات."""
from __future__ import annotations
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class Metrics:
    start_time: float = field(default_factory=time.time)
    requests_total: int = 0
    requests_failed: int = 0
    requests_success: int = 0
    endpoint_counts: dict = field(default_factory=lambda: defaultdict(int))
    status_counts: dict = field(default_factory=lambda: defaultdict(int))
    response_times: list = field(default_factory=list)
    chat_messages: int = 0
    chatbot_handled: int = 0
    advisory_handled: int = 0
    agent_handled: int = 0
    emergency_detected: int = 0
    logins_total: int = 0
    logins_failed: int = 0
    _lock: Lock = field(default_factory=Lock)

    def record_request(self, endpoint, status_code, duration_ms):
        with self._lock:
            self.requests_total += 1
            self.endpoint_counts[endpoint] += 1
            self.status_counts[status_code] += 1
            if status_code < 400:
                self.requests_success += 1
            else:
                self.requests_failed += 1
            self.response_times.append(duration_ms)
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]

    def record_handler(self, handler):
        with self._lock:
            self.chat_messages += 1
            if handler == "chatbot":
                self.chatbot_handled += 1
            elif handler == "advisory":
                self.advisory_handled += 1
            elif handler == "advisory_emergency":
                self.emergency_detected += 1
                self.advisory_handled += 1
            elif handler == "agent":
                self.agent_handled += 1

    def record_login(self, success=True):
        with self._lock:
            self.logins_total += 1
            if not success:
                self.logins_failed += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            times = sorted(self.response_times) if self.response_times else [0]
            return {
                "uptime_seconds": round(time.time() - self.start_time, 1),
                "requests": {
                    "total": self.requests_total,
                    "success": self.requests_success,
                    "failed": self.requests_failed,
                    "success_rate": round(
                        self.requests_success / max(self.requests_total, 1) * 100, 2
                    ),
                },
                "response_times_ms": {
                    "avg": round(sum(times) / len(times), 2),
                    "min": round(min(times), 2),
                    "max": round(max(times), 2),
                    "p50": round(times[len(times) // 2], 2),
                    "p95": round(times[int(len(times) * 0.95)], 2),
                    "p99": round(times[int(len(times) * 0.99)], 2),
                },
                "chat": {
                    "total_messages": self.chat_messages,
                    "chatbot": self.chatbot_handled,
                    "advisory": self.advisory_handled,
                    "agent": self.agent_handled,
                    "emergency": self.emergency_detected,
                    "chatbot_pct": round(
                        self.chatbot_handled / max(self.chat_messages, 1) * 100, 1
                    ),
                    "advisory_pct": round(
                        self.advisory_handled / max(self.chat_messages, 1) * 100, 1
                    ),
                    "agent_pct": round(
                        self.agent_handled / max(self.chat_messages, 1) * 100, 1
                    ),
                },
                "auth": {
                    "logins_total": self.logins_total,
                    "logins_failed": self.logins_failed,
                },
                "top_endpoints": sorted(
                    self.endpoint_counts.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "status_codes": dict(self.status_counts),
            }

    def reset(self):
        with self._lock:
            self.requests_total = 0
            self.requests_failed = 0
            self.requests_success = 0
            self.endpoint_counts.clear()
            self.status_counts.clear()
            self.response_times.clear()
            self.chat_messages = 0
            self.chatbot_handled = 0
            self.advisory_handled = 0
            self.agent_handled = 0
            self.emergency_detected = 0
            self.logins_total = 0
            self.logins_failed = 0


metrics = Metrics()

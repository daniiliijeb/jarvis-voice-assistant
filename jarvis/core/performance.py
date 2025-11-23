from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Optional


@contextmanager
def timer(name: str, cb) -> None:
    # Контекстный менеджер-таймер: измеряет время выполнения блока и вызывает колбэк
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        try:
            cb(name, duration_ms)
        except Exception:
            pass


@dataclass
class PerformanceStats:
    # Простая агрегация статистики по именованным таймерам
    durations_ms: Dict[str, float] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)

    def record(self, name: str, duration_ms: float) -> None:
        self.durations_ms[name] = self.durations_ms.get(name, 0.0) + duration_ms
        self.counts[name] = self.counts.get(name, 0) + 1

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        report: Dict[str, Dict[str, float]] = {}
        for k, total in self.durations_ms.items():
            c = self.counts.get(k, 1)
            report[k] = {
                "total_ms": round(total, 2),
                "count": c,
                "avg_ms": round(total / max(c, 1), 2),
            }
        return report


@dataclass
class FPSTracker:
    # Трекер FPS по скользящему окну (для будущего анализа экрана)
    window_s: float = 1.0
    _last_tick: Optional[float] = None
    _frames: int = 0
    fps: float = 0.0

    def tick(self) -> None:
        now = time.perf_counter()
        if self._last_tick is None:
            self._last_tick = now
            return
        self._frames += 1
        elapsed = now - self._last_tick
        if elapsed >= self.window_s:
            self.fps = self._frames / elapsed
            self._frames = 0
            self._last_tick = now



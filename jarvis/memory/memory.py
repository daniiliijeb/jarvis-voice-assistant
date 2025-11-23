from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List


@dataclass
class SimpleMemory:
    max_items: int = 10
    user_history: Deque[str] = field(default_factory=lambda: deque(maxlen=10))
    assistant_history: Deque[str] = field(default_factory=lambda: deque(maxlen=10))

    def add_user(self, text: str) -> None:
        if self.user_history.maxlen != self.max_items:
            self.user_history = deque(self.user_history, maxlen=self.max_items)
        self.user_history.append(text)

    def add_assistant(self, text: str) -> None:
        if self.assistant_history.maxlen != self.max_items:
            self.assistant_history = deque(self.assistant_history, maxlen=self.max_items)
        self.assistant_history.append(text)

    def dump(self) -> dict[str, List[str]]:
        return {
            "user": list(self.user_history),
            "assistant": list(self.assistant_history),
        }

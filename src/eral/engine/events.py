"""Small event bus for gameplay and UI messages."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


EventHandler = Callable[["Event"], None]


@dataclass(slots=True)
class Event:
    """A runtime event emitted by systems."""

    topic: str
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Publish-subscribe event bus used by the runtime."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers[topic].append(handler)

    def publish(self, topic: str, **payload: Any) -> Event:
        event = Event(topic=topic, payload=dict(payload))
        for handler in self._handlers.get(topic, []):
            handler(event)
        return event


from dataclasses import dataclass, field
import uuid


@dataclass
class ContinuousCommand:
    """持续性指令实例"""
    command_key: str
    command_name: str
    actor_ids: list[str]
    target_ids: list[str]
    actor_slots: dict[str, int] = field(default_factory=dict)
    target_slots: dict[str, int] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

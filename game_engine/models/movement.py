from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MovementSession:
    """移动步进会话：统一管理区域内逐点步进与跨区域三阶段流水线状态"""
    is_cross_region: bool = False  # 是否为跨区域长途 (leave)
    phase: int = 1                 # 跨区三阶段 (1: 离境前往entry_node, 2: 大地图通勤, 3: 抵达entry_node)
    src_region: str = ""           # 出发区域
    dst_region: str = ""           # 目标区域
    dst_node: str = ""             # 最终目标节点
    dst_name: str = ""             # 目标地点中文显示名 (如 "食堂大厅")
    remaining_steps: list[dict] = field(default_factory=list) # 路径步进队列 [{'region': ..., 'node': ..., 'time': ...}]
    rush_to_end: bool = False      # 是否开启“直达目的地”免打扰快进
    accumulated_msgs: list[str] = field(default_factory=list) # 途经寒暄日志

    def to_dict(self) -> dict[str, Any]:
        return {
            'is_cross_region': self.is_cross_region,
            'phase': self.phase,
            'src_region': self.src_region,
            'dst_region': self.dst_region,
            'dst_node': self.dst_node,
            'dst_name': self.dst_name,
            'remaining_steps': [dict(s) for s in self.remaining_steps],
            'rush_to_end': self.rush_to_end,
            'accumulated_msgs': list(self.accumulated_msgs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MovementSession | None:
        if not data:
            return None
        return cls(
            is_cross_region=data.get('is_cross_region', False),
            phase=data.get('phase', 1),
            src_region=data.get('src_region', ''),
            dst_region=data.get('dst_region', ''),
            dst_node=data.get('dst_node', ''),
            dst_name=data.get('dst_name', ''),
            remaining_steps=list(data.get('remaining_steps', [])),
            rush_to_end=data.get('rush_to_end', False),
            accumulated_msgs=list(data.get('accumulated_msgs', [])),
        )

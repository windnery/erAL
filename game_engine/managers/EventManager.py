from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.events._base import EVENT_REGISTRY, BaseEvent, PendingChoice, ChoiceOption
from game_engine.events._enums import EventTrigger

if TYPE_CHECKING:
    from world import World
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl


class EventManager:
    """事件调度管理器：管理事件的匹配、优先级排序、触发与持久化状态"""

    def __init__(self, world: World):
        self.world = world
        self.history: set[str] = set()
        self.pending_choice: PendingChoice | None = None

    def _make_key(self, event_id: str, target_id: str | None = None) -> str:
        """生成事件历史唯一键"""
        return f"{event_id}:{target_id}" if target_id else event_id

    def has_triggered(self, event_id: str, target_id: str | None = None) -> bool:
        """检查指定事件是否已触发过"""
        return self._make_key(event_id, target_id) in self.history

    def record_event(self, event_id: str, target_id: str | None = None):
        """记录事件已触发"""
        key = self._make_key(event_id, target_id)
        self.history.add(key)

    def set_pending_choice(
        self,
        event_id: str,
        title: str,
        options: list[ChoiceOption],
        target_id: str | None = None,
        extra_data: dict | None = None
    ):
        """挂起一个玩家选择"""
        self.pending_choice = PendingChoice(
            event_id=event_id,
            target_id=target_id,
            title=title,
            options=options,
            extra_data=extra_data or {}
        )

    def choose_option(self, option_key: str) -> list[str]:
        """处理玩家做出的选择并执行对应事件的 on_choice 分支"""
        if not self.pending_choice:
            return []

        choice = self.pending_choice
        self.pending_choice = None

        from game_engine.commands._context import CommandContext
        ctx = CommandContext(self.world)
        target = self.world.npc_manager.get_npc_by_id(choice.target_id) if choice.target_id else None

        # 查找对应事件并调用 on_choice
        for event_list in EVENT_REGISTRY.values():
            for cls in event_list:
                if cls.event_id == choice.event_id:
                    event = cls()
                    event.on_choice(self.world, ctx, option_key, target=target, **choice.extra_data)
                    return ctx.result()

        return ctx.result()

    def trigger(
        self,
        trigger: EventTrigger,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> list[BaseEvent]:
        """触发指定时机的一组事件

        执行流程：
        1. 筛选匹配当前 trigger 的候选事件；
        2. 过滤专属角色不符或已触发过的单次事件；
        3. 按照 priority 降序排列（同优先级下专属角色事件优先于通用事件）；
        4. 依次执行 can_trigger 判定；
        5. 命中后调用 execute，记录历史；
        6. 若事件标记为 exclusive，则中断后续事件判定直接返回。
        """
        event_classes = EVENT_REGISTRY.get(trigger, [])
        if not event_classes:
            return []

        target_id = target.id if target else None

        # 过滤并排序
        candidates: list[BaseEvent] = []
        for cls in event_classes:
            instance = cls()
            # 角色特化过滤
            if instance.target_chara_id is not None and instance.target_chara_id != target_id:
                continue
            # 单次事件过滤
            if instance.once and self.has_triggered(instance.event_id, target_id):
                continue
            candidates.append(instance)

        # 排序：priority 降序；同优先级时 target_chara_id 存在者优先
        candidates.sort(
            key=lambda e: (e.priority, 1 if e.target_chara_id else 0),
            reverse=True
        )

        triggered_events: list[BaseEvent] = []
        for event in candidates:
            try:
                can = event.can_trigger(self.world, ctx, target=target, **kwargs)
            except Exception:
                can = False

            if can:
                try:
                    success = event.execute(self.world, ctx, target=target, **kwargs)
                except Exception:
                    success = False

                if success:
                    self.record_event(event.event_id, target_id)
                    triggered_events.append(event)
                    if event.exclusive:
                        break

        return triggered_events

    def get_state(self) -> dict:
        """序列化事件管理器状态用于存档"""
        pending_data = None
        if self.pending_choice:
            pending_data = {
                'event_id': self.pending_choice.event_id,
                'target_id': self.pending_choice.target_id,
                'title': self.pending_choice.title,
                'options': [
                    {'key': o.key, 'text': o.text, 'desc': o.desc}
                    for o in self.pending_choice.options
                ],
                'extra_data': self.pending_choice.extra_data,
            }

        return {
            'history': sorted(list(self.history)),
            'pending_choice': pending_data,
        }

    def load_state(self, state: dict | None):
        """从存档数据还原事件历史与挂起选择"""
        if not state:
            self.history = set()
            self.pending_choice = None
            return
        self.history = set(state.get('history', []))
        pending_data = state.get('pending_choice')
        if pending_data:
            self.pending_choice = PendingChoice(
                event_id=pending_data['event_id'],
                target_id=pending_data.get('target_id'),
                title=pending_data.get('title', ''),
                options=[
                    ChoiceOption(key=o['key'], text=o['text'], desc=o.get('desc', ''))
                    for o in pending_data.get('options', [])
                ],
                extra_data=pending_data.get('extra_data', {})
            )
        else:
            self.pending_choice = None

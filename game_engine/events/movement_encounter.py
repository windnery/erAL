from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.events._base import BaseEvent, ChoiceOption, register_event
from game_engine.events._enums import EventTrigger
from game_engine.utils.text_color import c_chara, c_loc

if TYPE_CHECKING:
    from game_engine.commands._context import CommandContext
    from game_engine.models.shipgirl import ShipGirl
    from world import World


@register_event
class MovementEncounterEvent(BaseEvent):
    """中继步进移动途中的偶遇中断事件"""
    event_id: str = "movement_encounter"
    name: str = "路途偶遇"
    trigger: EventTrigger = EventTrigger.MOVE_ENTER
    priority: int = 100
    exclusive: bool = True
    once: bool = False

    def can_trigger(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        session = world.movement_manager.session
        if not session or session.rush_to_end:
            return False

        # 仅在中继节点触发拦截（即后续仍有待走步骤，非最终到达）
        if not session.remaining_steps:
            return False

        cur_region = world.player.location["region"]
        cur_node = world.player.location["node"]
        npcs = [
            sg
            for sg in world.npc_manager.get_npcs_at(cur_region, cur_node)
            if not sg.is_following()
            and not sg.is_sleeping()
            and not sg.cflag.get("unconscious", False)
        ]
        return bool(npcs)

    def execute(
        self,
        world: World,
        ctx: CommandContext,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        cur_region = world.player.location["region"]
        cur_node = world.player.location["node"]
        npcs = [
            sg
            for sg in world.npc_manager.get_npcs_at(cur_region, cur_node)
            if not sg.is_following()
            and not sg.is_sleeping()
            and not sg.cflag.get("unconscious", False)
        ]
        if not npcs:
            return False

        node_name = world.map_manager.get_node_name(cur_region, cur_node)
        names_str = "、".join([c_chara(sg.name, sg.color) for sg in npcs])
        title = f"在【{c_loc(node_name)}】遇到了 {names_str}，是否停下？"
        options = [
            ChoiceOption(key="greet_and_continue", text="打个招呼继续"),
            ChoiceOption(key="stop", text="停下"),
            ChoiceOption(key="continue_to_end", text="继续直到目的地"),
        ]
        world.event_manager.set_pending_choice(
            event_id=self.event_id,
            title=title,
            options=options,
            extra_data={
                "region": cur_region,
                "node": cur_node,
                "npc_ids": [sg.id for sg in npcs],
            },
        )
        return True

    def on_choice(
        self,
        world: World,
        ctx: CommandContext,
        option_key: str,
        target: ShipGirl | None = None,
        **kwargs
    ) -> bool:
        """接收玩家的选择分支并交由 MovementManager 推进"""
        msgs = world.movement_manager.handle_choice(option_key)
        for msg in msgs:
            ctx.say(msg)
        return True

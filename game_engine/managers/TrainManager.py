from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.commands._common import get_entity_by_id, get_name_by_id
from config.chara_config import PLAYER_ID
from game_engine.commands._commands import (
    REGISTER_CMD,
    REGISTER_CAN,
    REGISTER_CMD_NAME,
    REGISTER_CAT,
    REGISTER_MODE,
    REGISTER_CONTINUOUS,
    REGISTER_CONTINUOUS_TEXT,
    REGISTER_ACTOR_SLOTS,
    REGISTER_TARGET_SLOTS,
)
from game_engine.models.continuous_command import ContinuousCommand
from game_engine.models.player import Player

if TYPE_CHECKING:
    from game_engine.managers.NpcManager import NpcManager
    from world import World


class Train:
    def __init__(self, location: dict[str, str], player: Player):
        self.location = location
        self.player = player
        self.actors: list[str] = []  # 调教者
        self.targets: list[str] = []  # 被调教者
        self.participants: list[str] = []  # 会话名册（固定，与两侧列表独立）
        self.initiative: dict[str, int] = {}  # 主导权
        self.leader: str = ''  # 主导者
        self.continuous_commands: list[ContinuousCommand] = []  # 持续中的指令


class TrainManager:
    def __init__(self, npc_manager: NpcManager):
        self.train: Train | None = None  # 表示一整场调教
        self.npc_manager: NpcManager = npc_manager  # npc管理器

    @property
    def world(self) -> World:
        return self.npc_manager.world

    def get_train_commands(self):
        """返回当前调教会话可用的调教指令列表（仅 train_mode=True 的指令）
        与 _get_location_commands 同约定：can 收 world（单参数）
        """
        if not self.train:
            return []
        commands = []
        for key in REGISTER_CMD:
            if not REGISTER_MODE.get(key):
                continue
            can = REGISTER_CAN.get(key)
            if can and not can(self.world):
                continue
            commands.append({
                'key': key,
                'name': REGISTER_CMD_NAME[key],
                'cat': REGISTER_CAT[key],
                'continuous': REGISTER_CONTINUOUS.get(key, False),
                'continuous_active': self.has_continuous_cmd(key),
            })
        return commands

    def has_continuous_cmd(self, command_key: str) -> bool:
        """判断当前训练中是否已有同类持续指令。"""
        return bool(self.train and any(
            cmd.command_key == command_key
            for cmd in self.train.continuous_commands
        ))

    def add_continuous_cmd(self, command_key: str, actor_ids: list[str], target_ids: list[str]) -> ContinuousCommand | None:
        """添加持续性指令并扣减身体槽位"""
        if not self.train:
            return None

        # 每种持续指令只保留一条；当前训练的参与者集合是统一的，重复登记没有额外语义。
        if self.has_continuous_cmd(command_key):
            return None

        command_name = REGISTER_CMD_NAME.get(command_key, command_key)
        actor_slots = REGISTER_ACTOR_SLOTS.get(command_key, {})
        target_slots = REGISTER_TARGET_SLOTS.get(command_key, {})

        # 检查所有调教方槽位
        for aid in actor_ids:
            actor = get_entity_by_id(self.world.player, aid)
            if not actor or not actor.has_body_slots(actor_slots):
                return None

        # 检查所有被调教方槽位
        for tid in target_ids:
            target = get_entity_by_id(self.world.player, tid)
            if not target or not target.has_body_slots(target_slots):
                return None

        # 扣减槽位
        for aid in actor_ids:
            actor = get_entity_by_id(self.world.player, aid)
            if actor:
                actor.consume_body_slots(actor_slots)

        for tid in target_ids:
            target = get_entity_by_id(self.world.player, tid)
            if target:
                target.consume_body_slots(target_slots)

        cmd = ContinuousCommand(
            command_key=command_key,
            command_name=command_name,
            actor_ids=list(actor_ids),
            target_ids=list(target_ids),
            actor_slots=dict(actor_slots),
            target_slots=dict(target_slots),
        )
        self.train.continuous_commands.append(cmd)
        return cmd

    def cancel_continuous_cmd(self, cmd_id: str) -> bool:
        """解除指定的持续性指令并归还身体槽位"""
        if not self.train:
            return False

        cmd = next(
            (c for c in self.train.continuous_commands if c.id == cmd_id), None)
        if not cmd:
            return False

        # 归还调教方槽位
        for aid in cmd.actor_ids:
            actor = get_entity_by_id(self.world.player, aid)
            if actor:
                actor.restore_body_slots(cmd.actor_slots)

        # 归还被调教方槽位
        for tid in cmd.target_ids:
            target = get_entity_by_id(self.world.player, tid)
            if target:
                target.restore_body_slots(cmd.target_slots)

        self.train.continuous_commands.remove(cmd)
        return True

    def clear_all_continuous_cmds(self) -> None:
        """清空所有持续性指令并归还所有槽位"""
        if not self.train:
            return

        for cmd in list(self.train.continuous_commands):
            for aid in cmd.actor_ids:
                actor = get_entity_by_id(self.world.player, aid)
                if actor:
                    actor.restore_body_slots(cmd.actor_slots)
            for tid in cmd.target_ids:
                target = get_entity_by_id(self.world.player, tid)
                if target:
                    target.restore_body_slots(cmd.target_slots)

        self.train.continuous_commands.clear()

    def get_continuous_state(self) -> list[dict]:
        """获取当前持续性指令状态列表供前端渲染"""
        if not self.train:
            return []

        result = []
        for cmd in self.train.continuous_commands:
            actor_names = [get_name_by_id(self.world.player, aid) for aid in cmd.actor_ids]
            target_names = [get_name_by_id(self.world.player, tid) for tid in cmd.target_ids]
            actor_str = "、".join(actor_names)
            target_str = "、".join(target_names)
            template = REGISTER_CONTINUOUS_TEXT.get(cmd.command_key)
            if template:
                text = template.format(actors=actor_str, targets=target_str)
            else:
                target_suffix = f"（目标：{target_str}）" if target_str else ""
                text = f"{actor_str}正在执行{cmd.command_name}{target_suffix}"
            result.append({
                'id': cmd.id,
                'command_key': cmd.command_key,
                'command_name': cmd.command_name,
                'text': text,
            })
        return result

    def new_train(self, participants: list[str], initiative: dict[str, int], leader: str = PLAYER_ID):
        """开始一场调教"""
        # 进入调教模式
        self.world.train_mode = True
        # 初始化一场调教
        region = self.world.player.location['region']
        node = self.world.player.location['node']
        self.train = Train({'region': region, 'node': node}, self.world.player)
        self.train.participants = participants
        # 默认分侧：玩家为调教者，其余为被调教者（之后可经 toggle_actor/toggle_target 动态调整）
        self.train.actors = [p for p in participants if p == PLAYER_ID]
        self.train.targets = [p for p in participants if p != PLAYER_ID]
        self.train.initiative = initiative
        self.train.leader = leader

    def end_train(self):
        """结束一场调教"""
        if not self.train:
            return

        # 清除所有持续性指令并归还槽位
        self.clear_all_continuous_cmds()

        # 解除神志不清状态与重置身体槽位
        for cid in self.train.participants:
            entity = self.world.player if cid == PLAYER_ID else self.npc_manager.shipgirls.get(
                cid)
            if entity is not None:
                entity.cflag['unconscious'] = False
                entity.reset_body_slots()

        self.train = None
        self.world.train_mode = False
        # 调教期间舰娘调度被冻结（忽略睡觉等），结束后按当前时间立即重新调度
        self.npc_manager.update_positions(
            0, self.world.map_manager, self.world.player)

    def _toggle(self, field: str, chara_id: str) -> str:
        """把角色加入/移出某个列表（互斥：加入一侧自动移出另一侧）"""
        if not self.train:
            return '当前没有调教会话'
        if chara_id not in self.train.participants:
            return f'{chara_id}不在本次调教参与者中'
        lists = {'actors': self.train.actors, 'targets': self.train.targets}
        other = {'actors': self.train.targets, 'targets': self.train.actors}
        if chara_id in lists[field]:
            lists[field].remove(chara_id)
            # 若移出侧别，解除涉及该角色的持续性指令
            for cmd in list(self.train.continuous_commands):
                if (field == 'actors' and chara_id in cmd.actor_ids) or (field == 'targets' and chara_id in cmd.target_ids):
                    self.cancel_continuous_cmd(cmd.id)
        else:
            if chara_id in other[field]:
                other[field].remove(chara_id)
                # 若从另一侧移出，解除涉及该角色的持续性指令
                for cmd in list(self.train.continuous_commands):
                    if (field == 'actors' and chara_id in cmd.target_ids) or (field == 'targets' and chara_id in cmd.actor_ids):
                        self.cancel_continuous_cmd(cmd.id)
            lists[field].append(chara_id)
        return ''

    def toggle_actor(self, chara_id: str) -> str:
        """把角色加入/移出调教者列表（互斥）"""
        return self._toggle('actors', chara_id)

    def toggle_target(self, chara_id: str) -> str:
        """把角色加入/移出被调教者列表（互斥）"""
        return self._toggle('targets', chara_id)

    def initiative_cmp(self, chara_id1: str, chara_id2: str):
        """比较两个角色的主导权"""
        if not self.train:
            # 没有调教会话时，默认玩家主导(不过正常流程应该不存在这种情况)
            return True
        return self.train.initiative.get(chara_id1, 0) - self.train.initiative.get(chara_id2, 0) >= 0

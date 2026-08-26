from __future__ import annotations
from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from game_engine.commands._commands import REGISTER_CMD, REGISTER_CAN, REGISTER_CMD_NAME, REGISTER_CAT, \
    REGISTER_MODE
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
            })
        return commands

    def new_train(self, participants: list[str], initiative: dict[str, int], leader: str=PLAYER_ID):
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
        # 解除神志不清状态
        for cid in self.train.participants:
            entity = self.world.player if cid == PLAYER_ID else self.npc_manager.shipgirls.get(cid)
            if entity is not None:
                entity.cflag['unconscious'] = False
        self.train = None
        self.world.train_mode = False
        # 调教期间舰娘调度被冻结（忽略睡觉等），结束后按当前时间立即重新调度
        self.npc_manager.update_positions(0, self.world.map_manager, self.world.player)

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
        else:
            if chara_id in other[field]:
                other[field].remove(chara_id)
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

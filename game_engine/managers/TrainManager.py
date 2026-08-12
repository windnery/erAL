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
        self.initiative: dict[str, int] = {}  # 主导权
        self.leader: str = PLAYER_ID  # 主导者(默认为玩家)

    def do_cmd(self, cmd: str) -> str:
        """执行调教指令（预留，待接入调教执行时设计）"""
        return ''


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

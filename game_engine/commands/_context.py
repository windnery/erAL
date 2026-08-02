from __future__ import annotations
from typing import TYPE_CHECKING

from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World
    from game_engine.models.character import Character


class CommandContext:
    '''指令执行上下文 - 封装指令的通用流程（推进时间、消耗资源、收集消息）'''

    def __init__(self, world: World):
        self.world = world
        self.messages: list[str] = []
        self._npc_events: list[str] = []
        self._exhaustion_mes: str = ''

    def advance_time(self, minutes: int):
        '''推进时间，自动记录 NPC 变动事件'''
        self._npc_events = self.world.advance_time_with_events(minutes)

    def consume(self, stamina: int = 0, energy: int = 0, chara: Character | None = None):
        '''消耗体力和气力（传正数表示消耗量）
        npc: 若指定，NPC 也同步消耗'''
        # 如果传入玩家
        if isinstance(chara, Player):
            if energy:
                self._exhaustion_mes += self.world.change_energy(-energy)
                self.messages.append(f'气力-{energy} ({self.world.player.name})')
            if stamina:
                self._exhaustion_mes += self.world.change_stamina(-stamina)
                self.messages.append(f'体力-{stamina} ({self.world.player.name})')
        elif isinstance(chara, ShipGirl):
            if stamina:
                chara.set_stamina(chara.get_stamina() - stamina)
                self.messages.append(f'体力-{stamina} ({chara.name})')
            if energy:
                chara.set_energy(chara.get_energy() - energy)
                self.messages.append(f'气力-{energy} ({chara.name})')

    def recover(self, stamina: int = 0, energy: int = 0):
        '''恢复体力和气力'''
        if stamina:
            self._exhaustion_mes += self.world.change_stamina(stamina)
        if energy:
            self._exhaustion_mes += self.world.change_energy(energy)

    def say(self, *msgs: str):
        '''添加一条或多条消息'''
        self.messages.extend(msgs)

    def result(self) -> list[str]:
        '''组装最终返回：核心消息 + NPC 变动事件 + 耗尽结算（若有）'''
        mes = self.messages + self._npc_events
        if self._exhaustion_mes:
            mes.append(self._exhaustion_mes)
        return mes

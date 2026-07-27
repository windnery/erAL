from __future__ import annotations
from typing import TYPE_CHECKING

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

    def consume(self, stamina: int = 0, energy: int = 0, npc: Character | None = None):
        '''消耗体力和气力（传正数表示消耗量）
        npc: 若指定，NPC 也同步消耗'''
        if energy:
            self._exhaustion_mes += self.world.change_energy(-energy)
            self.messages.append(f'气力-{energy}')
        if stamina:
            self._exhaustion_mes += self.world.change_stamina(-stamina)
            self.messages.append(f'体力-{stamina}')

        if npc:
            if stamina:
                npc.set_stamina(npc.get_stamina() - stamina)
                self.messages.append(f'{npc.name} 体力-{stamina}')
            if energy:
                npc.set_energy(npc.get_energy() - energy)
                self.messages.append(f'{npc.name} 气力-{energy}')

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

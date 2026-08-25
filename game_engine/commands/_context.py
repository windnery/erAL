from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World
    from game_engine.models.character import Character


class CommandContext:
    """指令执行上下文 - 封装指令的通用流程（推进时间、消耗资源、收集消息）"""

    # 输出分区及顺序（= 前端翻页的块顺序）
    BLOCK_ORDER = ('narrative', 'source', 'stamina', 'palam', 'favor', 'exp', 'ejaculation', 'time')

    def __init__(self, world: World):
        self.world = world
        self.blocks: dict[str, list[str]] = {k: [] for k in self.BLOCK_ORDER}
        self._npc_events: list[str] = []
        self._exhaustion_mes: str = ''

    def advance_time(self, minutes: int):
        """推进时间，自动记录 NPC 变动事件与度过时间消息"""
        self._npc_events = self.world.advance_time_with_events(minutes)
        if minutes > 0:
            self.blocks['time'] = [f'度过了{minutes}分钟']

    def consume(self, stamina: int = 0, energy: int = 0, chara: Character | None = None):
        """消耗体力和气力（传正数表示消耗量）
        npc: 若指定，NPC 也同步消耗"""
        # 如果传入玩家
        if isinstance(chara, Player):
            if energy:
                self._exhaustion_mes += self.world.change_energy(-energy)
                self.blocks['stamina'].append(f'气力-{energy} ({self.world.player.name})')
            if stamina:
                self._exhaustion_mes += self.world.change_stamina(-stamina)
                self.blocks['stamina'].append(f'体力-{stamina} ({self.world.player.name})')
        elif isinstance(chara, ShipGirl):
            if stamina:
                chara.set_stamina(chara.get_stamina() - stamina)
                self.blocks['stamina'].append(f'体力-{stamina} ({chara.name})')
            if energy:
                chara.set_energy(chara.get_energy() - energy)
                self.blocks['stamina'].append(f'气力-{energy} ({chara.name})')
            # 体力归零：回家休息（调教中被强制结束调教）
            if stamina and chara.get_stamina() == 0 and not chara.cflag.get('sleeping') \
                    and not chara.cflag.get('resting'):
                self._exhaustion_mes += '\n'.join(self.world.npc_exhausted(chara))

    def recover(self, stamina: int = 0, energy: int = 0):
        """恢复体力和气力"""
        if stamina:
            self._exhaustion_mes += self.world.change_stamina(stamina)
        if energy:
            self._exhaustion_mes += self.world.change_energy(energy)

    def say(self, *msgs: str, color: str | None = None):
        """添加一条或多条叙事消息（场景描述、口上等）"""
        filtered_msgs = []
        for msg in msgs:
            if isinstance(msg, str) and msg.startswith('度过了') and msg.endswith('分钟'):
                self.blocks['time'] = [msg]
            else:
                filtered_msgs.append(msg)
        if color is None:
            self.blocks['narrative'].extend(filtered_msgs)
        else:
            self.blocks['narrative'].extend(f'[[c:{color}]]{msg}[[/c]]' for msg in filtered_msgs)

    def say_source(self, source: dict[str, int], prefix: str = ''):
        """添加一条source消息（打印 source 信息，自动过滤 0 值项）
        prefix: 可选前缀，如角色名（train 指令用 f'{tar_name} '）
        """
        source_list = [prefix] if prefix else []
        for k, v in source.items():
            if v != 0:
                source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
        self.say_block('source', ' '.join(source_list))

    def say_exp(self, *msgs: str):
        """添加经验消息（经验获得提示）"""
        self.blocks['exp'].extend(msgs)

    def say_block(self, key: str, *msgs: str):
        """向指定分区添加消息"""
        self.blocks[key].extend(msgs)

    def result(self) -> list[str]:
        """组装最终返回：按分区顺序（空块跳过），块间用空字符串分隔；末尾追加 NPC 事件、度过时间消息与耗尽结算"""
        mes: list[str] = []
        for key in ('narrative', 'source', 'stamina', 'palam', 'favor', 'exp', 'ejaculation'):
            block = self.blocks[key]
            if not block:
                continue
            if mes:
                mes.append('')
            mes.extend(block)
        if self._npc_events:
            if mes:
                mes.append('')
            mes.extend(self._npc_events)
        if self.blocks['time']:
            if mes:
                mes.append('')
            mes.extend(self.blocks['time'])
        if self._exhaustion_mes:
            if mes:
                mes.append('')
            mes.append(self._exhaustion_mes)
        return mes

    @property
    def messages(self) -> list[str]:
        """兼容旧接口：所有分区的拍平消息（无空行分隔）"""
        mes: list[str] = []
        for key in self.BLOCK_ORDER:
            mes.extend(self.blocks[key])
        return mes

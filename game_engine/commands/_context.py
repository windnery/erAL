from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from config.attr_defs import ATTR_DEFS
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import color_text

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
        self._consumed: dict[str, dict[str, Any]] = {}
        self._exp_items: dict[tuple[str, str, str], int] = {}
        self._non_matching_exp: list[str] = []

    def advance_time(self, minutes: int):
        """推进时间，自动记录 NPC 变动事件与度过时间消息"""
        self._npc_events = self.world.advance_time_with_events(minutes)
        if minutes > 0:
            self.blocks['time'] = [f'度过了{minutes}分钟']

    def consume(self, stamina: int = 0, energy: int = 0, chara: Character | None = None):
        """消耗体力和气力（传正数表示消耗量）
        npc: 若指定，NPC 也同步消耗"""
        target_chara = chara if chara is not None else self.world.player
        # 如果传入玩家
        if isinstance(target_chara, Player):
            if energy:
                self._exhaustion_mes += self.world.change_energy(-energy)
            if stamina:
                self._exhaustion_mes += self.world.change_stamina(-stamina)
        elif isinstance(target_chara, ShipGirl):
            if stamina:
                target_chara.set_stamina(target_chara.get_stamina() - stamina)
            if energy:
                target_chara.set_energy(target_chara.get_energy() - energy)
            # 调教中目标气力归零：陷入神志不清，主导权强制归0
            if energy and target_chara.get_energy() == 0 and self.world.is_training():
                train = self.world.train_manager.train
                if train and target_chara.id in train.targets and not target_chara.cflag.get('unconscious'):
                    target_chara.cflag['unconscious'] = True
                    train.initiative[target_chara.id] = 0
                    self._exhaustion_mes += f'{target_chara.name}气力0，开始神志不清了……彻底失去了主导权！'
            # 体力归零：回家休息（调教中被强制结束调教）
            if stamina and target_chara.get_stamina() == 0 and not target_chara.cflag.get('sleeping') \
                    and not target_chara.cflag.get('resting'):
                self._exhaustion_mes += '\n'.join(self.world.npc_exhausted(target_chara))

        # 累计消耗并同步更新 stamina block
        cid = target_chara.id
        if cid not in self._consumed:
            self._consumed[cid] = {'name': target_chara.name, 'stamina': 0, 'energy': 0}
        self._consumed[cid]['stamina'] += stamina
        self._consumed[cid]['energy'] += energy
        self._sync_stamina_block()

    def _sync_stamina_block(self):
        lines = []
        # 优先展示玩家，再展示其他角色
        sorted_items = sorted(
            self._consumed.values(),
            key=lambda info: (0 if info['name'] == self.world.player.name else 1)
        )
        for info in sorted_items:
            if info['stamina'] > 0:
                lines.append(f"体力-{info['stamina']} ({info['name']})")
            if info['energy'] > 0:
                lines.append(f"气力-{info['energy']} ({info['name']})")
        self.blocks['stamina'] = lines

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
            self.blocks['narrative'].extend(color_text(msg, color) for msg in filtered_msgs)

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
        """添加经验消息（经验获得提示，自动按角色与经验类型累加合并）"""
        for msg in msgs:
            if not msg:
                continue
            m = re.match(r"^(.+?)\+(\d+)\s*\((.+?)\)(.*)$", msg.strip())
            if m:
                exp_name, delta_str, chara_name, suffix = m.groups()
                key = (exp_name, chara_name, suffix)
                if key not in self._exp_items:
                    self._exp_items[key] = 0
                self._exp_items[key] += int(delta_str)
            else:
                self._non_matching_exp.append(msg)
        self._sync_exp_block()

    def _sync_exp_block(self):
        lines = []
        for (exp_name, chara_name, suffix), total_delta in self._exp_items.items():
            lines.append(f"{exp_name}+{total_delta} ({chara_name}){suffix}")
        self.blocks['exp'] = lines + self._non_matching_exp

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

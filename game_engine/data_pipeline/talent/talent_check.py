from __future__ import  annotations
from typing import TYPE_CHECKING
from game_engine.models.shipgirl import ShipGirl
from config.talent_config import RELATIONSHIP

if TYPE_CHECKING:
    from world import World


def talent_check(world: World, npc: ShipGirl):
    """检查天赋获取和消失"""
    mes = []
    mes.extend(_relationship(world, npc))

    return mes


def _relationship(world: World, npc: ShipGirl):
    """陷落阶段"""
    mes: list[str] = []
    cur = npc.get_talent_value('relationship')
    # 爱(3)已是自动升级最高阶段，后续需通过道具（誓约）提升
    if cur >= 3:
        return mes

    if (
        # 爱
        cur < 3 and
        npc.favor >= RELATIONSHIP['3']['favor'] and
        npc.trust >= RELATIONSHIP['3']['trust'] and
        npc.abl['intimacy_abl'] >= RELATIONSHIP['3']['intimacy_abl']
    ):
        npc.set_talent('relationship', '3')
        mes.append(f'{npc.name}最近似乎更在意{world.player.name}了……{npc.name}和{world.player.name}的关系变成了[[c:#ff6fae]][爱][[/c]]！')
    elif (
        # 喜欢
        cur < 2 and
        npc.favor >= RELATIONSHIP['2']['favor'] and
        npc.trust >= RELATIONSHIP['2']['trust'] and
        npc.abl['intimacy_abl'] >= RELATIONSHIP['2']['intimacy_abl']
    ):
        npc.set_talent('relationship', '2')
        mes.append(f'{npc.name}最近似乎更在意{world.player.name}了……{npc.name}和{world.player.name}的关系变成了[[c:#ff6fae]][喜欢][[/c]]！')
    elif (
        # 友好
        cur < 1 and
        npc.favor >= RELATIONSHIP['1']['favor'] and
        npc.trust >= RELATIONSHIP['1']['trust'] and
        npc.abl['intimacy_abl'] >= RELATIONSHIP['1']['intimacy_abl']
    ):
        npc.set_talent('relationship', '1')
        mes.append(f'{npc.name}最近似乎更在意{world.player.name}了……{npc.name}和{world.player.name}的关系变成了[[c:#ff6fae]][友好][[/c]]！')

    return mes
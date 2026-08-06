from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import new_source, global_can, favor_trust_proc
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from ...data_pipeline.trust.trust_calc import trust_calc
from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定
    if not global_can(world.player, npc):
        return False
    # 工作中
    if npc.is_working():
        return False
    # 约会中
    if npc.is_dating():
        return False
    # 关系未达到友好
    if npc.get_talent_value('relationship') < 1:
        return False
    # 亲密度不足5
    if npc.abl['intimacy_abl'] < 5:
        return False
    # 好感度低于240
    if npc.favor < 240:
        return False

    return True

def able(world: World, npc: ShipGirl):
    """执行成功判定"""
    SUCCESS_SCORE = 24
    score = 0
    # 好感度
    if npc.favor < 300:
        score -= 1
    elif npc.favor < 500:
        score += 2
    elif npc.favor < 700:
        score += 3
    elif npc.favor < 900:
        score += 4
    else:
        score += 6
    # 亲密
    match npc.abl['intimacy_abl']:
        case 6:
            score += 2
        case 7:
            score += 3
        case 8:
            score += 5
        case 9:
            score += 6
        case _:
            score += 7
    # 顺从
    match npc.abl['obedience_abl']:
        case 0:
            score -= 2
        case 1:
            score += 1
        case 2:
            score += 2
        case 3:
            score += 3
        case 4:
            score += 4
        case 5:
            score += 5
        case _:
            score += 6
    # 侍奉精神
    match npc.abl['servant_abl']:
        case 0:
            score += 0
        case 1:
            score += 1
        case 2:
            score += 2
        case 3:
            score += 3
        case 4:
            score += 4
        case 5:
            score += 5
        case _:
            score += 6
    # 会话
    match world.player.abl['talk_abl']:
        case 0:
            score -= 1
        case 1:
            score += 1
        case 2:
            score += 2
        case 3:
            score += 3
        case 4:
            score += 4
        case 5:
            score += 5
        case _:
            score += 6
    # 秘书舰
    if npc == world.npc_manager.secretary_ship:
        score += 4
    # 陷落阶段
    score += npc.get_talent_value('relationship') * 3
    # 恋人
    if npc.has_talent('lover'):
        score += 8
    # 胆怯
    if npc.get_talent_value('courage') == -1:
        score -= 2
    # 叛逆
    if npc.get_talent_value('attitude') == 1:
        score -= 4
    # 傲慢
    if npc.get_talent_value('response') == 1:
        score -= 2
    # 自尊心高
    if npc.get_talent_value('self_respect') == 1:
        score -= 1
    # 傲娇
    if npc.has_talent('tsundere'):
        # 傲娇且关系在喜欢以下
        if npc.get_talent_value('relationship') < 2:
            score -= 2
        else:
            score += 3
    # 冷漠
    if npc.has_talent('indifference'):
        score -= 3
    # 感情缺乏
    if npc.has_talent('emotional_deficiency'):
        score -= 3
    # 开朗的
    if npc.has_talent('bright'):
        score += 2
    # 阴郁的
    if npc.has_talent('morose'):
        score -= 2
    # 难以逾越的底线
    if npc.has_talent('impassable_line') and npc.exp['date_exp'] == 0:
        score -= 5
    # 不在意目光
    if npc.has_talent('not_minding_the_gaze'):
        score += 1
    # 自己爱解放
    score += npc.get_talent_value('self_love') * 2
    # 抵抗
    if npc.has_talent('resistance'):
        score -= 3
    # 羞耻心(-1不知羞耻 1害羞)
    score -= npc.get_talent_value('shame') * 2
    # 献身的
    if npc.has_talent('devoted'):
        score += 3
    # 玩家魅力
    score += world.player.get_talent_value('charm') * 2

    if score >= SUCCESS_SCORE:
        return True
    return False


@register_cmd('invite_date', '约会', '日常', can)
def invite_date(world: World, option: str):
    """约会
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)

    line = npc.get_line('invite_date')
    ctx.say(f'尝试邀请{npc.name}去约会……')
    if line:
        # 有口上
        ctx.say(line.replace('{name}', npc.name))

    if not able(world, npc):
        ctx.say(f'{npc.name}拒绝了你的邀请')
        source: dict[str, int] = new_source({
            'escape_source': 200,
            'disgust_source': 400
        })
    else:
        ctx.say(f'{npc.name}接受了你的邀请！')
        source: dict[str, int] = new_source({
            'love_source': 200,
            'achievement_source': 100,
            'lust_source': 100,
            'obedience_source': 100,
            'happiness_source': 200
        })

    # 通用source修正
    source = common_src_modify(source, npc)
    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
    ctx.say(' '.join(source_list))
    # source->palam
    mes_source, mes_target = palam_calc(source, world.player, npc)
    for mes in mes_source:
        ctx.say(mes)
    for mes in mes_target:
        ctx.say(mes)
    # 更新palam等级
    world.player.update_palam_level()
    npc.update_palam_level()
    # 体力和气力消耗
    energy_cost = 100
    ctx.consume(energy=energy_cost, chara=world.player)
    # 好感和信赖
    favor_trust_proc(source, npc, ctx)

    return ctx.result()

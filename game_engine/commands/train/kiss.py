from __future__ import annotations
from game_engine.commands._common import say_chara_line
from random import randint
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from config.chara_config import PLAYER_ID
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import accumulate_sources, add_attitude_mes, get_revision, train_global_can, new_source, get_name_by_id, get_entity_by_id, \
    favor_trust_proc, source_proc_batch
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World):
    """执行判定"""
    train_manager = world.train_manager
    # 通用判定
    if not train_global_can(train_manager):
        return False
    # 人数判定
    if len(train_manager.train.actors) * 2 < len(train_manager.train.targets):  # type: ignore
        return False

    return True


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    success_score = 15
    mes = ''
    score = 0

    # abl: 欲望
    temp = npc.abl['desire_abl']
    score += temp
    mes = add_attitude_mes(mes, f"欲望({temp})")

    # abl: 侍奉精神
    temp = npc.abl['servant_abl'] * 4
    score += temp
    mes = add_attitude_mes(mes, f"侍奉精神({temp})")

    # TODO: 快乐刻印

    # palam: 欲情
    temp = npc.palam_lv['lust_palam']
    score += temp
    mes = add_attitude_mes(mes, f"欲情({temp})")

    # 害羞
    if npc.get_talent_value('sense_of_shame') > 0:
        score -= 1
        mes = add_attitude_mes(mes, f"害羞(-1)")

    # 污臭耐性
    if npc.get_talent_value('foul_tolerance') < 0:
        score -= 1
        mes = add_attitude_mes(mes, f"污臭敏感(-1)")
    elif npc.get_talent_value('foul_tolerance') > 0:
        score += 1
        mes = add_attitude_mes(mes, f"污臭钝感(1)")

    # 献身的
    if npc.has_talent('devoted'):
        score += 6
        mes = add_attitude_mes(mes, f"献身(6)")

    # 否定快感
    if npc.get_talent_value('denial_of_pleasure') < 0:
        score -= 1
        mes = add_attitude_mes(mes, f"否定快感(-1)")

    if npc.get_talent_value('relationship') > 1:
        temp = 5 * (npc.get_talent_value('relationship') - 1)
        score += temp
        mes = add_attitude_mes(mes, f"{npc.get_talent_name('relationship')}({temp})")

    # TODO: 媚药

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


@register_cmd('kiss', '亲吻', cat='交流', train_mode=True, can=can, needs_target=False)
def kiss(world: World):
    """亲吻"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None:
        return []
    # able判定
    for target_id in train.targets:
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        ok, mes = able(world, chara)
        ctx.say(f'{chara.name} {mes}')
        if not ok:
            train.targets.remove(target_id)
    if len(train.targets) == 0:
        return ctx.result()
    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source({
        'm_pleasure_source': 20,
        'love_source': 100,
        'sex_act_source': 50,
        'submission_source': 10,
        'escape_source': 10,
        'unclean_source': 10,
        'disgust_source': 10
    })

    src_name = get_name_by_id(world.npc_manager, world.player, train.actors[0])
    tar_name = get_name_by_id(
        world.npc_manager, world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}亲吻{tar_name}……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            say_chara_line(chara, ctx, 'kiss')

    # 推进时间
    ctx.advance_time(command_time_data['kiss'])

    sources: dict[str, dict[str, int | float]] = {}
    # 调教者
    for actor_id in train.actors:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.npc_manager, world.player, actor_id)
        # abl: 舌
        temp_sources[actor_id]['m_pleasure_source'] += chara.abl['tongue_abl'] * 4
        temp_sources[actor_id]['love_source'] += chara.abl['tongue_abl'] * 10

        if chara.has_talent('flexible_tongue'):
            temp_sources[actor_id]['m_pleasure_source'] *= 1.5
            temp_sources[actor_id]['love_source'] *= 1.5

        sources.update(temp_sources)

        # exp
        exp_mes.append(exp_calc('tongue_exp', chara))
        exp_mes.append(exp_calc('kiss_exp', chara))

    # 合并调教者产生的source
    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        sources[target_id]['m_pleasure_source'] += get_revision(chara.exp['love_exp'], 200, 100)
        sources[target_id]['sex_act_source'] += get_revision(chara.exp['love_exp'], 50, 100)
        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        source_list = [f'{tar_name} ']
        for k, v in sources[target_id].items():
            if v != 0:
                source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
        ctx.say(' '.join(source_list))

        # 经验处理
        chara.set_exp('tongue_exp', chara.get_exp('tongue_exp') + 1)
        chara.set_exp('kiss_exp', chara.get_exp('kiss_exp') + 1)
        chara.set_exp('m_exp', chara.get_exp('m_exp') + 1)
        if chara.get_talent_value('relationship') > 1:
            # 喜欢
            chara.set_exp('love_exp', chara.get_exp('love_exp') + randint(1, 3))

        # 体力和气力消耗
        ctx.consume(energy=50, chara=chara)

        # exp
        exp_mes.append(exp_calc('tongue_exp', chara))
        exp_mes.append(exp_calc('kiss_exp', chara))

        # 处理好感和信赖
        if target_id != PLAYER_ID:
            favor_trust_proc(sources[target_id], chara, ctx)

    # source转换过程统一处理
    pairs = []
    for actor_id in train.actors:
        actor = get_entity_by_id(world.npc_manager, world.player, actor_id)
        for target_id in train.targets:
            target = get_entity_by_id(
                world.npc_manager, world.player, target_id)
            # 额外处理调教者方的反馈source
            m_pleasure_source = 10 + target.abl['tongue_abl'] * 4
            if target.has_talent('flexible_tongue'):
                m_pleasure_source *= 1.5
            source = common_src_modify({'m_pleasure_source': int(m_pleasure_source)}, actor)
            # 笛卡尔积
            pairs.append((sources[target_id], actor, target))
            # 反馈：target给actor的m_pleasure
            pairs.append((source, target, actor))
    source_proc_batch(pairs, ctx)

    ctx.say(*exp_mes)

    ctx.say(f'度过了{command_time_data["kiss"]}分钟')
    return ctx.result()
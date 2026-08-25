from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

from config.abl_config import ABL_LV
from config.chara_config import PLAYER_ID
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import add_attitude_mes, train_global_can, new_source, get_name_by_id, get_entity_by_id, \
    favor_trust_proc, source_proc_batch
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
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
    success_score = 18
    mes = ''
    score = 0

    # abl: 欲望
    temp = npc.abl['desire_abl'] * 3
    score += temp
    mes = add_attitude_mes(mes, f"欲望({temp})")

    # abl: v感觉
    temp = npc.abl['v_sen_abl'] * 2
    score += temp
    mes = add_attitude_mes(mes, f"V感觉({temp})")

    # abl: 侍奉精神
    temp = npc.abl['servant_abl'] * 4
    score += temp
    mes = add_attitude_mes(mes, f"侍奉精神({temp})")

    # abl: 露出癖
    temp = npc.abl['exposure_abl'] * 3
    score += temp
    mes = add_attitude_mes(mes, f"露出癖({temp})")

    # abl: 自慰中毒
    temp = npc.abl['masturbation_addiction_abl'] * 3
    score += temp
    mes = add_attitude_mes(mes, f"自慰中毒({temp})")

    # 快乐刻印
    temp = npc.mark['pleasure_mark'] * 3
    score += temp
    mes = add_attitude_mes(mes, f"快乐刻印({temp})")

    # palam: 欲情
    temp = npc.palam_lv['lust_palam'] * 2
    score += temp
    mes = add_attitude_mes(mes, f"欲情({temp})")

    # 害羞
    if npc.get_talent_value('sense_of_shame') > 0:
        score -= 2
        mes = add_attitude_mes(mes, f"害羞(-2)")

    # 否定快感
    if npc.get_talent_value('denial_of_pleasure') < 0:
        score -= 5
        mes = add_attitude_mes(mes, f"否定快感(-5)")

    # 处女
    if npc.get_talent_value('virgin') == 1:
        score -= 20
        mes = add_attitude_mes(mes, f"处女(-20)")
    elif npc.exp['v_exp'] < ABL_LV[2]:
        score -= 5
        mes = add_attitude_mes(mes, f"V经验不足(-5)")

    # TODO: 媚药

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


@register_cmd('spread_the_ass', '张开菊穴', cat='爱抚', train_mode=True, can=can, needs_target=False)
def spread_the_ass(world: World):
    """张开菊穴"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    if train is None:
        return []
    # able判定
    failed_targets: list[str] = []
    for target_id in train.targets:
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        ok, mes = able(world, chara)
        ctx.say(f'{chara.name} {mes}')
        if not ok:
            failed_targets.append(target_id)
    # 循环结束后统一移除（避免迭代中修改列表导致元素跳过）
    for target_id in failed_targets:
        train.targets.remove(target_id)
    if len(train.targets) == 0:
        return ctx.result()
    
    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source({
        'a_pleasure_source': 50,
        'achievement_source': 20,
        'fear_source': 120,
        'lubrication_source': 10,
        'exposure_source': 300,
        'submission_source': 450,
        'escape_source': 150,
        'disgust_source': 150
    })

    src_name = get_name_by_id(world.npc_manager, world.player, train.actors[0])
    tar_name = get_name_by_id(world.npc_manager, world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}命令{tar_name}张开肛门……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            say_chara_line(chara, ctx, 'spread_the_ass')

    # 推进时间
    ctx.advance_time(command_time_data['spread_the_ass'])

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in source.items()}
        }
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        # 处女 贞操重视修正
        if chara.get_talent_value('virgin') > 0:
            sources[target_id]['fear_source'] *= 1.2
            sources[target_id]['submission_source'] *= 1.2
            sources[target_id]['disgust_source'] *= 1.2
            sources[target_id]['exposure_source'] += 300
            if chara.get_talent_value('chastity') > 0:
                sources[target_id]['exposure_source'] *= 2
                sources[target_id]['escape_source'] *= 2

        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        ctx.say_source(sources[target_id], prefix=f'{tar_name}')

        # 体力和气力消耗
        ctx.consume(stamina=50, energy=90, chara=chara)

        # exp: 自慰
        if chara.abl['exposure_abl'] >= 3:
            # 露出癖3以上加算自慰经验
            chara.set_exp('masturbation_exp', chara.get_exp(
                'masturbation_exp') + 1)

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
            # 笛卡尔积
            pairs.append((sources[target_id], actor, target))
    source_proc_batch(pairs, ctx)

    return ctx.result()

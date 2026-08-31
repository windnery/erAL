from __future__ import annotations
from game_engine.commands._common import say_chara_line
from random import randint
from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import accumulate_sources, add_attitude_mes, get_revision, train_global_can, new_source, get_name_by_id, get_entity_by_id, \
    check_body_slots
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.models.continuous_command import ContinuousCommand
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
    # 槽位判定
    if not check_body_slots(world, actor_slots={'mouth': 1}, target_slots={'mouth': 1}):
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

    # 快乐刻印
    if npc.id != PLAYER_ID:
        temp = npc.mark['pleasure_mark'] * 3
        score += temp
        mes = add_attitude_mes(mes, f"快乐刻印({temp})")

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
        mes = add_attitude_mes(
            mes, f"{npc.get_talent_name('relationship')}({temp})")

    # TODO: 媚药

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


def continuous_tick(world: World, ctx: CommandContext, cmd: ContinuousCommand):
    # 持续效果
    act_num = len(cmd.actor_ids)
    tar_num = len(cmd.target_ids)
    if act_num == 0 or tar_num == 0:
        return [], []
    num_adjust = float(act_num / tar_num)
    source: dict[str, int] = new_source({
        'm_pleasure_source': 10,
        'love_source': 50,
        'sex_act_source': 25,
        'submission_source': 5,
        'escape_source': 5,
        'unclean_source': 5,
        'disgust_source': 5
    })
    feedback_source: dict[str, int] = new_source({
        'm_pleasure_source': 5,
    })

    sources: dict[str, dict[str, int | float]] = {}
    exp_mes = []
    # 调教者
    for actor_id in cmd.actor_ids:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        temp_sources[actor_id]['m_pleasure_source'] += int(
            chara.abl['tongue_abl'] * 2)
        temp_sources[actor_id]['love_source'] += int(
            chara.abl['tongue_abl'] * 5)

        if chara.has_talent('flexible_tongue'):
            temp_sources[actor_id]['m_pleasure_source'] *= 1.5
            temp_sources[actor_id]['love_source'] *= 1.5

        sources.update(temp_sources)
        exp_mes.append(exp_calc('tongue_exp', chara))
        exp_mes.append(exp_calc('kiss_exp', chara))

    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in cmd.target_ids:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)
        sources[target_id]['m_pleasure_source'] += int(
            get_revision(chara.exp['love_exp'], 200, 100) * 0.5)
        sources[target_id]['sex_act_source'] += int(
            get_revision(chara.exp['love_exp'], 50, 100) * 0.5)
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 50% 气力消耗
        ctx.consume(energy=25, chara=chara)

        chara.set_exp('tongue_exp', chara.get_exp('tongue_exp') + 1)
        chara.set_exp('kiss_exp', chara.get_exp('kiss_exp') + 1)
        chara.set_exp('m_exp', chara.get_exp('m_exp') + 1)
        if chara.get_talent_value('relationship') > 1:
            chara.set_exp('love_exp', chara.get_exp(
                'love_exp') + randint(1, 3))

        exp_mes.append(exp_calc('tongue_exp', chara))
        exp_mes.append(exp_calc('kiss_exp', chara))

    pairs = []
    for actor_id in cmd.actor_ids:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in cmd.target_ids:
            target = get_entity_by_id(world.player, target_id)
            feedback = feedback_source.copy()
            feedback['m_pleasure_source'] += int(target.abl['tongue_abl'] * 2)
            if target.has_talent('flexible_tongue'):
                feedback['m_pleasure_source'] *= 1.5
            source_actor = common_src_modify(feedback, actor)
            pairs.append((sources[target_id], actor, target))
            pairs.append((source_actor, target, actor))

    return pairs, exp_mes


@register_cmd(
    'kiss',
    '亲吻',
    cat='交流',
    train_mode=True,
    can=can,
    needs_target=False,
    continuous=True,
    continuous_text='{actors}正在亲吻{targets}',
    actor_slots={'mouth': 1},
    target_slots={'mouth': 1},
    continuous_tick=continuous_tick,
)
def kiss(world: World):
    """亲吻"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None:
        return []
    # able判定
    failed_targets: list[str] = []
    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        ok, mes = able(world, chara)
        ctx.say(f'{chara.name} {mes}')
        if not ok:
            failed_targets.append(target_id)
    # 循环结束后统一移除（避免迭代中修改列表导致元素跳过）
    for target_id in failed_targets:
        train.targets.remove(target_id)
    if len(train.targets) == 0:
        return ctx.result()

    new_cmd_id = None
    if getattr(world, 'is_current_cmd_continuous', False):
        new_cmd = world.train_manager.add_continuous_cmd(
            'kiss', list(train.actors), list(train.targets))
        if new_cmd:
            new_cmd_id = new_cmd.id

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
    feedback_source: dict[str, int] = new_source({
        'm_pleasure_source': 10,
    })

    src_name = get_name_by_id(world.player, train.actors[0])
    tar_name = get_name_by_id(world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}亲吻{tar_name}……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        if isinstance(chara, ShipGirl):
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
        chara = get_entity_by_id(world.player, actor_id)
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
        chara = get_entity_by_id(world.player, target_id)
        sources[target_id]['m_pleasure_source'] += get_revision(
            chara.exp['love_exp'], 200, 100)
        sources[target_id]['sex_act_source'] += get_revision(
            chara.exp['love_exp'], 50, 100)
        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 经验处理
        chara.set_exp('tongue_exp', chara.get_exp('tongue_exp') + 1)
        chara.set_exp('kiss_exp', chara.get_exp('kiss_exp') + 1)
        chara.set_exp('m_exp', chara.get_exp('m_exp') + 1)
        if chara.get_talent_value('relationship') > 1:
            # 喜欢
            chara.set_exp('love_exp', chara.get_exp(
                'love_exp') + randint(1, 3))

        # 体力和气力消耗
        ctx.consume(energy=50, chara=chara)

        # exp
        exp_mes.append(exp_calc('tongue_exp', chara))
        exp_mes.append(exp_calc('kiss_exp', chara))

    # 构建主指令 pairs
    pairs = []
    for actor_id in train.actors:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in train.targets:
            target = get_entity_by_id(world.player, target_id)
            feedback = feedback_source.copy()
            feedback['m_pleasure_source'] += target.abl['tongue_abl'] * 4
            if target.has_talent('flexible_tongue'):
                feedback['m_pleasure_source'] *= 1.5
            source_actor = common_src_modify(feedback, actor)
            pairs.append((sources[target_id], actor, target))
            pairs.append((source_actor, target, actor))

    # 统一回合结算管道
    from game_engine.commands._common import process_train_turn
    process_train_turn(world, ctx, pairs, exp_mes, new_cmd_id=new_cmd_id)

    return ctx.result()

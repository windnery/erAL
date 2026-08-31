from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import pain_check_v, train_global_can, new_source, get_name_by_id, get_entity_by_id, \
    accumulate_sources, check_body_slots
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.models.continuous_command import ContinuousCommand

if TYPE_CHECKING:
    from world import World


def can(world: World):
    """执行判定"""
    train_manager = world.train_manager
    # 通用判定
    if not train_global_can(train_manager):
        return False
    # 玩家不能被调教（男性）
    if PLAYER_ID in train_manager.train.targets:  # type: ignore
        return False
    # 槽位判定（调教方1手，被调教方1阴道）
    if not check_body_slots(world, actor_slots={'hands': 1}, target_slots={'vagina': 1}):
        return False

    return True


def continuous_tick(world: World, ctx: CommandContext, cmd: ContinuousCommand):
    # 持续效果
    act_num = len(cmd.actor_ids)
    tar_num = len(cmd.target_ids)
    if act_num == 0 or tar_num == 0:
        return [], []
    num_adjust = float(act_num / tar_num)
    source: dict[str, int] = new_source({
        'v_pleasure_source': 60,
        'pain_source': 7,
        'exposure_source': 5,
        'escape_source': 10,
        'disgust_source': 10
    })

    sources: dict[str, dict[str, int | float]] = {}
    exp_mes = []
    # 调教者
    for actor_id in cmd.actor_ids:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        temp_sources[actor_id]['v_pleasure_source'] += int(
            chara.abl['finger_abl'] * 2.5)

        if chara.has_talent('flexible_fingers'):
            temp_sources[actor_id]['v_pleasure_source'] *= 1.5

        sources.update(temp_sources)
        exp_mes.append(exp_calc('finger_exp', chara))

    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in cmd.target_ids:
        sources: dict[str, dict[str, int | float]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)
        if chara.get_talent_value('virgin') > 0:
            sources[target_id]['pain_source'] *= 1.5
            sources[target_id]['v_pleasure_source'] *= 0.5
            sources[target_id]['exposure_source'] *= 1.5
            sources[target_id]['escape_source'] *= 1.2
            sources[target_id]['disgust_source'] *= 1.2

        pain_check_v(sources[target_id], chara)
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 50% 消耗
        ctx.consume(stamina=15, energy=40, chara=chara)

        exp_mes.append(exp_calc('v_exp', chara))

    pairs = []
    for actor_id in cmd.actor_ids:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in cmd.target_ids:
            target = get_entity_by_id(world.player, target_id)
            pairs.append((sources[target_id], actor, target))

    return pairs, exp_mes


@register_cmd(
    'finger_insert',
    '指插入',
    cat='爱抚',
    train_mode=True,
    can=can,
    needs_target=False,
    continuous=True,
    continuous_text='{actors}正在用手指插入{targets}',
    actor_slots={'hands': 1},
    target_slots={'vagina': 1},
    continuous_tick=continuous_tick,
)
def finger_insert(world: World):
    """指插入"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None:
        return []

    new_cmd_id = None
    if getattr(world, 'is_current_cmd_continuous', False):
        new_cmd = world.train_manager.add_continuous_cmd(
            'finger_insert', list(train.actors), list(train.targets))
        if new_cmd:
            new_cmd_id = new_cmd.id

    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source({
        'v_pleasure_source': 120,
        'pain_source': 15,
        'exposure_source': 10,
        'escape_source': 20,
        'disgust_source': 20
    })

    src_name = get_name_by_id(world.player, train.actors[0])
    tar_name = get_name_by_id(world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}把手指插入{tar_name}的蜜唇中来回搅弄着……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            say_chara_line(chara, ctx, 'finger_insert')

    # 推进时间
    ctx.advance_time(command_time_data['finger_insert'])

    sources: dict[str, dict[str, int | float]] = {}
    # 调教者
    for actor_id in train.actors:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        # abl: 指
        temp_sources[actor_id]['v_pleasure_source'] += chara.abl['finger_abl'] * 5

        if chara.has_talent('flexible_fingers'):
            temp_sources[actor_id]['v_pleasure_source'] *= 1.5

        sources.update(temp_sources)

        # exp
        exp_mes.append(exp_calc('finger_exp', chara))

    # 合并调教者产生的source
    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int | float]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)
        # 处女修正
        if chara.get_talent_value('virgin') > 0:
            sources[target_id]['pain_source'] *= 1.5
            sources[target_id]['v_pleasure_source'] *= 0.5
            sources[target_id]['exposure_source'] *= 1.5
            sources[target_id]['escape_source'] *= 1.2
            sources[target_id]['disgust_source'] *= 1.2
        # v苦痛判定
        pain_check_v(sources[target_id], chara)
        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 体力和气力消耗
        ctx.consume(stamina=30, energy=80, chara=chara)

        # v exp
        exp_mes.append(exp_calc('v_exp', chara))

    # 构建主指令 pairs
    pairs = []
    for actor_id in train.actors:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in train.targets:
            target = get_entity_by_id(world.player, target_id)
            pairs.append((sources[target_id], actor, target))

    # 统一回合结算管道
    from game_engine.commands._common import process_train_turn
    process_train_turn(world, ctx, pairs, exp_mes, new_cmd_id=new_cmd_id)

    return ctx.result()

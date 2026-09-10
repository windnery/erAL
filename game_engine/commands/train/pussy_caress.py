from __future__ import annotations

from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from data.time.time_data import COMMAND_TIME_DATA
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import (
    accumulate_sources,
    check_body_slots,
    get_entity_by_id,
    get_name_by_id,
    new_source,
    say_chara_line,
    train_global_can,
)
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
    # 人数判定
    if len(train_manager.train.actors) * 2 < len(train_manager.train.targets):  # type: ignore
        return False
    # 被调教方有男性
    for target_id in train_manager.train.targets:  # type: ignore
        chara = get_entity_by_id(world.player, target_id)
        if chara.is_male():
            return False
    # 槽位判定（调教方1个手）
    return check_body_slots(world, actor_slots={'hands': 1})


def continuous_tick(world: World, ctx: CommandContext, cmd: ContinuousCommand):
    # 持续效果
    act_num = len(cmd.actor_ids)
    tar_num = len(cmd.target_ids)
    if act_num == 0 or tar_num == 0:
        return [], []
    num_adjust = float(act_num / tar_num)
    source: dict[str, int] = new_source({
        'c_pleasure_source': 40,
        "happiness_source": 50,
        "lust_source": 75,
        'love_source': 75,
        'exposure_source': 50,
        'passivity_source': 70,
        'disgust_source': 185
    })

    sources: dict[str, dict[str, int | float]] = {}
    exp_mes = []
    # 调教者
    for actor_id in cmd.actor_ids:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        temp_sources[actor_id]['c_pleasure_source'] += int(
            chara.abl['finger_abl'] * 10)


        if chara.has_talent('flexible_fingers'):
            temp_sources[actor_id]['c_pleasure_source'] *= 1.5
            temp_sources[actor_id]['lubrication_source'] *= 1.5

        sources.update(temp_sources)
        exp_mes.append(exp_calc('finger_exp', chara))

    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in cmd.target_ids:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 50% 消耗
        ctx.consume(stamina=2, energy=25, chara=chara)

        # exp
        exp_mes.append(exp_calc('c_exp', chara))

    pairs = []
    for actor_id in cmd.actor_ids:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in cmd.target_ids:
            target = get_entity_by_id(world.player, target_id)
            pairs.append((sources[target_id], actor, target))

    return pairs, exp_mes


@register_cmd(
    'pussy_caress',
    '秘穴爱抚',
    cat='爱抚',
    train_mode=True,
    can=can,
    needs_target=False,
    continuous=True,
    continuous_text='{actors}正在爱抚{targets}的秘穴',
    actor_slots={'hands': 1},
    target_slots={},
    continuous_tick=continuous_tick,
)
def pussy_caress(world: World):
    """秘穴爱抚"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None:
        return []

    new_cmd_id = None
    if getattr(world, 'is_current_cmd_continuous', False):
        new_cmd = world.train_manager.add_continuous_cmd(
            'pussy_caress', list(train.actors), list(train.targets))
        if new_cmd:
            new_cmd_id = new_cmd.id

    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source({
        'c_pleasure_source': 80,
        "happiness_source": 100,
        "lust_source": 150,
        'love_source': 150,
        'exposure_source': 100,
        'passivity_source': 145,
        'disgust_source': 370
    })

    src_name = get_name_by_id(world.player, train.actors[0])
    tar_name = get_name_by_id(world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}温柔地用手指来回摩擦着{tar_name}的秘穴……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            say_chara_line(chara, ctx, 'pussy_caress')

    # 推进时间
    ctx.advance_time(COMMAND_TIME_DATA['pussy_caress'])

    sources: dict[str, dict[str, int | float]] = {}
    # 调教者
    for actor_id in train.actors:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        # abl: 指
        temp_sources[actor_id]['c_pleasure_source'] += chara.abl['finger_abl'] * 10

        if chara.has_talent('flexible_fingers'):
            temp_sources[actor_id]['c_pleasure_source'] *= 1.5
            temp_sources[actor_id]['lubrication_source'] *= 1.5

        sources.update(temp_sources)

        # exp
        exp_mes.append(exp_calc('finger_exp', chara))



    # 合并调教者产生的source
    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)
        # TODO: 衣装影响

        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 体力和气力消耗
        ctx.consume(stamina=5, energy=50, chara=chara)

        # exp
        exp_mes.append(exp_calc('c_exp', chara))

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

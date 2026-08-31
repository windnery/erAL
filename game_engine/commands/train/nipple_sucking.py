from __future__ import annotations
from game_engine.commands._common import say_chara_line
from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import train_global_can, new_source, get_name_by_id, get_entity_by_id, \
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
    # 人数判定
    if len(train_manager.train.actors) < len(train_manager.train.targets):  # type: ignore
        return False
    # 槽位判定（调教方1嘴，被调教方1胸）
    if not check_body_slots(world, actor_slots={'mouth': 1}, target_slots={'breasts': 1}):
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
        'b_pleasure_source': 25,
        'love_source': 15,
        'exposure_source': 10,
        'unclean_source': 15,
        'disgust_source': 50
    })

    sources: dict[str, dict[str, int | float]] = {}
    exp_mes = []
    # 调教者
    for actor_id in cmd.actor_ids:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        temp_sources[actor_id]['b_pleasure_source'] += int(
            chara.abl['tongue_abl'] * 10)
        temp_sources[actor_id]['love_source'] += int(
            chara.abl['tongue_abl'] * 2)

        if chara.has_talent('flexible_tongue'):
            temp_sources[actor_id]['b_pleasure_source'] *= 1.5

        sources.update(temp_sources)
        exp_mes.append(exp_calc('tongue_exp', chara))

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

        exp_mes.append(exp_calc('b_exp', chara))

    pairs = []
    for actor_id in cmd.actor_ids:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in cmd.target_ids:
            target = get_entity_by_id(world.player, target_id)
            pairs.append((sources[target_id], actor, target))

    return pairs, exp_mes


@register_cmd(
    'nipple_sucking',
    '吸乳头',
    cat='爱抚',
    train_mode=True,
    can=can,
    needs_target=False,
    continuous=True,
    continuous_text='{actors}正在吮吸{targets}的乳头',
    actor_slots={'mouth': 1},
    target_slots={'breasts': 1},
    continuous_tick=continuous_tick,
)
def nipple_sucking(world: World):
    """吸乳头"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None:
        return []

    new_cmd_id = None
    if getattr(world, 'is_current_cmd_continuous', False):
        new_cmd = world.train_manager.add_continuous_cmd(
            'nipple_sucking', list(train.actors), list(train.targets))
        if new_cmd:
            new_cmd_id = new_cmd.id

    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source({
        'b_pleasure_source': 50,
        'love_source': 30,
        'exposure_source': 20,
        'unclean_source': 30,
        'disgust_source': 100
    })

    src_name = get_name_by_id(world.player, train.actors[0])
    tar_name = get_name_by_id(world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}吸允着{tar_name}的乳头……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            say_chara_line(chara, ctx, 'nipple_sucking')

    # 推进时间
    ctx.advance_time(command_time_data['nipple_sucking'])

    sources: dict[str, dict[str, int | float]] = {}
    # 调教者
    for actor_id in train.actors:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.player, actor_id)
        temp_sources[actor_id]['b_pleasure_source'] += chara.abl['tongue_abl'] * 20
        temp_sources[actor_id]['love_source'] += chara.abl['tongue_abl'] * 5

        if chara.has_talent('flexible_tongue'):
            temp_sources[actor_id]['b_pleasure_source'] *= 1.5

        sources.update(temp_sources)

        # exp
        exp_mes.append(exp_calc('tongue_exp', chara))

    # 合并调教者产生的source
    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust)
                        for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)
        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 体力和气力消耗
        ctx.consume(stamina=5, energy=50, chara=chara)

        # exp
        exp_mes.append(exp_calc('b_exp', chara))

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

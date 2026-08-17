from __future__ import annotations
from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from config.chara_config import PLAYER_ID
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import train_global_can, new_source, get_name_by_id, get_entity_by_id, \
    favor_trust_proc, accumulate_sources, source_proc
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify

if TYPE_CHECKING:
    from world import World


def can(world: World):
    """执行判定"""
    train_manager = world.train_manager
    # 通用判定
    if not train_global_can(train_manager):
        return False
    # 人数判定
    if len(train_manager.train.actors) * 2 < len(train_manager.train.targets): # type: ignore
        return False

    return True


@register_cmd('caress', '爱抚', cat='爱抚', train_mode=True, can=can, needs_target=False)
def caress(world: World):
    """爱抚"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    if train is None: return []
    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source({
        'c_pleasure_source': 40,
        'b_pleasure_source': 40,
        'love_source': 50,
        'sex_act_source': 60,
        'exposure_source': 20,
        'unclean_source': 30,
        'escape_source': 20,
        'disgust_source': 20
    })

    src_name = get_name_by_id(world.npc_manager, world.player, train.actors[0])
    tar_name = get_name_by_id(world.npc_manager, world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}温柔地用手指来回抚摸着{tar_name}的肌肤……')
    for target_id in train.targets:
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            line = chara.get_line('caress') # type: ignore
            if line:
                # 有口上
                ctx.say(line.replace('{name}', chara.name))

    # 推进时间
    ctx.advance_time(command_time_data['caress'])

    sources: dict[str, dict[str, int | float]]  = {}
    # 调教者
    for actor_id in train.actors:
        temp_sources: dict[str, dict[str, int | float]] = {
            actor_id: source.copy()
        }
        chara = get_entity_by_id(world.npc_manager, world.player, actor_id)
        temp_sources[actor_id]['c_pleasure_source'] += chara.abl['finger_abl'] * 4
        temp_sources[actor_id]['b_pleasure_source'] += chara.abl['finger_abl'] * 4

        if chara.has_talent('flexible_fingers'):
            temp_sources[actor_id]['c_pleasure_source'] *= 1.5
            temp_sources[actor_id]['b_pleasure_source'] *= 1.5

        sources.update(temp_sources)

        # exp
        chara.set_exp('finger_exp', chara.get_exp('finger_exp') + 1)

        # 体力和气力消耗
        ctx.consume(stamina=20, energy=20, chara=chara)

    # 合并调教者产生的source
    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust) for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.npc_manager, world.player, target_id)
        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        source_list = [f'{tar_name} ']
        for k, v in sources[target_id].items():
            if v != 0:
                source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
        ctx.say(' '.join(source_list))

        # 体力和气力消耗
        ctx.consume(stamina=10, energy=40, chara=chara)

        # 处理好感和信赖
        if target_id != PLAYER_ID:
            favor_trust_proc(sources[target_id], chara, ctx)

    # source转换过程统一处理
    for actor_id in train.actors:
        actor = get_entity_by_id(world.npc_manager, world.player, actor_id)
        for target_id in train.targets:
            target = get_entity_by_id(world.npc_manager, world.player, target_id)
            # 笛卡尔积
            source_proc(sources[target_id], actor, target, ctx)

    ctx.say(f'度过了{command_time_data["caress"]}分钟')
    return ctx.result()

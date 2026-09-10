from __future__ import annotations

from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from data.time.time_data import COMMAND_TIME_DATA
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import (
    accumulate_sources,
    get_entity_by_id,
    new_source,
    say_chara_line,
)
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify

if TYPE_CHECKING:
    from world import World


def can(world: World):
    """执行判定"""
    train_manager = world.train_manager
    if not train_manager.train:
        return False
    # 调教方1+
    if not train_manager.train.actors:
        return False
    # 被调教方1+
    if not train_manager.train.targets:
        return False
    return True


@register_cmd(
    "do_nothing", "什么都不做", cat="特殊", train_mode=True, can=can, needs_target=False
)
def do_nothing(world: World):
    """什么都不做"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None:
        return []

    new_cmd_id = None
    if getattr(world, "is_current_cmd_continuous", False):
        new_cmd = world.train_manager.add_continuous_cmd(
            "do_nothing", list(train.actors), list(train.targets)
        )
        if new_cmd:
            new_cmd_id = new_cmd.id

    act_num = len(train.actors)  # 调教者人数
    tar_num = len(train.targets)  # 被调教者人数
    num_adjust = float(act_num / tar_num)  # 人数补正
    source: dict[str, int] = new_source(
        {"love_source": 10, "exposure_source": 10, "escape_source": 10}
    )

    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        if target_id != PLAYER_ID:
            # 只有舰娘有口上
            say_chara_line(chara, ctx, "do_nothing")

    # 推进时间
    ctx.advance_time(COMMAND_TIME_DATA["do_nothing"])

    sources: dict[str, dict[str, int | float]] = {}
    # 调教者
    for actor_id in train.actors:
        temp_sources: dict[str, dict[str, int | float]] = {actor_id: source.copy()}
        chara = get_entity_by_id(world.player, actor_id)
        sources.update(temp_sources)

    # 合并调教者产生的source
    merged_source = accumulate_sources(sources)

    # 被调教者
    for target_id in train.targets:
        sources: dict[str, dict[str, int]] = {
            target_id: {k: int(v * num_adjust) for k, v in merged_source.items()}
        }
        chara = get_entity_by_id(world.player, target_id)

        # abl: 受虐属性
        table = [
            (0.8, 0, 0),
            (1, 20, 30),
            (1.2, 40, 70),
            (1.4, 70, 120),
            (1.5, 110, 180),
            (1.7, 150, 250),
            (1.9, 200, 300),
            (2.1, 250, 350),
            (2.3, 300, 400),
            (2.5, 350, 450),
            (3, 500, 500),
        ]
        sources[target_id]["exposure_source"] *= table[chara.abl["masochism_abl"]][0]
        sources[target_id]["lubrication_source"] += table[chara.abl["masochism_abl"]][1]
        sources[target_id]["lust_source"] += table[chara.abl["masochism_abl"]][2]

        # talent: 受虐狂
        if chara.has_talent("masochist"):
            sources[target_id]["exposure_source"] = int(
                sources[target_id]["exposure_source"] * 2.5
            )
            sources[target_id]["lubrication_source"] = int(
                sources[target_id]["lubrication_source"] * 1.2
            )
            sources[target_id]["lust_source"] = int(
                sources[target_id]["lust_source"] * 1.2
            )

        # 通用source修正
        sources[target_id] = common_src_modify(sources[target_id], chara)

        # 体力和气力消耗
        ctx.consume(stamina=10, energy=10, chara=chara)

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

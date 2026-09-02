from __future__ import annotations

from typing import TYPE_CHECKING

from config.chara_config import PLAYER_ID
from config.map_config import HAVE_BED_LOC
from data.time.time_data import command_time_data
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import (
    accumulate_sources,
    get_entity_by_id,
    get_name_by_id,
    new_source,
    pain_check_v,
    train_global_can, add_attitude_mes, check_body_slots,
)
from game_engine.commands._common import say_chara_line
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.models.continuous_command import ContinuousCommand
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import c_talent

if TYPE_CHECKING:
    from world import World


def can(world: World):
    """执行判定"""
    train_manager = world.train_manager
    if not train_global_can(train_manager):
        return False
    if PLAYER_ID in train_manager.train.targets:
        return False
    # 槽位判定（调教方1肉棒，被调教方1阴道）
    if not check_body_slots(world, actor_slots={'penis': 1}, target_slots={'vagina': 1}):
        return False
    for chara_id in train_manager.train.actors:
        # 调教方有人无插入能力
        chara = get_entity_by_id(world.player, chara_id)
        if not chara.can_insert():
            return False
    return True


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    success_score = 15
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

    # 快乐刻印
    temp = npc.mark['pleasure_mark'] * 3
    score += temp
    mes = add_attitude_mes(mes, f"快乐刻印({temp})")

    # palam: 欲情
    temp = npc.palam_lv['lust_palam'] * 3
    score += temp
    mes = add_attitude_mes(mes, f"欲情({temp})")

    # palam: 润滑
    if npc.palam_lv['lubrication_palam'] < 3:
        score -= 5
        mes = add_attitude_mes(mes, f"润滑(-5)")

    # 害羞
    if npc.get_talent_value('sense_of_shame') > 0:
        score -= 2
        mes = add_attitude_mes(mes, f"害羞(-2)")

    # 陷落阶段
    temp = 5 + npc.get_talent_value('relationship') * 5
    score += temp
    mes = add_attitude_mes(
        mes, f"{npc.get_talent_name('relationship')}({temp})")

    # 否定快感
    if npc.get_talent_value('denial_of_pleasure') < 0:
        score -= 5
        mes = add_attitude_mes(mes, f"否定快感(-5)")

    # 处女
    if npc.get_talent_value('virgin') == 1:
        temp = max(10, 40 - npc.exp['v_exp'])
        score -= temp
        mes = add_attitude_mes(mes, f"处女(-{temp})")

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
    num_adjust = act_num / tar_num
    base_source = new_source({
        'v_pleasure_source': 150,
        'love_source': 75,
        'pain_source': 250,
        'exposure_source': 25,
        'unclean_source': 30,
        'disgust_source': 150
    })
    feedback_source = new_source({
        'c_pleasure_source': 200,
    })

    actor_sources: dict[str, dict[str, int | float]] = {}
    exp_mes = []
    for actor_id in cmd.actor_ids:
        actor = get_entity_by_id(world.player, actor_id)
        source = base_source.copy()
        actor_sources[actor_id] = source
        if actor.id == PLAYER_ID and actor.get_talent_value('male_virgin') == 1:
            actor.set_talent('male_virgin', '0')
            ctx.say(c_talent(f'{actor.name}失去了[处男]！'))
        exp_mes.append(exp_calc('insert_exp', actor))

        # 50% 消耗
        ctx.consume(stamina=20, energy=20, chara=actor)

    merged_source = accumulate_sources(actor_sources)
    target_sources: dict[str, dict[str, int]] = {}
    defloration: dict[str, bool] = {}
    for target_id in cmd.target_ids:
        chara = get_entity_by_id(world.player, target_id)
        source = {key: int(value * num_adjust)
                  for key, value in merged_source.items()}

        if chara.get_talent_value('virgin') == 1:
            defloration[target_id] = True
            source['pain_source'] += 500
            ctx.say(c_talent(f'{chara.name}失去了[处女]！'))
            say_chara_line(chara, ctx, 'defloration')

        pain_check_v(source, chara)
        region = chara.location['region']
        node = chara.location['node']
        if (region in HAVE_BED_LOC
                and node in HAVE_BED_LOC[region]
                and len(cmd.actor_ids) == 1
                and cmd.actor_ids[0] == PLAYER_ID):
            source['v_pleasure_source'] += int(chara.exp['love_exp'] * 0.5)

        source = common_src_modify(source, chara)
        target_sources[target_id] = source

        # 50% 消耗
        ctx.consume(stamina=25, energy=30, chara=chara)

        exp_mes.append(exp_calc('v_exp', chara))
        exp_mes.append(exp_calc('v_insert_exp', chara))
        exp_mes.append(exp_calc('love_exp', chara,
                       chara.get_talent_value('relationship') * 2))
        if defloration.get(target_id) and chara.get_talent_value('relationship') > 1:
            exp_mes.append(exp_calc('love_exp', chara, 10))
        if defloration.get(target_id):
            chara.set_talent('virgin', '0')

    pairs = []
    for actor_id in cmd.actor_ids:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in cmd.target_ids:
            target = get_entity_by_id(world.player, target_id)
            pairs.append((target_sources[target_id], actor, target))
            feedback = common_src_modify(feedback_source, actor)
            pairs.append((feedback, target, actor))

    return pairs, exp_mes


@register_cmd(
    'common_position',
    '正常位',
    cat='性交',
    train_mode=True,
    can=can,
    needs_target=False,
    continuous=True,
    continuous_text='{actors}正在与{targets}进行正常位',
    actor_slots={'penis': 1},
    target_slots={'vagina': 1},
    continuous_tick=continuous_tick,
)
def common_position(world: World):
    """正常位"""
    ctx = CommandContext(world)
    train = world.train_manager.train
    exp_mes = []
    if train is None or not train.actors or not train.targets:
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
            'common_position', list(train.actors), list(train.targets))
        if new_cmd:
            new_cmd_id = new_cmd.id

    act_num = len(train.actors)
    tar_num = len(train.targets)
    num_adjust = act_num / tar_num
    base_source = new_source({
        'v_pleasure_source': 300,
        'love_source': 150,
        'pain_source': 500,
        'exposure_source': 50,
        'unclean_source': 60,
        'disgust_source': 300
    })
    feedback_source = new_source({
        'c_pleasure_source': 400,
    })

    src_name = get_name_by_id(world.player, train.actors[0])
    tar_name = get_name_by_id(world.player, train.targets[0])
    if act_num > 1:
        src_name += '等人'
    if tar_num > 1:
        tar_name += '等人'
    ctx.say(f'{src_name}将肉棒抵在{tar_name}的蜜穴上，缓缓插入……')

    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        if target_id != PLAYER_ID:
            say_chara_line(chara, ctx, 'common_position')

    ctx.advance_time(command_time_data['common_position'])

    actor_sources: dict[str, dict[str, int | float]] = {}
    for actor_id in train.actors:
        actor = get_entity_by_id(world.player, actor_id)
        source = base_source.copy()
        actor_sources[actor_id] = source
        if actor.id == PLAYER_ID and actor.get_talent_value('male_virgin') == 1:
            actor.set_talent('male_virgin', '0')
            ctx.say(c_talent(f'{actor.name}失去了[处男]！'))
        # 插入经验
        exp_mes.append(exp_calc('insert_exp', actor))
        # 消费体力和气力
        ctx.consume(stamina=40, energy=40, chara=actor)

    merged_source = accumulate_sources(actor_sources)
    target_sources: dict[str, dict[str, int]] = {}
    defloration: dict[str, bool] = {}  # 记录本次破处发生的角色（在清除天赋前记录）
    for target_id in train.targets:
        chara = get_entity_by_id(world.player, target_id)
        source = {key: int(value * num_adjust)
                  for key, value in merged_source.items()}

        if chara.get_talent_value('virgin') == 1:
            defloration[target_id] = True
            source['pain_source'] += 1000
            ctx.say(c_talent(f'{chara.name}失去了[处女]！'))
            say_chara_line(chara, ctx, 'defloration')

        # v苦痛处理
        pain_check_v(source, chara)
        # 正常位补正
        region = chara.location['region']
        node = chara.location['node']
        if (region in HAVE_BED_LOC
                and node in HAVE_BED_LOC[region]
                and len(train.actors) == 1
                and train.actors[0] == PLAYER_ID):
            source['v_pleasure_source'] += chara.exp['love_exp']

        source = common_src_modify(source, chara)
        target_sources[target_id] = source

        ctx.consume(stamina=50, energy=60, chara=chara)
        # v经验 v性交经验
        exp_mes.append(exp_calc('v_exp', chara))
        exp_mes.append(exp_calc('v_insert_exp', chara))
        exp_mes.append(exp_calc('love_exp', chara,
                       chara.get_talent_value('relationship') * 2))
        if defloration.get(target_id) and chara.get_talent_value('relationship') > 1:
            # 首夜奖励：处女且关系>1 时额外给 love_exp
            exp_mes.append(exp_calc('love_exp', chara, 10))
        if defloration.get(target_id):
            # 破处后无条件清除处女天赋（不依赖关系等级）
            chara.set_talent('virgin', '0')

    # 构建主指令 pairs
    pairs = []
    for actor_id in train.actors:
        actor = get_entity_by_id(world.player, actor_id)
        for target_id in train.targets:
            target = get_entity_by_id(world.player, target_id)
            pairs.append((target_sources[target_id], actor, target))
            feedback = common_src_modify(feedback_source, actor)
            # 反馈：target给actor的c_pleasure
            pairs.append((feedback, target, actor))

    # 统一回合结算管道
    from game_engine.commands._common import process_train_turn
    process_train_turn(world, ctx, pairs, exp_mes,
                       new_cmd_id=new_cmd_id, ejaculation_position='中出')

    return ctx.result()

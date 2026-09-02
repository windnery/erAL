from __future__ import annotations
from typing import TYPE_CHECKING

from collections import defaultdict

from config.abl_config import ABL_LV
from config.attr_defs import ATTR_DEFS
from config.base_config import MAX_RATIONALITY
from config.chara_config import PLAYER_ID
from config.palam_config import EJACULATION_VITALITY_COST, SEMEN_SOURCES, ORGASM_BASE
from config.source_config import ALL_SOURCE_KEYS
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.initiative_calc import (
    initiative_ejaculation_proc,
    initiative_grow_proc,
    initiative_orgasm_proc,
    pleasure_sum,
)
from game_engine.data_pipeline.mark.mark_calc import mark_calc
from game_engine.data_pipeline.mood.mood_calc import mood_proc
from game_engine.data_pipeline.palam.orgasm_calc import orgasm_check, orgasm_check_parts
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from game_engine.data_pipeline.trust.trust_calc import trust_calc
from game_engine.managers.NpcManager import NpcManager
from game_engine.models.character import Character
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import c_chara, c_orgasm, c_ejaculation

if TYPE_CHECKING:
    from world import World
    from game_engine.managers.TrainManager import TrainManager


def say_chara_line(chara, ctx: CommandContext, action: str, block: str = 'narrative'):
    """输出角色口上场景（按角色色逐条染色）；无口上时静默。"""
    from game_engine.dialogue import get_scene

    scene = get_scene(chara, action, ctx.world.player.name)
    if scene:
        for msg in scene:
            ctx.say_block(block, c_chara(msg, chara.color))
        return True
    # False说明无口上
    return False


def new_source(base: dict[str, int]):
    """根据base生成新的source"""
    s = {k: 0 for k in ALL_SOURCE_KEYS}
    if base:
        s.update(base)
    return s


def source_proc(source: dict[str, int], actor: Character, target: ShipGirl, ctx: CommandContext, block: str = 'palam'):
    """source的统一转换过程（单对）"""
    # 刻印处理（仅舰娘有刻印）
    if isinstance(target, ShipGirl):
        mark_calc(source, target, ctx)
    # source->palam
    mes_source, mes_target, _ = palam_calc(source, actor, target)
    if mes_source:
        ctx.say_block(block, *mes_source)
    if mes_target:
        ctx.say_block(block, *mes_target)
    # 绝顶判定
    if isinstance(target, ShipGirl):
        orgasm_mes = orgasm_check(target)
        if orgasm_mes:
            ctx.say_block(block, *orgasm_mes)
    # 更新palam等级
    actor.update_palam_level()
    target.update_palam_level()
    # source->情绪/理性/心情（仅舰娘）
    if isinstance(target, ShipGirl):
        emotion_rationality_calc(source, target)
        mood_proc(source, target)


def source_proc_batch(pairs: list[tuple[dict[str, int], Character, Character]], ctx: CommandContext,
                      ejaculation_position: str | None = None):
    """source的统一转换过程（批量，多对 (source, actor, target)）
    数值：每对依次累计（保持笛卡尔积多次累计语义）
    输出：按角色聚合后统一打印一次（同一角色只出现一次）
    顺序：基础palam -> 射精处理(提示+口上+精液palam) -> 绝顶判定/等级/情绪理性
    """
    if not pairs:
        return

    # 收集所有对的增量（dry_run 不改 palam）
    # id(chara) -> {palam_key: delta}
    per_chara: dict[int, dict[str, int]] = {}
    # id(target) -> 该角色收到的 source（用于情绪/理性）
    source_of: dict[int, dict[str, int]] = {}
    targets_order: list[int] = []  # 保持 target 出现顺序
    actors_order: list[int] = []

    for source, actor, target in pairs:
        self_initiative = ctx.world.train_manager.initiative_cmp(
            actor.id, target.id)
        _, _, changes = palam_calc(
            source, actor, target, dry_run=True, self_initiative=self_initiative)
        for (chara_kind, palam), delta in changes.items():
            chara = actor if chara_kind == 'source' else target
            key = id(chara)
            per_chara.setdefault(key, {})
            per_chara[key][palam] = per_chara[key].get(palam, 0) + delta
            if key not in targets_order and chara_kind == 'target':
                targets_order.append(key)
            if key not in actors_order and chara_kind == 'source':
                actors_order.append(key)
        # 记录每个 target 收到的 source（同 target 多对时合并）
        tid = id(target)
        if tid not in source_of:
            source_of[tid] = {}
        for k, v in source.items():
            source_of[tid][k] = source_of[tid].get(k, 0) + v

    # 1. 统一应用基础 palam + 按角色打印一次
    for key, deltas in per_chara.items():
        if not deltas:
            continue
        # 找该角色的对象
        chara = None
        for _, actor, target in pairs:
            if id(actor) == key:
                chara = actor
                break
            if id(target) == key:
                chara = target
                break
        if chara is None:
            continue
        mes = [f'{chara.name}']
        for palam, delta in deltas.items():
            if delta == 0:
                continue
            mes.append(
                f'{ATTR_DEFS["palam"][palam]["name"]} {chara.palam[palam]} + {delta} = {chara.palam[palam] + delta}')
            chara.palam[palam] += delta
        if len(mes) > 1:
            ctx.say_block('palam', *mes)

    # 2. 基础 palam 之后、绝顶之前进行射精处理
    if ejaculation_position:
        ejaculation_proc(ctx, position=ejaculation_position, check_orgasm=False)
    else:
        ejaculation_proc(ctx, check_orgasm=False)

    # 3. 绝顶/等级/情绪理性：每个角色实例一次（去重）
    train = ctx.world.train_manager.train
    processed: set[int] = set()
    for _, actor, target in pairs:
        # target 侧
        tid = id(target)
        if tid not in processed:
            processed.add(tid)
            if isinstance(target, ShipGirl):
                orgasm_mes, org_lv, org_num = orgasm_check_parts(target)
                if orgasm_mes:
                    ctx.say_block('palam', *orgasm_mes)
                    # 绝顶主导权衰减（按最高等级 × 部位数）
                    if train is not None and train.initiative:
                        decay_mes = initiative_orgasm_proc(
                            train, target, max(org_lv.values()), org_num)
                        if decay_mes:
                            ctx.say_block('palam', decay_mes)
            target.update_palam_level()
            if isinstance(target, ShipGirl) and tid in source_of:
                emotion_rationality_calc(source_of[tid], target)
                mood_proc(source_of[tid], target)
                # 刻印处理
                mark_calc(source_of[tid], target, ctx)
        # actor 侧
        aid = id(actor)
        if aid not in processed:
            processed.add(aid)
            actor.update_palam_level()

    # 4. 主导权增长结算：所有参与者基础增长，本轮受快感越多增长越少
    if train is not None and train.initiative:
        # 每人本轮收到的快感系source之和（本轮未收到按0计）
        received: dict[str, int] = {cid: 0 for cid in train.initiative}
        chara_of: dict[int, Character] = {}
        for _, actor, target in pairs:
            chara_of[id(actor)] = actor
            chara_of[id(target)] = target
        for tid, src in source_of.items():
            chara = chara_of.get(tid)
            if chara is not None:
                received[chara.id] = received.get(
                    chara.id, 0) + pleasure_sum(src)
        chara_pleasures = []
        for cid, s in received.items():
            entity = get_entity_by_id(train.player, cid)
            if isinstance(entity, Character):
                chara_pleasures.append((entity, s))
        grow_mes = initiative_grow_proc(train, chara_pleasures)
        if grow_mes:
            ctx.say_block('palam', *grow_mes)


def low_intimacy2favor(intimacy_abl: int) -> int:
    """亲密低会导致好感度下降"""
    if intimacy_abl == 0:
        return -3
    elif intimacy_abl == 1:
        return -2
    elif intimacy_abl == 2:
        return -1
    else:
        return 0


def low_favor2favor(favor: int) -> int:
    """好感度低会导致好感度下降"""
    if favor <= 50:
        return -3
    elif favor <= 100:
        return -2
    elif favor <= 250:
        return -1
    else:
        return 0


def get_revision(raw_num: int, limit: int, revision_rate: int | float) -> int:
    """获取修正后的数值"""
    return int(limit - limit * revision_rate / (revision_rate + raw_num))


def get_name_by_id(player: Player, chara_id: str):
    """通过id获取角色名"""
    if chara_id == player.id:
        return player.name
    npc = NpcManager.get_npc_by_id(chara_id)
    return npc.name if npc else chara_id


def get_entity_by_id(player: Player, chara_id: str) -> Character:
    """通过id获取角色"""
    return NpcManager.get_npc_by_id(chara_id) if chara_id != PLAYER_ID else player


def global_can(player: Player, npc: ShipGirl):
    """指令不可用的通用判定 优先级最高"""
    # 气力0
    if player.is_energy_empty():
        return False
    # 睡眠中
    if npc.is_sleeping():
        return False

    return True


def train_global_can(train_manager: TrainManager):
    """调教指令不可用的通用判定 优先级最高"""
    train = train_manager.train
    if train:
        # 调教方1+
        if not train.actors:
            return False
        # 被调教方1+
        if not train.targets:
            return False
        # 调教方有角色气力0
        for source in train.actors:
            chara = NpcManager.get_npc_by_id(
                source) if source != PLAYER_ID else train.player
            if chara.is_energy_empty():
                return False
    else:
        return False

    return True


def check_body_slots(world: World, actor_slots: dict[str, int] | None = None, target_slots: dict[str, int] | None = None) -> bool:
    """检查调教方和被调教方是否具备指定的身体槽位"""
    train = world.train_manager.train
    if not train:
        return False
    if actor_slots:
        for actor_id in train.actors:
            actor = get_entity_by_id(world.player, actor_id)
            if not actor or not actor.has_body_slots(actor_slots):
                return False
    if target_slots:
        for target_id in train.targets:
            target = get_entity_by_id(world.player, target_id)
            if not target or not target.has_body_slots(target_slots):
                return False
    return True


def process_train_turn(
    world: World,
    ctx: CommandContext,
    main_pairs: list[tuple[dict[str, int], Character, Character]],
    main_exp_mes: list[str] | None = None,
    new_cmd_id: str | None = None,
    ejaculation_position: str | None = None,
):
    """调教指令的统一回合结算管道：
    1. 收集所有持续中指令产生的 pairs、exp 并扣减 50% 体力/气力
    2. 按 (actor, target) 合并所有 Source 字典
    3. 输出单次汇总的 Source 提示
    4. 统一执行一次 source_proc_batch（Palam/绝顶/主导权/情绪理性）
    5. 统一为每个被调教者结算一次好感度与信赖度
    6. 统一输出所有 Exp 增量
    """
    train = world.train_manager.train
    if not train:
        return

    all_exp_mes = list(main_exp_mes or [])
    all_pairs = list(main_pairs)

    from game_engine.commands._commands import REGISTER_CONTINUOUS_TICK

    # 遍历收集所有持续中指令（跳过本轮刚加入的 new_cmd_id）
    for cmd in list(train.continuous_commands):
        if new_cmd_id and cmd.id == new_cmd_id:
            continue
        tick_func = REGISTER_CONTINUOUS_TICK.get(cmd.command_key)
        if tick_func:
            res = tick_func(world, ctx, cmd)
            if res:
                tick_pairs, tick_exp = res
                all_pairs.extend(tick_pairs)
                all_exp_mes.extend(tick_exp)

    # 将所有 pairs 按 (id(actor), id(target)) 进行 Source 累加合并
    merged_pairs_map: dict[tuple[int, int], tuple[dict[str, int], Character, Character]] = {}
    target_totals: dict[int, tuple[Character, dict[str, int]]] = {}

    for src, actor, target in all_pairs:
        pair_key = (id(actor), id(target))
        if pair_key not in merged_pairs_map:
            merged_pairs_map[pair_key] = (new_source({}), actor, target)
        for k, v in src.items():
            merged_pairs_map[pair_key][0][k] = merged_pairs_map[pair_key][0].get(k, 0) + int(v)

        tid = id(target)
        if tid not in target_totals:
            target_totals[tid] = (target, new_source({}))
        for k, v in src.items():
            target_totals[tid][1][k] = target_totals[tid][1].get(k, 0) + int(v)

    final_pairs = list(merged_pairs_map.values())

    # 输出所有收到 Source 的角色摘要，包括目标对调教方的反馈。
    # 反馈 Source 仍然会参与后续结算，不能因为角色当前不在 targets 列表就隐藏摘要。
    for tid, (target_chara, total_src) in target_totals.items():
        ctx.say_source(total_src, prefix=target_chara.name)

    # 统一执行一轮 source_proc_batch
    source_proc_batch(final_pairs, ctx, ejaculation_position=ejaculation_position)

    # 统一为每个被调教者结算一次好感度与信赖度
    for tid, (target_chara, total_src) in target_totals.items():
        if isinstance(target_chara, ShipGirl) and target_chara.id in train.targets:
            favor_trust_proc(total_src, target_chara, ctx)

    # 统一输出 exp 信息
    ctx.say_exp(*all_exp_mes)


def execute_continuous_ticks(world: World, ctx: CommandContext, skip_cmd_id: str | None = None):
    """兼容旧接口"""
    process_train_turn(world, ctx, [], [], new_cmd_id=skip_cmd_id)


def accumulate_sources(dict_iterable) -> dict[str, int | float]:
    result = defaultdict(int)
    if isinstance(dict_iterable, dict):
        dict_iterable = dict_iterable.values()
    for inner_dict in dict_iterable:
        for key, value in inner_dict.items():
            result[key] += value
    return dict(result)


def favor_trust_proc(source: dict[str, int], npc: ShipGirl, ctx: CommandContext, is_intimate: bool = False,
                     ex_favor: int = 0, ex_trust: int = 0, block: str = 'favor', is_ejaculation: bool = False):
    """处理好感和信赖"""
    favor_delta = favor_calc(ctx.world.player, npc, source)
    trust_delta = trust_calc(ctx.world.player, npc, source)
    # 亲昵指令额外判断好感度和亲密
    if is_intimate:
        favor_delta += low_intimacy2favor(npc.abl['intimacy_abl'])
        favor_delta += low_favor2favor(npc.favor)
    favor_delta += ex_favor
    trust_delta += ex_trust
    npc.favor += favor_delta
    npc.trust += trust_delta

    if favor_delta > 0:
        ctx.say_block(block,
                      f'好感+{favor_delta} ({npc.name})' + (f'{c_orgasm("(射精加成)")}' if is_ejaculation else ''))
    elif favor_delta < 0:
        ctx.say_block(block, f'好感{favor_delta} ({npc.name})')
    if trust_delta > 0:
        ctx.say_block(block,
                      f'信赖+{trust_delta} ({npc.name})' + (f'{c_orgasm("(射精加成)")}' if is_ejaculation else ''))
    elif trust_delta < 0:
        ctx.say_block(block, f'信赖{trust_delta} ({npc.name})')


def pain_check_v(source: dict[str, int | float], chara: Character):
    """v苦痛判定"""
    # exp: v经验
    if chara.exp['v_exp'] < ABL_LV[1]:
        source['pain_source'] *= 2.5
        source['disgust_source'] *= 1.5
    elif chara.exp['v_exp'] < ABL_LV[2]:
        source['pain_source'] *= 1.5
        source['disgust_source'] *= 1.2
    elif chara.exp['v_exp'] < ABL_LV[3]:
        pass
    elif chara.exp['v_exp'] < ABL_LV[4]:
        source['pain_source'] *= 0.5
    elif chara.exp['v_exp'] < ABL_LV[5]:
        source['pain_source'] *= 0.3
    else:
        source['pain_source'] *= 0.1

    # palam: 润滑
    if chara.palam_lv['lubrication_palam'] < 1:
        source['pain_source'] *= 1.5
        source['disgust_source'] *= 1.7
    elif chara.palam_lv['lubrication_palam'] < 2:
        source['pain_source'] *= 1.3
        source['disgust_source'] *= 1.5
    elif chara.palam_lv['lubrication_palam'] < 3:
        source['pain_source'] *= 1.1
        source['disgust_source'] *= 1.2
    elif chara.palam_lv['lubrication_palam'] < 4:
        source['pain_source'] *= 0.9
    elif chara.palam_lv['lubrication_palam'] < 5:
        source['pain_source'] *= 0.8
    elif chara.palam_lv['lubrication_palam'] < 6:
        source['pain_source'] *= 0.6
    elif chara.palam_lv['lubrication_palam'] < 7:
        source['pain_source'] *= 0.5
    elif chara.palam_lv['lubrication_palam'] < 8:
        source['pain_source'] *= 0.4
    elif chara.palam_lv['lubrication_palam'] < 9:
        source['pain_source'] *= 0.3
    else:
        source['pain_source'] *= 0.1


def pain_check_a(source: dict[str, int | float], chara: Character):
    """a苦痛判定"""
    # exp: a经验
    if chara.exp['a_exp'] < ABL_LV[1]:
        source['pain_source'] *= 3.0
        source['disgust_source'] *= 3.0
    elif chara.exp['a_exp'] < ABL_LV[2]:
        source['pain_source'] *= 2.0
        source['disgust_source'] *= 2.0
    elif chara.exp['a_exp'] < ABL_LV[3]:
        source['disgust_source'] *= 1.5
    elif chara.exp['a_exp'] < ABL_LV[4]:
        source['pain_source'] *= 0.6
        source['disgust_source'] *= 1.2
    elif chara.exp['a_exp'] < ABL_LV[5]:
        source['pain_source'] *= 0.4
    else:
        source['pain_source'] *= 0.2

    # palam: 润滑
    if chara.palam_lv['lubrication_palam'] < 1:
        source['pain_source'] *= 1.5
        source['disgust_source'] *= 1.7
    elif chara.palam_lv['lubrication_palam'] < 2:
        source['pain_source'] *= 1.3
        source['disgust_source'] *= 1.5
    elif chara.palam_lv['lubrication_palam'] < 3:
        source['pain_source'] *= 1.1
        source['disgust_source'] *= 1.2
    elif chara.palam_lv['lubrication_palam'] < 4:
        source['pain_source'] *= 0.9
    elif chara.palam_lv['lubrication_palam'] < 5:
        source['pain_source'] *= 0.8
    elif chara.palam_lv['lubrication_palam'] < 6:
        source['pain_source'] *= 0.6
    elif chara.palam_lv['lubrication_palam'] < 7:
        source['pain_source'] *= 0.5
    elif chara.palam_lv['lubrication_palam'] < 8:
        source['pain_source'] *= 0.4
    elif chara.palam_lv['lubrication_palam'] < 9:
        source['pain_source'] *= 0.3
    else:
        source['pain_source'] *= 0.2


def add_attitude_mes(mes: str, new: str):
    """添加合意判定输出消息"""
    if mes:
        mes = mes + '+' + new
    else:
        mes = new
    return mes


def get_attitude(player: Player, npc: ShipGirl, impassable_line: int):
    """合意判定
    :param player: 玩家
    :param npc: 角色
    :param impassable_line: 无法逾越的底线的影响
    :return: 合意值 """
    attitude = 0
    mes = ''
    # ===================================== 好感度 =====================================
    if npc.favor <= 800:
        attitude += 0
    elif npc.favor <= 2000:
        attitude += 50
        mes = add_attitude_mes(mes, '好感(50)')
    elif npc.favor <= 4000:
        attitude += 75
        mes = add_attitude_mes(mes, '好感(75)')
    elif npc.favor <= 8000:
        attitude += 100
        mes = add_attitude_mes(mes, '好感(100)')
    elif npc.favor <= 24000:
        attitude += 150
        mes = add_attitude_mes(mes, '好感(150)')
    elif npc.favor <= 40000:
        attitude += 200
        mes = add_attitude_mes(mes, '好感(200)')
    else:
        attitude += 300
        mes = add_attitude_mes(mes, '好感(300)')
    # ===================================== 信赖 =====================================
    if npc.trust <= 50:
        attitude -= 50
        mes = add_attitude_mes(mes, '信赖(-50)')
    elif npc.trust <= 150:
        attitude -= 20
        mes = add_attitude_mes(mes, '信赖(-20)')
    elif npc.trust <= 300:
        attitude += 0
    elif npc.trust <= 500:
        attitude += 30
        mes = add_attitude_mes(mes, '信赖(30)')
    elif npc.trust <= 750:
        attitude += 50
        mes = add_attitude_mes(mes, '信赖(50)')
    else:
        attitude += 100
        mes = add_attitude_mes(mes, '信赖(100)')
    # ===================================== 情绪&理性 =====================================
    temp = npc.get_emotion() // 25 + (MAX_RATIONALITY - npc.get_rationality()) // 25
    attitude += temp
    mes = add_attitude_mes(mes, f'情绪&理性({temp})')
    # ===================================== 旁人在场 =====================================
    if (
        NpcManager.with_mob(npc.location['region'], npc.location['node'])
        and npc.abl['exposure_abl'] < 6  # abl:露出 < 6
        and npc.get_talent_value('sense_of_shame') > -1  # talent:不知羞耻
    ):
        temp = -20 + npc.abl['exposure_abl'] * 3 - npc.get_talent_value('sense_of_shame') * 5
        attitude += temp
        mes = add_attitude_mes(mes, f'旁人在场({temp})')
    # ===================================== abl =====================================
    # 亲密
    temp = npc.abl['intimacy_abl'] * 10
    attitude += temp
    mes = add_attitude_mes(mes, f'亲密({temp})') if temp != 0 else mes
    # 欲望
    temp = npc.abl['desire_abl'] * 5
    attitude += temp
    mes = add_attitude_mes(mes, f'欲望({temp})') if temp != 0 else mes
    # 恭顺
    temp = npc.abl['obedience_abl'] * 5
    attitude += temp
    mes = add_attitude_mes(mes, f'恭顺({temp})') if temp != 0 else mes
    # 侍奉精神
    temp = npc.abl['servant_abl'] * 5
    attitude += temp
    mes = add_attitude_mes(mes, f'侍奉精神({temp})') if temp != 0 else mes
    # ===================================== palam =====================================
    # 亲密
    t = npc.palam_lv['kindness_palam'] * 5
    attitude += t
    mes = add_attitude_mes(mes, f'好意({t})') if t != 0 else mes
    # 欲望
    t = npc.palam_lv['lust_palam'] * 5
    attitude += t
    mes = add_attitude_mes(mes, f'欲望({t})') if t != 0 else mes
    # ===================================== talent =====================================
    # 陷落阶段
    temp = npc.get_talent_value("relationship") * 50
    attitude += temp
    mes = add_attitude_mes(
        mes, f'{npc.get_talent_name("relationship")}({temp})')
    # 胆怯
    if npc.get_talent_value("courage") == -1:
        attitude -= 20
        mes = add_attitude_mes(mes, '胆怯(-20)')
    # 叛逆
    if npc.get_talent_value("attitude") == 1:
        attitude -= 30
        mes = add_attitude_mes(mes, '叛逆(-30)')
    # 傲慢
    if npc.get_talent_value("response") == 1:
        attitude -= 20
        mes = add_attitude_mes(mes, '傲慢(-20)')
    # 自尊心高
    if npc.get_talent_value("self_respect") == 1:
        attitude -= 10
        mes = add_attitude_mes(mes, '自尊心高(-10)')
    # 傲娇
    if npc.has_talent("tsundere"):
        # 傲娇且关系在喜欢以下
        if npc.get_talent_value("relationship") < 2:
            attitude -= 20
            mes = add_attitude_mes(mes, '傲娇(-20)')
        else:
            attitude += 30
            mes = add_attitude_mes(mes, '傲娇(30)')
    # 冷漠
    if npc.has_talent("indifference"):
        attitude -= 30
        mes = add_attitude_mes(mes, '冷漠(-30)')
    # 感情缺乏
    if npc.has_talent("emotional_deficiency"):
        attitude -= 30
        mes = add_attitude_mes(mes, '感情缺乏(-30)')
    # 开朗的
    if npc.has_talent("bright"):
        attitude += 20
        mes = add_attitude_mes(mes, '开朗的(20)')
    # 阴郁的
    if npc.has_talent("morose"):
        attitude -= 20
        mes = add_attitude_mes(mes, '阴郁的(-20)')
    # 难以逾越的底线
    if npc.has_talent("impassable_line") and impassable_line > 0:
        attitude -= impassable_line
        mes = add_attitude_mes(mes, f'难以逾越的底线({-impassable_line})')
    # 不在意目光
    if npc.has_talent("not_minding_the_gaze"):
        attitude += 10
        mes = add_attitude_mes(mes, '不在意目光(10)')
    # 自己爱解放/压抑
    temp = npc.get_talent_value("self_love") * 20
    if temp != 0:
        attitude += temp
        mes = add_attitude_mes(
            mes, f'{npc.get_talent_name("self_love")}({temp})')
    # 抵抗
    if npc.has_talent("resistance"):
        attitude -= 30
        mes = add_attitude_mes(
            mes, f'{npc.get_talent_name("resistance")}(-30)')
    # 羞耻心(-1不知羞耻 1害羞)
    temp = -npc.get_talent_value("shame") * 2
    if temp != 0:
        attitude += temp
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("shame")}({temp})')
    # 献身的
    if npc.has_talent("devoted"):
        attitude += 30
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("devoted")}(+30)')
    # 玩家魅力
    if player.get_talent_value("charm") != 0:
        temp = player.get_talent_value("charm") * 20
        attitude += temp
        mes = add_attitude_mes(mes, f"玩家魅力({temp})")
    # ===================================== 刻印 =====================================
    # 屈服&快乐刻印
    temp = npc.mark['submission_mark'] * 20 + npc.mark['pleasure_mark'] * 20
    attitude += temp
    mes = add_attitude_mes(mes, f'屈服&快乐刻印({temp})')
    # 失望刻印
    temp = npc.mark['disappointment_mark'] * 30
    attitude -= temp
    mes = add_attitude_mes(mes, f'失望刻印({-temp})')
    # TODO: cflag

    return mes, attitude


def ejaculation_proc(ctx: CommandContext, position: str = '身体', check_orgasm: bool = True):
    """射精判定"""
    player = ctx.world.player
    train = ctx.world.train_manager.train
    if train is None:
        return

    from game_engine.data_pipeline.palam.ejaculation_calc import ejaculation_check

    if not ejaculation_check(player):
        return

    player.set_exp('ejaculation_exp', player.get_exp('ejaculation_exp') + 1)
    player.set_vitality(player.get_vitality() - EJACULATION_VITALITY_COST)
    ctx.say_block('palam', c_ejaculation(f'{player.name}射精了！（{position}）'))
    # 射精主导权衰减
    if train.initiative:
        decay_mes = initiative_ejaculation_proc(train, player)
        if decay_mes:
            ctx.say_block('palam', decay_mes)

    semen_src = new_source(SEMEN_SOURCES.get(position, {}))
    for target_id in train.targets:
        chara = get_entity_by_id(player, target_id)
        if not isinstance(chara, ShipGirl):
            continue
        chara.set_exp('semen_exp', chara.get_exp('semen_exp') + 1)
        chara.set_exp('v_semen_exp', chara.get_exp('v_semen_exp') + 1)
        say_chara_line(chara, ctx, 'ejaculation', block='palam')

        source = common_src_modify(semen_src.copy(), chara)
        mes_source, mes_target, _ = palam_calc(source, player, chara,
                                               self_initiative=ctx.world.train_manager.initiative_cmp(player.id, chara.id))
        if mes_target:
            ctx.say_block('palam', *mes_target)
        if check_orgasm:
            orgasm_mes, org_lv, org_num = orgasm_check_parts(chara)
            if orgasm_mes:
                ctx.say_block('palam', *orgasm_mes)
                # 绝顶主导权衰减（按最高等级 × 部位数）
                if train.initiative:
                    decay_mes = initiative_orgasm_proc(
                        train, chara, max(org_lv.values()), org_num)
                    if decay_mes:
                        ctx.say_block('palam', decay_mes)
            chara.update_palam_level()
            emotion_rationality_calc(source, chara)
        favor_trust_proc(source, chara, ctx, block='favor',
                         is_ejaculation=True)

    for palam in ORGASM_BASE.keys():
        # 射精后清空所有部位快感
        player.palam[palam] = 0
    player.update_palam_level()
    if player.get_vitality() == 0:
        ctx.world.train_manager.end_train()
        ctx.say_block('palam', '精力耗尽，本次调教强制结束……')


def work_abl_modifier(abl: int, works: int):
    """工作abl加成"""
    match abl:
        case 1:
            works *= 1.25
        case 2:
            works *= 1.5
        case 3:
            works *= 1.75
        case 4:
            works *= 2
        case 5:
            works *= 2.5
        case 6:
            works *= 3

    return int(works)


def data_score_calc(npc: ShipGirl):
    """约会得分计算"""
    # 刻印
    score = npc.mark['submission_mark'] * 10 + npc.mark['pleasure_mark'] * 10
    # 喜欢及以上
    if npc.get_talent_value('relationship') >= 2:
        intimacy_score = min(npc.abl['intimacy_abl'] * 10, 100)  # 亲密
        desire_score = min(npc.abl['desire_abl'] * 10, 100)  # 欲望
        servant_score = min(npc.abl['servant_abl'] * 10, 100)  # 侍奉精神
        dating_exp_score = min(npc.exp['date_exp'], 100)  # 约会经验
        love_exp_score = min(npc.exp['love_exp'], 100)  # 爱情经验
        score += intimacy_score + desire_score + \
            servant_score + dating_exp_score + love_exp_score
    elif npc.get_talent_value('relationship') == 1:
        # 友好
        intimacy_score = min(npc.abl['intimacy_abl'] * 10, 50)  # 亲密
        desire_score = min(npc.abl['desire_abl'] * 10, 50)  # 欲望
        servant_score = min(npc.abl['servant_abl'] * 10, 50)  # 侍奉精神
        dating_exp_score = min(npc.exp['date_exp'], 50)  # 约会经验
        love_exp_score = min(npc.exp['love_exp'], 50)  # 爱情经验
        score += intimacy_score + desire_score + \
            servant_score + dating_exp_score + love_exp_score
    # palam
    lust_palam_lv = min(npc.palam_lv['lust_palam'], 10) * 5
    kindness_palam_lv = min(npc.palam_lv['kindness_palam'], 10) * 5
    obedience_palam_lv = min(npc.palam_lv['obedience_palam'], 10) * 5
    score += lust_palam_lv + kindness_palam_lv + obedience_palam_lv
    # 情绪/理性
    score += npc.base['emotion'] // 50 + \
        (MAX_RATIONALITY - npc.base['rationality']) // 30
    # talent
    score += npc.get_talent_value('courage') * 10 + npc.get_talent_value('sexual_interest') * 10\
        - npc.get_talent_value('self_control') * 10 - \
        npc.get_talent_value('indifference') * 10

    return score

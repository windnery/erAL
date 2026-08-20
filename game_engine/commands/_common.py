from collections import defaultdict

from config.abl_config import ABL_LV
from config.attr_defs import ATTR_DEFS
from config.base_config import MAX_RATIONALITY
from config.chara_config import PLAYER_ID
from config.source_config import ALL_SOURCE_KEYS
from game_engine.commands._context import CommandContext

def say_chara_line(chara, ctx: CommandContext, action: str):
    """输出角色口上场景（按角色色逐条染色）；无口上时静默。"""
    from game_engine.dialogue import get_scene

    scene = get_scene(chara, action)
    if scene:
        for msg in scene:
            ctx.say(msg.replace('{name}', chara.name), color=getattr(chara, 'color', '#ffffff'))


from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.orgasm_calc import orgasm_check
from config.palam_config import EJACULATION_VITALITY_COST, SEMEN_SOURCES
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
from game_engine.data_pipeline.trust.trust_calc import trust_calc
from game_engine.managers.NpcManager import NpcManager
from game_engine.managers.TrainManager import TrainManager
from game_engine.models.character import Character
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl

def new_source(base: dict[str, int]):
    """根据base生成新的source"""
    s = {k: 0 for k in ALL_SOURCE_KEYS}
    if base: s.update(base)
    return s


def source_proc(source: dict[str, int], actor: Character, target: Character, ctx: CommandContext):
    """source的统一转换过程（单对）"""
    # source->palam
    mes_source, mes_target, _ = palam_calc(source, actor, target)
    for mes in mes_source:
        ctx.say(mes)
    for mes in mes_target:
        ctx.say(mes)
    # 绝顶判定
    ctx.say(*orgasm_check(target))
    # 更新palam等级
    actor.update_palam_level()
    target.update_palam_level()
    # source->情绪/理性
    if target.id != PLAYER_ID:
        # 只有舰娘有情绪/理性
        emotion_rationality_calc(source, target)


def source_proc_batch(pairs: list[tuple[dict[str, int], Character, Character]], ctx: CommandContext):
    """source的统一转换过程（批量，多对 (source, actor, target)）
    数值：每对依次累计（保持笛卡尔积多次累计语义）
    输出：按角色聚合后统一打印一次（同一角色只出现一次）
    绝顶/等级/情绪理性：每个角色实例执行一次（去重）
    """
    if not pairs:
        return

    # 收集所有对的增量（dry_run 不改 palam）
    per_chara: dict[int, dict[str, int]] = {}  # id(chara) -> {palam_key: delta}
    source_of: dict[int, dict[str, int]] = {}  # id(target) -> 该角色收到的 source（用于情绪/理性）
    targets_order: list[int] = []  # 保持 target 出现顺序
    actors_order: list[int] = []

    for source, actor, target in pairs:
        _, _, changes = palam_calc(source, actor, target, dry_run=True)
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

    # 统一应用 + 按角色打印一次
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
            mes.append(f'{ATTR_DEFS["palam"][palam]["name"]} {chara.palam[palam]} + {delta} = {chara.palam[palam] + delta}')
            chara.palam[palam] += delta
        if len(mes) > 1:
            ctx.say(*mes)

    # 绝顶/等级/情绪理性：每个角色实例一次（去重）
    processed: set[int] = set()
    for _, actor, target in pairs:
        # target 侧
        tid = id(target)
        if tid not in processed:
            processed.add(tid)
            ctx.say(*orgasm_check(target))
            target.update_palam_level()
            if target.id != PLAYER_ID and tid in source_of:
                emotion_rationality_calc(source_of[tid], target)
        # actor 侧
        aid = id(actor)
        if aid not in processed:
            processed.add(aid)
            actor.update_palam_level()


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

def get_revision(raw_num: int, limit: int, revision_rate: int|float) -> int:
    """获取修正后的数值"""
    return int(limit - limit * revision_rate / (revision_rate + raw_num))


def get_name_by_id(npc_manager: NpcManager, player: Player, chara_id: str):
    """通过id获取角色名"""
    if chara_id == player.id:
        return player.name
    npc = npc_manager.get_npc_by_id(chara_id)
    if npc:
        return npc.name
    else:
        return chara_id


def get_entity_by_id(npc_manager: NpcManager, player: Player, chara_id: str):
    """通过id获取角色"""
    return npc_manager.get_npc_by_id(chara_id) if chara_id != PLAYER_ID else player


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
            chara = train_manager.npc_manager.get_npc_by_id(source) if source != PLAYER_ID else train.player
            if chara.is_energy_empty():
                return False
    else:
        return False

    return True


def accumulate_sources(dict_iterable) -> dict[str, int | float]:
    result = defaultdict(int)
    if isinstance(dict_iterable, dict):
        dict_iterable = dict_iterable.values()
    for inner_dict in dict_iterable:
        for key, value in inner_dict.items():
            result[key] += value
    return dict(result)


def favor_trust_proc(source: dict[str, int], npc: ShipGirl, ctx: CommandContext, is_intimate: bool = False,
                     ex_favor: int = 0, ex_trust: int = 0):
    """处理好感和信赖"""
    favor_delta = favor_calc(npc, source)
    trust_delta = trust_calc(npc, source)
    # 亲昵指令额外判断好感度和亲密
    if is_intimate:
        favor_delta += low_intimacy2favor(npc.abl['intimacy_abl'])
        favor_delta += low_favor2favor(npc.favor)
    favor_delta += ex_favor
    trust_delta += ex_trust
    npc.favor += favor_delta
    npc.trust += trust_delta

    if favor_delta > 0:
        ctx.say(f'好感+{favor_delta} ({npc.name})')
    elif favor_delta < 0:
        ctx.say(f'好感{favor_delta} ({npc.name})')
    if trust_delta > 0:
        ctx.say(f'信赖+{trust_delta} ({npc.name})')
    elif trust_delta < 0:
        ctx.say(f'信赖{trust_delta} ({npc.name})')


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
        source['pain_source'] *= 1.2
        source['disgust_source'] *= 1.5
    elif chara.palam_lv['lubrication_palam'] < 2:
        source['pain_source'] *= 0.7
        source['disgust_source'] *= 1.2
    elif chara.palam_lv['lubrication_palam'] < 3:
        source['pain_source'] *= 0.4
    elif chara.palam_lv['lubrication_palam'] < 4:
        source['pain_source'] *= 0.2
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
        source['pain_source'] *= 1.2
        source['disgust_source'] *= 2.0
    elif chara.palam_lv['lubrication_palam'] < 2:
        source['disgust_source'] *= 1.5
    elif chara.palam_lv['lubrication_palam'] < 3:
        source['pain_source'] *= 0.6
    elif chara.palam_lv['lubrication_palam'] < 4:
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
    # 好感度
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
    # 信赖
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
    # 情绪&理性
    temp = npc.get_emotion() // 25 + (MAX_RATIONALITY - npc.get_rationality()) // 25
    attitude += temp
    mes = add_attitude_mes(mes, f'情绪&理性({temp})')
    # 陷落阶段
    temp = npc.get_talent_value("relationship") * 50
    attitude += temp
    mes = add_attitude_mes(mes, f'{npc.get_talent_name("relationship")}({temp})')
    """abl"""
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
    """palam"""
    # 亲密
    t = npc.palam_lv['kindness_palam'] * 5
    attitude += t
    mes = add_attitude_mes(mes, f'好意({t})') if t != 0 else mes
    # 欲望
    t = npc.palam_lv['lust_palam'] * 5
    attitude += t
    mes = add_attitude_mes(mes, f'欲望({t})') if t != 0 else mes
    """talent"""
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
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("self_love")}({temp})')
    # 抵抗
    if npc.has_talent("resistance"):
        attitude -= 30
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("resistance")}(-30)')
    # 羞耻心(-1不知羞耻 1害羞)
    temp = -npc.get_talent_value("shame") * 2
    if temp != 0:
        attitude += temp
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("sense_of_shame")}({temp})')
    # 献身的
    if npc.has_talent("devoted"):
        attitude += 30
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("devoted")}(+30)')
    # 玩家魅力
    if player.get_talent_value("charm") != 0:
        temp = player.get_talent_value("charm") * 20
        attitude += temp
        mes = add_attitude_mes(mes, f"玩家魅力({temp})")
    # TODO: 刻印
    # TODO: cflag
    # 约会中
    if npc.is_dating():
        attitude += 40
        mes = add_attitude_mes(mes, '约会中(40)')

    return mes, attitude


def ejaculation_proc(world, ctx: CommandContext, position: str = '中出'):
    """射精判定"""
    player = world.player
    train = world.train_manager.train
    if train is None:
        return

    from game_engine.data_pipeline.palam.ejaculation_calc import ejaculation_check

    if not ejaculation_check(player):
        return

    player.set_exp('ejaculation_exp', player.get_exp('ejaculation_exp') + 1)
    player.set_vitality(player.get_vitality() - EJACULATION_VITALITY_COST)
    ctx.say(f'{player.name}射精了！（{position}）')

    semen_src = new_source(SEMEN_SOURCES.get(position, {}))
    for target_id in train.targets:
        if target_id == PLAYER_ID:
            continue
        chara = get_entity_by_id(world.npc_manager, player, target_id)
        chara.set_exp('semen_exp', chara.get_exp('semen_exp') + 1)
        chara.set_exp('v_semen_exp', chara.get_exp('v_semen_exp') + 1)
        say_chara_line(chara, ctx, 'ejaculation')

        source = common_src_modify(semen_src.copy(), chara)
        source_list = [f'{chara.name} ']
        for key, value in source.items():
            if value:
                source_list.append(f"{ATTR_DEFS['source'][key]['name']}({value})")
        ctx.say(' '.join(source_list))
        source_proc(source, player, chara, ctx)
        favor_trust_proc(source, chara, ctx)

    player.palam['m_pleasure_palam'] = 0
    player.update_palam_level()
    if player.get_vitality() == 0:
        world.train_manager.end_train()
        ctx.say('精力耗尽，本次调教强制结束……')
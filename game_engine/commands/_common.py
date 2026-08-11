from config.base_config import MAX_RATIONALITY
from config.source_config import ALL_SOURCE_KEYS
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.palam.palam_calc import palam_calc
from game_engine.data_pipeline.base.emo_rat_calc import emotion_rationality_calc
from game_engine.data_pipeline.trust.trust_calc import trust_calc
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl


def new_source(base: dict[str, int]):
    """根据base生成新的source"""
    s = {k: 0 for k in ALL_SOURCE_KEYS}
    if base: s.update(base)
    return s

def source_proc(source: dict[str, int], player: Player, npc: ShipGirl, ctx: CommandContext):
    """source的统一转换过程"""
    # source->palam
    mes_source, mes_target = palam_calc(source, player, npc)
    for mes in mes_source:
        ctx.say(mes)
    for mes in mes_target:
        ctx.say(mes)
    # 更新palam等级
    player.update_palam_level()
    npc.update_palam_level()
    # source->情绪/理性
    emotion_rationality_calc(source, npc)


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


def global_can(player: Player, npc: ShipGirl):
    """指令不可用的通用判定 优先级最高"""
    # 气力0
    if player.is_energy_empty():
        return False
    # 睡眠中
    if npc.is_sleeping():
        return False

    return True


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
        mes = add_attitude_mes(mes, '好感(0)')
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
        mes = add_attitude_mes(mes, '信赖(0)')
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
    mes = add_attitude_mes(mes, f'亲密({temp})')
    # 欲望
    temp = npc.abl['desire_abl'] * 5
    attitude += temp
    mes = add_attitude_mes(mes, f'欲望({temp})')
    # 恭顺
    temp = npc.abl['obedience_abl'] * 5
    attitude += temp
    mes = add_attitude_mes(mes, f'恭顺({temp})')
    # 侍奉精神
    temp = npc.abl['servant_abl'] * 5
    attitude += temp
    mes = add_attitude_mes(mes, f'侍奉精神({temp})')
    """palam"""
    # 亲密
    attitude += npc.palam_lv['kindness_palam'] * 5
    mes = add_attitude_mes(mes, f'好意({npc.palam_lv["kindness_palam"] * 5})')
    # 欲望
    attitude += npc.palam_lv['lust_palam'] * 5
    mes = add_attitude_mes(mes, f'欲望({npc.palam_lv["lust_palam"] * 5})')
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
    attitude += temp
    mes = add_attitude_mes(mes, f'{npc.get_talent_name("self_love")}({temp})')
    # 抵抗
    if npc.has_talent("resistance"):
        attitude -= 30
        mes = add_attitude_mes(mes, f'{npc.get_talent_name("resistance")}(-30)')
    # 羞耻心(-1不知羞耻 1害羞)
    temp = -npc.get_talent_value("shame") * 2
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
    # TODO: 情绪/理性
    # TODO: 刻印
    # TODO: cflag
    # 约会中
    if npc.is_dating():
        attitude += 40
        mes = add_attitude_mes(mes, '约会中(40)')

    return mes, attitude
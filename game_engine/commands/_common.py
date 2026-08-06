from config.source_kind import ALL_SOURCE_KEYS
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.favor.favor_calc import favor_calc
from game_engine.data_pipeline.trust.trust_calc import trust_calc
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl


def new_source(base: dict[str, int]):
    """根据base生成新的source"""
    s = {k: 0 for k in ALL_SOURCE_KEYS}
    if base: s.update(base)
    return s


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

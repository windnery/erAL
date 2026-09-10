from __future__ import annotations

from typing import TYPE_CHECKING

from data.time.time_data import COMMAND_TIME_DATA
from game_engine.commands._commands import register_cmd
from game_engine.commands._common import (
    add_attitude_mes,
    favor_trust_proc,
    get_attitude,
    new_source,
    say_chara_line,
    source_proc_batch,
)
from game_engine.commands._context import CommandContext
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.exp_calc import exp_calc
from game_engine.models.character import Character
from game_engine.models.shipgirl import ShipGirl
from game_engine.utils.text_color import c_notice

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 气力0
    if world.player.is_energy_empty():
        return False
    # 口被占用
    if npc.body_slots["mouth"] == 0 or world.player.body_slots["mouth"] == 0:
        return False
    # 陷落阶段在喜欢以上 必定可用
    if npc.get_talent_value("relationship") >= 3:
        return True
    # 工作中
    if npc.is_working():
        return False
    # 好感度低
    if npc.favor < 600:
        return False
    # 亲密低
    return not npc.abl["intimacy_abl"] < 6


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    success_score = 200
    mes, score = get_attitude(world.player, npc, 30)

    # 恋人
    if npc.has_talent("lover"):
        score += 60
        mes = add_attitude_mes(mes, "恋人(60)")

    # 无接吻经验
    if npc.get_talent_value("no_kiss_exp"):
        score -= 20
        mes = add_attitude_mes(mes, "无接吻经验(-20)")

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


@register_cmd("kiss_i", "亲吻", "亲昵", can=can)
def kiss_i(world: World, option: str):
    """亲吻
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    ctx.say(f"尝试和{npc.name}接吻……")

    ok, detail = able(world, npc)
    say_chara_line(npc, ctx, "kiss_i", outcome="success" if ok else "fail")
    ctx.say(detail)

    if not ok:
        ctx.say(f"{npc.name}撇过了脸，看来还没有到那一步……")
        source: dict[str, int] = new_source(
            {"fear_source": 500, "disgust_source": 1000}
        )
    else:
        source: dict[str, int] = new_source(
            {
                "happiness_source": 150,
                "love_source": 150,
                "exposure_source": 80,
                "m_pleasure_source": 10,
                "disgust_source": 300,
            }
        )
        feedback_source: dict[str, int] = new_source(
            {
                "m_pleasure_source": 10,
            }
        )
        # 睡觉中
        if npc.is_sleeping():
            source["disgust_source"] = 200
        # abl: 舌
        source["m_pleasure_source"] += world.player.abl["tongue_abl"] * 2
        feedback_source["m_pleasure_source"] += npc.abl["tongue_abl"] * 2
        # abl: 亲密
        if npc.abl["intimacy_abl"] <= 1:
            source["love_source"] += npc.abl["intimacy_abl"] * 30
        elif npc.abl["intimacy_abl"] <= 3:
            source["happiness_source"] += 150 + npc.abl["intimacy_abl"] * 30
            source["love_source"] += 150 + npc.abl["intimacy_abl"] * 30
            source["lust_source"] += 65 + npc.abl["intimacy_abl"] * 20
        elif npc.abl["intimacy_abl"] <= 5:
            source["happiness_source"] += 300 + npc.abl["intimacy_abl"] * 40
            source["love_source"] += 280 + npc.abl["intimacy_abl"] * 30
            source["lust_source"] += 130 + npc.abl["intimacy_abl"] * 26
            source["exposure_source"] += 80 + npc.abl["intimacy_abl"] * 15
        elif npc.abl["intimacy_abl"] <= 8:
            source["happiness_source"] += 450 + npc.abl["intimacy_abl"] * 70
            source["love_source"] += 380 + npc.abl["intimacy_abl"] * 40
            source["lust_source"] += 170 + npc.abl["intimacy_abl"] * 30
            source["exposure_source"] += 110 + npc.abl["intimacy_abl"] * 18
        else:
            source["happiness_source"] += 500 + npc.abl["intimacy_abl"] * 85
            source["love_source"] += 480 + npc.abl["intimacy_abl"] * 50
            source["lust_source"] += 230 + npc.abl["intimacy_abl"] * 35
            source["exposure_source"] += 160 + npc.abl["intimacy_abl"] * 20
        # 好感度
        if npc.favor <= 500:
            source["love_source"] += npc.favor
        elif npc.favor <= 5000:
            source["love_source"] += 400 + (npc.favor - 500) // 5
            source["happiness_source"] += 400 + (npc.favor - 500) // 4
        else:
            source["love_source"] += 1200 + (npc.favor - 5000) // 7
            source["happiness_source"] += 1200 + (npc.favor - 5000) // 4
        # 约会中
        if npc.is_dating():
            source["love_source"] = int(source["love_source"] * 1.5)
            source["passivity_source"] += 100 + 200 * npc.abl["obedience_abl"]
            source["conquest_source"] += 100 + 200 * npc.abl["sadism_abl"]
            # 约会经验
            ctx.say_exp(exp_calc("date_exp", world.player))
            ctx.say_exp(exp_calc("date_exp", npc))
        # 旁人在场
        if world.npc_manager.with_mob(npc.location["region"], npc.location["node"]):
            source["happiness_source"] = int(source["happiness_source"] * 0.7)
            source["love_source"] = int(source["love_source"] * 0.8)
            source["conquest_source"] = int(source["conquest_source"] * 0.8)
            source["passivity_source"] = int(source["passivity_source"] * 0.9)
            source["exposure_source"] = int(source["exposure_source"] * 1.1)
            ctx.say(c_notice(f"有旁人在场，{npc.name}似乎有些害羞……"))
        else:
            source["happiness_source"] = int(source["happiness_source"] * 1.2)
            source["love_source"] = int(source["love_source"] * 1.2)
            source["conquest_source"] = int(source["conquest_source"] * 1.2)
            source["passivity_source"] = int(source["passivity_source"] * 1.2)

        # exp: 接吻经验
        ctx.say_exp(exp_calc("kiss_exp", world.player))
        ctx.say_exp(exp_calc("kiss_exp", npc))
        ctx.say_exp(exp_calc("m_exp", world.player))
        ctx.say_exp(exp_calc("m_exp", npc))

    # 推进时间
    ctx.advance_time(COMMAND_TIME_DATA["kiss_i"])

    # 通用source修正
    source = common_src_modify(source, npc)
    ctx.say_source(source, npc.name)
    pairs: list[tuple[dict[str, int], Character, Character]] = [(source, world.player, npc)]
    
    if ok:
        feedback_source = common_src_modify(feedback_source, world.player)
        pairs.append((feedback_source, npc, world.player))
        ctx.say_source(feedback_source, world.player.name)

    # 统一转换source
    source_proc_batch(pairs, ctx)


    # 体力和气力消耗
    if npc.is_dating():
        ctx.consume(energy=30, chara=npc)
        ctx.consume(energy=50, chara=world.player)
    else:
        ctx.consume(energy=70, chara=npc)
        ctx.consume(energy=100, chara=world.player)

    # 好感和信赖处理
    if not ok:
        ex_favor = 0
        if npc.favor <= 500:
            ex_favor = -50
        elif npc.favor <= 1000:
            ex_favor = -30
        elif npc.favor <= 2000:
            ex_favor = -10
    else:
        ex_favor = 0
        if npc.favor <= 100:
            ex_favor = -3
        elif npc.favor <= 300:
            ex_favor = -2
        elif npc.favor <= 500:
            ex_favor = -1

    favor_trust_proc(source, npc, ctx, True, ex_favor=ex_favor)

    return ctx.result()

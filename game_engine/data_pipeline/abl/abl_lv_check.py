from config.juel import get_juel_demand
from config.abl_lv import EXP2ABL, ABL_LV, JUEL2ABL_MAX_LV, EXP2ABL_MAX_LV
from game_engine.models.character import Character


# abl升级处理
def abl_lv_process(chara: Character, attr_defs):
    mes = []
    mes.extend(juel2abl(chara, attr_defs))
    mes.extend(exp2abl(chara, attr_defs))
    return mes


# 检查juel是否达到升级需求
def juel2abl(chara: Character, attr_defs):
    mes: list[str] = []
    for abl_k in get_juel_demand(chara):
        while chara.abl[abl_k] < JUEL2ABL_MAX_LV:
            demand = get_juel_demand(chara)[abl_k]  # 每级重算，真正生效
            if not any(chara.juel[k] >= v != -1 for k, v in demand.items()):
                # 每一个juel都不足，无法升级
                break
            chara.abl[abl_k] += 1
            for k, v in demand.items():
                # 扣除第一个满足的juel
                if chara.juel[k] >= v != -1:
                    chara.juel[k] -= v
                    break
            mes.append(f"{chara.name}的{attr_defs['abl'][abl_k]['name']}提升到了{chara.abl[abl_k]}！")
    return mes


# 检查exp是否达到升级需求
def exp2abl(chara: Character, attr_defs):
    mes: list[str] = []

    for exp_k in EXP2ABL:
        abl_k = exp_k.replace('exp', 'abl')
        while (
                chara.abl[abl_k] != EXP2ABL_MAX_LV and
                chara.exp[exp_k] >= ABL_LV[chara.abl[abl_k] + 1]
        ):
            chara.abl[abl_k] += 1
            mes.append(f'{chara.name}的{attr_defs["abl"][abl_k]["name"]}提升到了{chara.abl[abl_k]}！')
    return mes

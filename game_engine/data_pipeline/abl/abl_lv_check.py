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

    juel_demand = get_juel_demand(chara)
    for abl_k, juel in juel_demand.items():
        can_up = True
        if chara.abl[abl_k] == JUEL2ABL_MAX_LV:
            # abl达到上限
            continue
        # TODO: 最高等级判定
        while can_up:
            for k in juel.keys():
                if chara.juel[k] < juel[k]:
                    can_up = False
                    break
            if can_up:
                chara.abl[abl_k] += 1
                mes.append(f"{chara.name}的{attr_defs['abl'][abl_k]['name']}提升到了{chara.abl[abl_k]}！")
                for k in juel.keys():
                    chara.juel[k] -= juel[k]
    return mes


# 检查exp是否达到升级需求
def exp2abl(chara: Character, attr_defs):
    mes: list[str] = []

    for exp_k in EXP2ABL:
        abl_k = exp_k.replace('exp', 'abl')
        if chara.exp[exp_k] == EXP2ABL_MAX_LV:
            # abl达到上限
            continue
        while chara.exp[exp_k] > ABL_LV[chara.abl[abl_k] + 1]:
            chara.abl[abl_k] += 1
            mes.append(f'{chara.name}的{attr_defs["abl"][abl_k]["name"]}提升到了{chara.abl[abl_k]}！')
    return mes

from config.attr_defs import ATTR_DEFS
from config.juel_config import get_juel_demand
from config.abl_config import EXP2ABL, ABL_LV, JUEL2ABL_MAX_LV, EXP2ABL_MAX_LV
from game_engine.models.character import Character


# 感觉升至指定等级所需的对应部位绝顶经验阈值
SEN_ABL_ORGASM_DEMAND: dict[int, int] = {
    3: 1,
    4: 5,
    5: 15,
    6: 30,
    7: 50,
}


def check_abl_prerequisites(chara: Character, abl_k: str) -> bool:
    """检查 ABL 升级前置条件链

    欲望 (desire_abl) 升级受 顺从 (obedience_abl) 限制：欲望等级不可超过顺从等级
    侍奉精神 (servant_abl) 升级受 亲密 (intimacy_abl) 限制：侍奉精神等级不可超过亲密等级
    C/V/A/B/M 感觉升至 3 级及以上时需要对应部位的绝顶经验达到阈值
    """
    cur_lv = chara.abl.get(abl_k, 0)
    target_lv = cur_lv + 1

    # 欲望升级受顺从限制
    if abl_k == 'desire_abl':
        if chara.abl.get('obedience_abl', 0) < cur_lv:
            return False

    # 侍奉精神升级受亲密限制
    elif abl_k == 'servant_abl':
        if chara.abl.get('intimacy_abl', 0) < cur_lv:
            return False

    # 感觉升至 3 级及以上受对应部位绝顶经验限制
    elif abl_k in ('c_sen_abl', 'v_sen_abl', 'a_sen_abl', 'b_sen_abl', 'm_sen_abl'):
        if target_lv >= 3:
            req_exp = SEN_ABL_ORGASM_DEMAND.get(target_lv, 50 + (target_lv - 7) * 30)
            part = abl_k.split('_')[0]
            actual_exp = chara.exp.get(f'{part}_orgasm_exp', 0)
            if actual_exp < req_exp:
                return False

    return True


# abl升级处理
def abl_lv_process(chara: Character, attr_defs):
    mes = []
    mes.extend(juel2abl(chara))
    mes.extend(exp2abl(chara))
    return mes


# 检查juel是否达到升级需求
def juel2abl(chara: Character):
    mes: list[str] = []
    for abl_k in get_juel_demand(chara):
        while chara.abl[abl_k] < JUEL2ABL_MAX_LV:
            if not check_abl_prerequisites(chara, abl_k):
                break
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
            mes.append(f"[[c:#ffd400]]{chara.name}的{ATTR_DEFS['abl'][abl_k]['name']}提升到了{chara.abl[abl_k]}！[[/c]]")
    return mes


# 检查exp是否达到升级需求
def exp2abl(chara: Character):
    mes: list[str] = []

    for exp_k in EXP2ABL:
        abl_k = exp_k.replace('exp', 'abl')
        while (
                chara.abl[abl_k] < EXP2ABL_MAX_LV and
                (chara.abl[abl_k] + 1) in ABL_LV and
                chara.exp[exp_k] >= ABL_LV[chara.abl[abl_k] + 1]
        ):
            chara.abl[abl_k] += 1
            mes.append(f'[[c:#ffd400]]{chara.name}的{ATTR_DEFS["abl"][abl_k]["name"]}提升到了{chara.abl[abl_k]}！[[/c]]')
    return mes

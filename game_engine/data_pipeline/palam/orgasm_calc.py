from config.juel_config import JUEL_GET
from config.palam_config import ORGASM_BASE, ORGASM_LV_CN, ORGASM_LV_JUEL_MODIFIER, ORGASM_NUM_CN, ORGASM_NUM_JUEL_MODIFIER
from game_engine.models.shipgirl import ShipGirl


def orgasm_proc(orgasm_lv: dict[str, int], target: ShipGirl, orgasm_num: int):
    """绝顶处理"""
    mes: list[str] = []
    mark_mes: str = ''
    climaxed = [(palam_id, lv) for palam_id, lv in orgasm_lv.items() if lv > 0]
    for palam_id, lv in climaxed:
        part = palam_id[0].upper()  # 绝顶部位
        text = orgasm_lv_print(part, lv)
        mes.append(f'[[c:#ff6fae]]{text}[[/c]]')
        # 快乐刻印判定（刻印最高lv3，与其它刻印一致）
        if lv > target.mark['pleasure_mark'] and target.mark['pleasure_mark'] < 3:
            self_plv = min(lv, 3)
            target.mark['pleasure_mark'] = self_plv
            mark_mes = f'[[c:#ffd400]]{target.name}获得了快乐刻印lv{self_plv}！[[/c]]'
        # 绝顶后palam和juel处理
        orgasm_palam_juel_proc(palam_id, target, orgasm_num, lv)
    climaxed_lv = [lv for _, lv in climaxed]
    if orgasm_num >= 2 and len(set(climaxed_lv)) == 1:
        lv = climaxed_lv[0]
        text = f'{ORGASM_NUM_CN[orgasm_num]}{ORGASM_LV_CN[lv]}！（各部位珠子加成）'
        mes.append(f'[[c:#ff6fae]]{text}[[/c]]')
    if mark_mes:
        mes.append(mark_mes)
    return mes


def orgasm_lv_print(part: str, orgasm_lv: int):
    """绝顶等级打印"""
    mes = ''
    if orgasm_lv == 1:
        mes = f"{part}{ORGASM_LV_CN[orgasm_lv]}！"
    elif orgasm_lv == 2:
        mes = f"{part}{ORGASM_LV_CN[orgasm_lv]}！（珠子加成）"
    elif orgasm_lv == 3:
        mes = f"{part}{ORGASM_LV_CN[orgasm_lv]}！（珠子大加成）"
    elif orgasm_lv == 4:
        mes = f"{part}{ORGASM_LV_CN[orgasm_lv]}！（珠子特大加成）"
    return mes


def orgasm_palam_juel_proc(palam_id: str, target: ShipGirl, orgasm_num: int = 1, orgasm_lv: int = 1):
    """绝顶palam juel处理"""
    # 绝顶部位palam减半
    _palam = target.palam[palam_id] // 2
    # 获取juel
    juel_id = palam_id.replace('palam', 'juel')
    best = 0
    for _palam_lv, juel in JUEL_GET.items():
        if _palam >= _palam_lv:
            best = juel
        else:
            break
    modifier = ORGASM_NUM_JUEL_MODIFIER.get(orgasm_num, 1.0) * ORGASM_LV_JUEL_MODIFIER.get(orgasm_lv, 1.0)
    target.juel[juel_id] += int(best * modifier)

    target.palam[palam_id] -= _palam


def orgasm_check(target: ShipGirl):
    """绝顶检查"""
    mes = []
    orgasm_lv = {
        # 绝顶等级 最大4
        'c_pleasure_palam': 0,
        'v_pleasure_palam': 0,
        'a_pleasure_palam': 0,
        'b_pleasure_palam': 0,
        'm_pleasure_palam': 0,
    }
    orgasm_num = 0  # 绝顶部位数

    for part, orgasm_demands in ORGASM_BASE.items():
        for orgasm_demand in orgasm_demands:
            if target.palam[part] >= orgasm_demand:
                orgasm_lv[part] += 1
            else:
                break
        if orgasm_lv[part] > 0:
            # 绝顶部位数+1
            orgasm_num += 1

    if orgasm_num > 0:
        # 绝顶
        mes = orgasm_proc(orgasm_lv, target, orgasm_num)

    return mes

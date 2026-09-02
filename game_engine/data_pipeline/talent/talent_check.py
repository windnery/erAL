from __future__ import annotations
from typing import TYPE_CHECKING
from config.chara_config import PLAYER_ID
from game_engine.models.character import Character
from game_engine.models.shipgirl import ShipGirl
from config.talent_config import RELATIONSHIP
from game_engine.utils.text_color import c_talent

if TYPE_CHECKING:
    from world import World


def talent_check(world: World, npc: Character) -> list[str]:
    """检查天赋获取和消失"""
    mes = []
    # 先检查不带TODO的部分
    mes.extend(_relationship(world, npc))
    mes.extend(_attitude(world, npc))
    mes.extend(_self_respect(world, npc))
    mes.extend(_indifference(world, npc))
    mes.extend(_self_love(world, npc))
    mes.extend(_morose(world, npc))
    mes.extend(_resistance(world, npc))
    mes.extend(_flexible_fingers(world, npc))
    mes.extend(_flexible_tongue(world, npc))
    mes.extend(_devoted(world, npc))
    mes.extend(_vaginal_fan(world, npc))
    mes.extend(_anal_fan(world, npc))
    mes.extend(_breast_fan(world, npc))
    mes.extend(_oral_fan(world, npc))

    return mes


def _relationship(world: World, chara: ShipGirl):
    """陷落阶段"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    cur = chara.get_talent_value('relationship')
    # 爱(3)已是自动升级最高阶段，后续需通过道具（誓约）提升
    if cur >= 3:
        return mes

    if (
        # 爱
        cur < 3 and
        chara.favor >= RELATIONSHIP['3']['favor'] and
        chara.trust >= RELATIONSHIP['3']['trust'] and
        chara.abl['intimacy_abl'] >= RELATIONSHIP['3']['intimacy_abl']
    ):
        chara.set_talent('relationship', '3')
        mes.append(
            f'{chara.name}最近似乎更在意{world.player.name}了……{chara.name}和{world.player.name}的关系变成了{c_talent("[爱]")}！')
    elif (
        # 喜欢
        cur < 2 and
        chara.favor >= RELATIONSHIP['2']['favor'] and
        chara.trust >= RELATIONSHIP['2']['trust'] and
        chara.abl['intimacy_abl'] >= RELATIONSHIP['2']['intimacy_abl']
    ):
        chara.set_talent('relationship', '2')
        mes.append(
            f'{chara.name}最近似乎更在意{world.player.name}了……{chara.name}和{world.player.name}的关系变成了{c_talent("[喜欢]")}！')
    elif (
        # 友好
        cur < 1 and
        chara.favor >= RELATIONSHIP['1']['favor'] and
        chara.trust >= RELATIONSHIP['1']['trust'] and
        chara.abl['intimacy_abl'] >= RELATIONSHIP['1']['intimacy_abl']
    ):
        chara.set_talent('relationship', '1')
        mes.append(
            f'{chara.name}最近似乎更在意{world.player.name}了……{chara.name}和{world.player.name}的关系变成了{c_talent("[友好]")}！')

    return mes


def _attitude(world: World, chara: ShipGirl):
    """态度"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 失去叛逆
    if (
        chara.get_talent_value('attitude') == 1 and  # 叛逆
        chara.abl['intimacy_abl'] >= 6 and  # 亲密达到6
        chara.mark.get('disappointment_mark', 0) == 0 and  # 失望标记为0
        chara.get_talent_value('relationship') >= 2  # 关系达到喜欢
    ):
        chara.set_talent('attitude', '0')
        mes.append(f'{chara.name}不知不觉中变得听从{world.player.name}的话了……')
        mes.append(f'{chara.name}失去了{c_talent("[叛逆]", "common")}！')
    return mes


def _self_respect(world: World, chara: ShipGirl):
    """自尊心"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 失去自尊心高
    if (
        chara.get_talent_value('self_respect') == 1 and  # 自尊心高
        chara.favor >= 2000 and  # 好感度达到2000
        chara.trust >= 500 and  # 信赖度达到500
        chara.abl['obedience_abl'] >= 6  # 顺从达到6
    ):
        chara.set_talent('self_respect', '0')
        mes.append(f'在{world.player.name}的攻势下，{chara.name}的自尊心逐渐被击溃……')
        mes.append(f'{chara.name}失去了{c_talent("[自尊心高]", "common")}！')
    return mes


def _indifference(world: World, chara: ShipGirl):
    """冷漠"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 失去冷漠
    if (
        chara.get_talent_value('indifference') == 1 and  # 冷漠
        chara.favor >= 2000 and  # 好感度达到2000
        chara.trust >= 500 and  # 信赖度达到500
        chara.abl['intimacy_abl'] >= 6  # 亲密达到6
    ):
        chara.set_talent('indifference', '0')
        mes.append(f'{chara.name}在和{world.player.name}的交往中逐渐褪去了冰冷的外壳……')
        mes.append(f'{chara.name}失去了{c_talent("[冷漠]", "common")}！')
    return mes


def _morose(world: World, chara: ShipGirl):
    """阴郁"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 失去阴郁
    if (
        chara.get_talent_value('morose') == 1 and  # 阴郁
        chara.abl['intimacy_abl'] >= 6 and  # 亲密达到6
        chara.mark.get('pleasure_mark', 0) > 0  # 快乐刻印大于0
        # TODO: 需要增加好心情的累计天数判定
    ):
        chara.set_talent('morose', '0')
        mes.append(f'和{world.player.name}度过的日子里让{chara.name}感觉到很快乐……')
        mes.append(f'{chara.name}失去了{c_talent("[阴郁]", "common")}！')

    return mes


def _self_love(world: World, chara: ShipGirl):
    """自己爱"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 失去压抑
    if chara.abl['desire_abl'] >= 7 and chara.get_talent_value('self_love') == -1:
        chara.set_talent('self_love', '0')
        mes.append(f'{chara.name}对{world.player.name}的感觉越来越强烈……再也无法抑制住自己的情感。')
        mes.append(f'{chara.name}失去了{c_talent("[压抑]", 'common')}！')

    return mes


def _resistance(world: World, chara: ShipGirl):
    """抵抗"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 失去抵抗
    if (
        chara.abl['obedience_abl'] >= 7 and
        chara.has_talent('resistance') and
        chara.mark.get('disappointment_mark', 0) == 0
    ):
        chara.set_talent('resistance', '0')
        mes.append(f'{chara.name}变得不再抗拒{world.player.name}的要求……')
        mes.append(f'{chara.name}失去了{c_talent("[抵抗]", 'common')}！')
    return mes


def _flexible_fingers(world: World, chara: Character):
    """灵巧手指"""
    mes: list[str] = []
    # 获得灵巧手指
    if chara.abl['finger_abl'] >= 5:
        chara.set_talent('flexible_fingers', '1')
        mes.append(f'{chara.name}的手指现在无比灵巧……')
        mes.append(f'{chara.name}获得了{c_talent("[灵巧手指]", "common")}！')
    return mes


def _flexible_tongue(world: World, chara: Character):
    """灵巧舌头"""
    mes: list[str] = []
    # 获得灵巧舌头
    if chara.abl['tongue_abl'] >= 5:
        chara.set_talent('flexible_tongue', '1')
        mes.append(f'{chara.name}的舌头现在无比灵巧……')
        mes.append(f'{chara.name}获得了{c_talent("[灵巧舌头]", "common")}！')
    return mes


def _urophilia(world: World, chara: Character):
    """漏尿癖"""
    mes: list[str] = []
    # TODO: 获得漏尿癖
    return mes


def _devoted(world: World, chara: ShipGirl):
    """献身的"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 获得献身的
    obedience_abl = chara.abl['obedience_abl']
    intimacy_abl = chara.abl['intimacy_abl']
    desire_abl = chara.abl['desire_abl']
    submission_mark = chara.mark.get('submission_mark', 0)
    score = obedience_abl + intimacy_abl + desire_abl + submission_mark
    if not chara.has_talent('devoted') and score >= 25:
        chara.set_talent('devoted', '1')
        mes.append(f'{chara.name}的身心都被{world.player.name}征服了……')
        mes.append(f'{chara.name}获得了{c_talent("[献身的]", "common")}！')
    return mes


def _pleasure_response(world: World, chara: Character):
    """快感应答"""
    mes: list[str] = []
    # TODO: 快感应答
    return mes


def _masturbation_fan(world: World, chara: Character):
    """自慰狂"""
    mes: list[str] = []
    # TODO: 获得自慰狂
    return mes


def _vaginal_fan(world: World, chara: ShipGirl):
    """淫壶"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 获得淫壶
    if chara.abl['v_sen_abl'] >= 5 and chara.exp['v_orgasm_exp'] >= 50:
        chara.set_talent('vaginal_fan', '1')
        mes.append(f'{chara.name}的阴道对刺激的反应越来越强烈……')
        mes.append(f'{chara.name}获得了{c_talent("[淫壶]", "common")}！')
    return mes


def _anal_fan(world: World, chara: ShipGirl):
    """淫尻"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 获得淫尻
    if chara.abl['a_sen_abl'] >= 5 and chara.exp['a_orgasm_exp'] >= 50:
        chara.set_talent('anal_fan', '1')
        mes.append(f'{chara.name}的肛门对刺激的反应越来越强烈……')
        mes.append(f'{chara.name}获得了{c_talent("[淫尻]", "common")}！')
    return mes


def _breast_fan(world: World, chara: ShipGirl):
    """淫乳"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 获得淫乳
    if chara.abl['b_sen_abl'] >= 5 and chara.exp['b_orgasm_exp'] >= 50:
        chara.set_talent('breast_fan', '1')
        mes.append(f'{chara.name}的乳房对刺激的反应越来越强烈……')
        mes.append(f'{chara.name}获得了{c_talent("[淫乳]", "common")}！')
    return mes


def _oral_fan(world: World, chara: ShipGirl):
    """淫舌"""
    if chara.id == PLAYER_ID:
        return []
    mes: list[str] = []
    # 获得淫舌
    if chara.abl['m_sen_abl'] >= 5 and chara.exp['m_orgasm_exp'] >= 30:
        chara.set_talent('oral_fan', '1')
        mes.append(f'{chara.name}的嘴巴对刺激的反应越来越强烈……')
        mes.append(f'{chara.name}获得了{c_talent("[淫舌]", "common")}！')
    return mes


def _sadism(world: World, chara: Character):
    """施虐狂"""
    mes: list[str] = []
    # TODO: 获得施虐狂
    return mes


def _masochism(world: World, chara: Character):
    """受虐狂"""
    mes: list[str] = []
    # TODO: 获得受虐狂
    return mes


def _c_sensitivity(world: World, chara: Character):
    """C感度"""
    mes: list[str] = []
    # TODO: C感度
    return mes


def _v_sensitivity(world: World, chara: Character):
    """V感度"""
    mes: list[str] = []
    # TODO: V感度
    return mes


def _a_sensitivity(world: World, chara: Character):
    """A感度"""
    mes: list[str] = []
    # TODO: A感度
    return mes


def _b_sensitivity(world: World, chara: Character):
    """B感度"""
    mes: list[str] = []
    # TODO: B感度
    return mes


def _m_sensitivity(world: World, chara: Character):
    """M感度"""
    mes: list[str] = []
    # TODO: M感度
    return mes


def _bra_size(world: World, chara: Character):
    """胸围"""
    mes: list[str] = []
    # TODO: 胸围
    return mes


def _hip_size(world: World, chara: Character):
    """臀围"""
    mes: list[str] = []
    # TODO: 臀围
    return mes

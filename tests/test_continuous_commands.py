# -*- coding: utf-8 -*-
import pytest
from config.chara_config import PLAYER_ID


@pytest.fixture(autouse=True)
def cleanup_continuous_train(world):
    """持续指令测试结束后清理会话和单例 NPC 的槽位状态。"""
    yield
    if world.train_manager.train is not None:
        world.train_manager.clear_all_continuous_cmds()
        world.train_manager.train = None
        world.train_mode = False
    world.player.reset_body_slots()
    for sg in world.npc_manager.get_all_npcs():
        sg.reset_body_slots()


def test_body_slots_basic(world):
    player = world.player
    assert player.has_body_slots({'hands': 2, 'mouth': 1}) is True
    assert player.has_body_slots({'hands': 3}) is False

    assert player.consume_body_slots({'hands': 1}) is True
    assert player.body_slots['hands'] == 1

    player.restore_body_slots({'hands': 1})
    assert player.body_slots['hands'] == 2

    player.consume_body_slots({'hands': 2})
    player.reset_body_slots()
    assert player.body_slots['hands'] == 2


def test_single_train_command_does_not_consume_slots(world, z23_nearby):
    # 开启调教
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]

    initial_player_hands = world.player.body_slots['hands']
    initial_girl_breasts = z23_nearby.body_slots['breasts']

    # 执行单次爱抚 (caress)
    res = world.command_manager.do_cmd('caress', {'continuous': False})
    assert res is not None

    # 槽位不应被扣减
    assert world.player.body_slots['hands'] == initial_player_hands
    assert len(world.train_manager.train.continuous_commands) == 0


def test_continuous_train_command_consumes_slots_and_ticks(world, z23_nearby):
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 10  # 保证 able 判定通过

    # 执行持续爱抚 (caress: actor hands=1)
    res = world.command_manager.do_cmd('caress', {'continuous': True})
    assert res is not None
    assert world.player.body_slots['hands'] == 1
    assert len(world.train_manager.train.continuous_commands) == 1
    cmd = world.train_manager.train.continuous_commands[0]
    assert cmd.command_key == 'caress'

    # 执行另一个持续指令：胸爱抚（actor hands=1, target breasts=1）
    res2 = world.command_manager.do_cmd('breast_caress', {'continuous': True})
    assert res2 is not None
    assert world.player.body_slots['hands'] == 0  # 2手都被占用
    assert z23_nearby.body_slots['breasts'] == 1
    assert len(world.train_manager.train.continuous_commands) == 2

    # 再尝试获取调教指令列表，需要手的指令（如揉胸、指插入、肛门爱抚）can 判定应失败，不在列表中
    can_train_cmds = world.train_manager.get_train_commands()
    assert not any(c['key'] == 'breast_massage' for c in can_train_cmds)
    assert not any(c['key'] == 'finger_insert' for c in can_train_cmds)
    assert not any(c['key'] == 'ass_caress' for c in can_train_cmds)

    # 执行不需要手的指令：亲吻（占用嘴）
    res3 = world.command_manager.do_cmd('kiss', {'continuous': False})
    assert res3 is not None

    # 检查状态下发
    state = world.get_state(z23_nearby.id)
    assert len(state['continuous_commands']) == 2
    assert '正在爱抚' in state['continuous_commands'][0]['text']

    # 解除第一个持续指令
    world.train_manager.cancel_continuous_cmd(cmd.id)
    assert world.player.body_slots['hands'] == 1
    assert len(world.train_manager.train.continuous_commands) == 1

    # 结束调教，所有槽位复原
    world.command_manager.do_cmd('end_train')
    assert world.player.body_slots['hands'] == 2
    assert z23_nearby.body_slots['breasts'] == 2
    assert world.train_manager.train is None


def test_duplicate_continuous_command_is_rejected(world, z23_nearby):
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20

    first = world.command_manager.do_cmd('caress', {'continuous': True})
    second = world.command_manager.do_cmd('caress', {'continuous': True})

    assert first is not None
    assert second == ['该指令已经在持续执行中']
    assert len(world.train_manager.train.continuous_commands) == 1
    assert world.player.body_slots['hands'] == 1


def test_continuous_state_uses_command_specific_text(world, z23_nearby):
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20
    z23_nearby.palam_lv['lubrication_palam'] = 3

    world.command_manager.do_cmd('common_position', {'continuous': True})
    state = world.get_state(z23_nearby.id)

    assert state['continuous_commands'][0]['text'] == '指挥官正在与Z23进行正常位'


def test_continuous_train_state_roundtrips_in_save(world, z23_nearby, tmp_path):
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20

    world.command_manager.do_cmd('caress', {'continuous': True})
    world.save_manager.sav_dir = tmp_path
    world.save_manager.save_game(1)

    from world import World
    restored = World()
    restored.save_manager.sav_dir = tmp_path
    assert restored.save_manager.load_game(1) is None
    assert restored.train_manager.train is not None
    assert len(restored.train_manager.train.continuous_commands) == 1
    assert restored.train_manager.train.continuous_commands[0].command_key == 'caress'
    assert restored.player.body_slots['hands'] == 1


def test_spread_labia_and_ass_slots(world, z23_nearby):
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20  # 保证 able 判定通过

    # 张开阴唇占用 target hands=1, vagina=1
    res = world.command_manager.do_cmd('spread_the_labia', {'continuous': True})
    assert res is not None
    assert z23_nearby.body_slots['hands'] == 1
    assert z23_nearby.body_slots['vagina'] == 0
    assert len(world.train_manager.train.continuous_commands) == 1

    # 再执行张开菊穴占用 target hands=1, ass=1
    res2 = world.command_manager.do_cmd('spread_the_ass', {'continuous': True})
    assert res2 is not None
    assert z23_nearby.body_slots['hands'] == 0
    assert z23_nearby.body_slots['ass'] == 0
    assert len(world.train_manager.train.continuous_commands) == 2

    # 指插入需要 target vagina=1，此时已为0，不能执行
    can_cmds = world.train_manager.get_train_commands()
    assert not any(c['key'] == 'finger_insert' for c in can_cmds)

    # 切换目标/角色侧别时，自动解绑并恢复槽位
    world.train_manager.toggle_target(z23_nearby.id)
    assert len(world.train_manager.train.continuous_commands) == 0
    assert z23_nearby.body_slots['hands'] == 2
    assert z23_nearby.body_slots['vagina'] == 1
    assert z23_nearby.body_slots['ass'] == 1


def test_common_position_slots(world, z23_nearby):
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20  # 保证 able 判定通过
    z23_nearby.palam_lv['lubrication_palam'] = 3

    # 正常位占用 actor penis=1, target vagina=1
    res = world.command_manager.do_cmd('common_position', {'continuous': True})
    assert res is not None
    assert world.player.body_slots['penis'] == 0
    assert z23_nearby.body_slots['vagina'] == 0

    # 此时再次尝试正常位，can判定应失败
    can_cmds = world.train_manager.get_train_commands()
    assert not any(c['key'] == 'common_position' for c in can_cmds)

    # 取消正常位
    cmd_id = world.train_manager.train.continuous_commands[0].id
    world.train_manager.cancel_continuous_cmd(cmd_id)
    assert world.player.body_slots['penis'] == 1
    assert z23_nearby.body_slots['vagina'] == 1


def test_continuous_source_halved_and_consumption(world, z23_nearby):
    """测试持续指令每轮产生的 Source 数值减半、体力气力消耗减半，以及与主指令合并结算"""
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20
    z23_nearby.base['stamina'] = 1000
    z23_nearby.base['energy'] = 1000
    world.player.base['stamina'] = 1000
    world.player.base['energy'] = 1000

    # 1. 开启持续爱抚
    res1 = world.command_manager.do_cmd('caress', {'continuous': True})
    assert len(world.train_manager.train.continuous_commands) == 1

    # 记录执行第二轮前的体力气力与好感
    p_sta_before = world.player.base['stamina']
    p_ene_before = world.player.base['energy']
    z_sta_before = z23_nearby.base['stamina']
    z_ene_before = z23_nearby.base['energy']

    # 2. 执行单次亲吻（同时触发持续爱抚的 50% 消耗与 Source 合并）
    # 单次 kiss 消耗: target energy 50
    # 持续 caress 消耗: actor stamina 10, energy 10; target stamina 5, energy 20
    res2 = world.command_manager.do_cmd('kiss', {'continuous': False})

    # 验证体力气力扣减符合预期
    assert world.player.base['stamina'] == p_sta_before - 10
    assert world.player.base['energy'] == p_ene_before - 10
    assert z23_nearby.base['stamina'] == z_sta_before - 5
    assert z23_nearby.base['energy'] == z_ene_before - (50 + 20)

    # 验证前端返回的结算列表中：
    # 1) Source 汇总摘要只输出一次，且同时包含 kiss (快M) 与 caress (快B/快C)
    source_lines = [line for line in res2 if '快M' in line and '快B' in line]
    assert len(source_lines) == 1

    # 2) Palam 标题在结算区只出现一次
    palam_name_headers = [line for line in res2 if line == z23_nearby.name]
    assert len(palam_name_headers) == 1

    # 3) 信赖/好感结算各至多输出一次
    favor_lines = [line for line in res2 if '好感' in line]
    assert len(favor_lines) <= 1
    trust_lines = [line for line in res2 if '信赖' in line]
    assert len(trust_lines) == 1

    # 4) 主导权结算只输出一次 (指挥官与Z23各一条)
    initiative_lines = [line for line in res2 if '主导权' in line]
    assert len(initiative_lines) == 2  # 指挥官 + Z23 各一条增减记录

    # 5) 体力与气力消耗按角色合并展示，无重复行
    stamina_lines = [line for line in res2 if line.startswith('体力-') or line.startswith('气力-')]
    # 指挥官: 体力-10, 气力-10; Z23: 体力-5, 气力-70
    assert stamina_lines == [
        '体力-10 (指挥官)',
        '气力-10 (指挥官)',
        '体力-5 (Z23)',
        '气力-70 (Z23)'
    ]


def test_multiple_continuous_merged_exp(world, z23_nearby):
    """测试多重持续状态下，重复获得的经验类型（如手淫经验）自动合并+N"""
    world.train_manager.new_train([PLAYER_ID, z23_nearby.id], {PLAYER_ID: 100, z23_nearby.id: 50})
    world.train_manager.train.actors = [PLAYER_ID]
    world.train_manager.train.targets = [z23_nearby.id]
    z23_nearby.abl['desire_abl'] = 20

    # 开启持续爱抚 (caress: 给指挥官 finger_exp + 1, 给Z23 caress_exp + 1)
    world.command_manager.do_cmd('caress', {'continuous': True})
    
    # 模拟直接在 Context 中写入多条同类经验并验证合并
    from game_engine.commands._context import CommandContext
    ctx = CommandContext(world)
    ctx.say_exp(
        '口淫经验+1 (指挥官)',
        'B经验+1 (标枪)',
        '手淫经验+1 (指挥官)',
        '手淫经验+1 (指挥官)',
    )
    assert ctx.blocks['exp'] == [
        '口淫经验+1 (指挥官)',
        'B经验+1 (标枪)',
        '手淫经验+2 (指挥官)',
    ]





import json
from pathlib import Path

import pytest


def test_runtime_state_roundtrips_when_save_is_loaded(world, tmp_path):
    # Given: mutable state that save v2 did not include.
    z23 = world.npc_manager.get_npc_by_id('Z23')
    z23.talk_fatigue = 143
    z23.is_talk_fatigue = True
    world.player.cflag['runtime_marker'] = True
    world.train_manager.new_train(
        ['player', 'Z23', 'laffey'],
        {'player': 70, 'Z23': 20, 'laffey': 10},
        leader='Z23',
    )
    train = world.train_manager.train
    assert train is not None
    train.location = {'region': 'office', 'node': 'desk'}
    train.actors = ['Z23']
    train.targets = ['player', 'laffey']
    world.save_manager.sav_dir = tmp_path
    world.save_manager.save_game(1)

    # When: a fresh world loads the slot.
    from world import World

    restored = World()
    restored.save_manager.sav_dir = tmp_path
    error = restored.save_manager.load_game(1)

    # Then: every mutable field and the active training session are restored.
    assert error is None
    restored_z23 = restored.npc_manager.get_npc_by_id('Z23')
    assert restored_z23.talk_fatigue == 143
    assert restored_z23.is_talk_fatigue is True
    assert restored.player.cflag['runtime_marker'] is True
    assert restored.train_mode is True
    restored_train = restored.train_manager.train
    assert restored_train is not None
    assert restored_train.location == {'region': 'office', 'node': 'desk'}
    assert restored_train.participants == ['player', 'Z23', 'laffey']
    assert restored_train.actors == ['Z23']
    assert restored_train.targets == ['player', 'laffey']
    assert restored_train.initiative == {'player': 70, 'Z23': 20, 'laffey': 10}
    assert restored_train.leader == 'Z23'


def test_skin_defaults_survive_when_v1_save_is_loaded(world, tmp_path):
    # Given: a v1 save made before skin and item fields existed.
    payload = world.save_manager.serialize_world()
    payload['version'] = 1
    del payload['data']['skins']
    del payload['data']['items']
    slot_path = tmp_path / 'slot_1.json'
    slot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

    from world import World

    restored = World()
    expected_unlocked = restored.skin_manager.unlocked_skins.copy()
    expected_locked = restored.skin_manager.locked_skins.copy()
    expected_wearing = restored.skin_manager.ships_wear_skin.copy()
    restored.save_manager.sav_dir = tmp_path

    # When: the legacy slot is loaded.
    error = restored.save_manager.load_game(1)

    # Then: new-system defaults remain available instead of becoming empty.
    assert error is None
    assert restored.skin_manager.unlocked_skins == expected_unlocked
    assert restored.skin_manager.locked_skins == expected_locked
    assert restored.skin_manager.ships_wear_skin == expected_wearing


def test_existing_slot_survives_when_atomic_replace_fails(world, tmp_path, monkeypatch):
    # Given: an existing valid slot and a simulated filesystem replacement failure.
    world.save_manager.sav_dir = tmp_path
    world.player.money = 100
    world.save_manager.save_game(1)
    slot_path = tmp_path / 'slot_1.json'
    original = slot_path.read_bytes()
    world.player.money = 999

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError('simulated replace failure')

    monkeypatch.setattr(Path, 'replace', fail_replace)

    # When: saving the updated state cannot atomically replace the slot.
    with pytest.raises(OSError, match='simulated replace failure'):
        world.save_manager.save_game(1)

    # Then: the previous slot is untouched and the temporary file is cleaned up.
    assert slot_path.read_bytes() == original
    assert not (tmp_path / 'slot_1.tmp').exists()


def test_ten_save_slots_and_saved_at_timestamp(world, tmp_path):
    world.save_manager.sav_dir = tmp_path
    save_list = world.save_manager.get_save_list()
    assert len(save_list) == 10
    assert all(s['has_save'] is False for s in save_list)

    # 存档到槽位 10
    meta = world.save_manager.save_game(10)
    assert 'saved_at' in meta
    assert meta['saved_at'] != ''

    # 检查 save_list 状态
    updated_list = world.save_manager.get_save_list()
    assert len(updated_list) == 10
    slot10 = next(s for s in updated_list if s['slot'] == 10)
    assert slot10['has_save'] is True
    assert slot10['saved_at'] == meta['saved_at']

    # 检查 CommandManager 的选项文本格式
    opts = world.command_manager.get_cmd_options('save')
    assert len(opts) == 10
    opt10 = next(o for o in opts if o['key'] == '10')
    assert f"[{meta['saved_at']}]" in opt10['name']
    opt1 = next(o for o in opts if o['key'] == '1')
    assert '空' in opt1['name']

    # 读档槽位 10
    from world import World
    restored = World()
    restored.save_manager.sav_dir = tmp_path
    err = restored.save_manager.load_game(10)
    assert err is None
    assert restored.time_manager.day == world.time_manager.day


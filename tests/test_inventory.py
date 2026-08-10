# -*- coding: utf-8 -*-
"""道具背包：use_items 校验 + items 指令注册 + 系统指令 frontend 透传"""
import pytest
from world import World
from game_engine.commands._commands import REGISTER_CMD, REGISTER_CAT, REGISTER_FRONTEND
from game_engine.managers.ItemManager import ItemManager


@pytest.fixture
def world():
    return World()


def _give(world, item_id, num=1):
    world.item_manager.gain_items(item_id, num)


class TestUseItems:
    def test_use_consumable_item_removes_one(self, world):
        """消耗品使用后数量-1"""
        _give(world, 'oath_ring', 2)
        info = world.item_manager.items_db['oath_ring']
        info['is_usable'] = True   # oath_ring 默认不可用，先放开
        ok, msg = world.item_manager.use_items('oath_ring', 1)
        assert ok is True
        assert world.item_manager.items['oath_ring'] == 1

    def test_use_non_consumable_keeps_count(self, world):
        """非消耗品使用后数量不变"""
        _give(world, 'oath_ring', 1)
        info = world.item_manager.items_db['oath_ring']
        # 手动改 is_consumable=False 模拟非消耗品
        info['is_consumable'] = False
        info['is_usable'] = True
        ok, _ = world.item_manager.use_items('oath_ring', 1)
        assert ok is True
        assert world.item_manager.items['oath_ring'] == 1

    def test_use_not_usable_item_rejected(self, world):
        """is_usable=False 的道具不可使用"""
        _give(world, 'oath_ring', 1)
        # oath_ring 默认 is_usable=False
        ok, msg = world.item_manager.use_items('oath_ring', 1)
        assert ok is False
        assert '无法使用' in msg
        assert world.item_manager.items['oath_ring'] == 1

    def test_use_missing_item_rejected(self, world):
        """没有该道具时拒绝"""
        ok, msg = world.item_manager.use_items('oath_ring', 1)
        assert ok is False

    def test_use_unknown_item_rejected(self, world):
        """未知道具 id 拒绝"""
        ok, msg = world.item_manager.use_items('no_such_item', 1)
        assert ok is False

    def test_use_consumes_all_remaining(self, world):
        """持有 1 个消耗品使用 1 次后归零（items 键仍存在）"""
        _give(world, 'oath_ring', 1)
        info = world.item_manager.items_db['oath_ring']
        info['is_consumable'] = True
        info['is_usable'] = True
        ok, _ = world.item_manager.use_items('oath_ring', 1)
        assert ok is True
        assert world.item_manager.items['oath_ring'] == 0


class TestItemsCommand:
    def test_items_registered_as_system_frontend(self):
        """items 指令：系统分类、不需要目标、frontend=True"""
        assert 'items' in REGISTER_CMD
        assert REGISTER_CAT['items'] == '系统'
        assert REGISTER_FRONTEND.get('items') is True

    def test_system_commands_include_frontend_field(self, world):
        """_get_system_commands 透传 frontend 字段（前端需要）"""
        sys_com = world.command_manager._get_system_commands()
        items_cmd = [c for c in sys_com if c['key'] == 'items']
        assert len(items_cmd) == 1
        assert items_cmd[0]['frontend'] is True

    def test_other_system_commands_frontend_false(self, world):
        """save/load 等系统指令 frontend 为 False"""
        sys_com = world.command_manager._get_system_commands()
        for c in sys_com:
            if c['key'] in ('save', 'load', 'move', 'leave'):
                assert c['frontend'] is False

    def test_items_do_cmd_returns_empty(self, world):
        """items 纯前端占位：do_cmd 返回空（前端不展示）"""
        result = world.command_manager.do_cmd('items')
        assert result == []

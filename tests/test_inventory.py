# -*- coding: utf-8 -*-
"""道具背包：use_items 校验 + items 指令注册 + 系统指令 frontend 透传"""
import pytest

from game_engine.commands._commands import REGISTER_CMD, REGISTER_CAT, REGISTER_FRONTEND
from world import World


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

    def test_use_not_usable_item_consumes_anyway(self, world):
        """is_usable=False 的道具也能被 use_items 消耗（后端不校验 is_usable）

        设计决策（用户）：前端已通过按钮 disabled 约束，后端不重复校验。
        oath.py 等后端指令调用 use_items 时不受 is_usable 限制。
        """
        _give(world, 'oath_ring', 1)
        # oath_ring 默认 is_usable=False，但仍可被后端消耗
        ok, msg = world.item_manager.use_items('oath_ring', 1)
        assert ok is True
        assert world.item_manager.items['oath_ring'] == 0

    def test_use_missing_item_returns_true(self, world):
        """没有持有该道具时也返回成功（不校验持有量，数量不足由前端隐藏）

        注意：这是宽松语义——后端不检查 items 中是否持有，直接消耗（可能变负）。
        设计决策（用户）：前端背包只显示持有道具，后端信任调用方。
        """
        _give(world, 'oath_ring', 1)
        ok, msg = world.item_manager.use_items('oath_ring', 1)
        assert ok is True

    def test_use_unknown_item_raises_keyerror(self, world):
        """未知道具 id 直接崩溃（KeyError）

        设计决策（用户）：故意崩溃反而能更快查出误写 id 的调用方，
        比静默报错更容易发现 bug。
        """
        with pytest.raises(KeyError):
            world.item_manager.use_items('no_such_item', 1)

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

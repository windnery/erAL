# -*- coding: utf-8 -*-
"""pytest 共享 fixture：每个测试使用全新的 World 实例"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import game_engine.commands


@pytest.fixture
def world():
    """全新世界实例（加载全部 JSON + 4 舰娘，约 10ms）"""
    from world import World
    return World()


@pytest.fixture
def player(world):
    """玩家对象"""
    return world.player


@pytest.fixture
def npcs(world):
    """全部舰娘 dict {id: ShipGirl}"""
    return world.npc_manager.shipgirls


@pytest.fixture
def z23(world):
    """Z23 舰娘"""
    return world.npc_manager.shipgirls['Z23']


def place_next_to_player(world, sg):
    """把舰娘放到玩家所在位置（同区域同节点）"""
    world.npc_manager.set_loc(sg.id, world.player.location['region'], world.player.location['node'])
    return sg


@pytest.fixture
def z23_nearby(world):
    """Z23 已放到玩家身边"""
    return place_next_to_player(world, world.npc_manager.shipgirls['Z23'])


@pytest.fixture
def source_dict():
    """构造一个全 0 的 source 字典"""
    from config.source_config import ALL_SOURCE_KEYS
    return {k: 0 for k in ALL_SOURCE_KEYS}

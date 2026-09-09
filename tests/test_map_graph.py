"""地图图模型测试：links 邻接完整性、Dijkstra 寻路、字符画地图视图"""
import json
from pathlib import Path

import pytest

from data.data_loader import load_maps
from game_engine.managers.MapManager import MapManager, _INF

MAPS_DIR = Path(__file__).parent.parent / 'data' / 'maps'


def test_all_nodes_have_valid_links():
    """所有区域节点都声明 links，且边指向同区域的真实节点"""
    maps = load_maps()
    for region, nodes in maps.items():
        for node_id, node in nodes.items():
            assert 'links' in node, f'{region}/{node_id} 缺少 links'
            for to, cost in node['links'].items():
                assert to in nodes, f'{region}/{node_id} -> {to} 不是本区域节点'
                assert isinstance(cost, int) and cost > 0, \
                    f'{region}/{node_id} -> {to} 通行时间非法'


def test_links_are_bidirectional():
    """无向连通图：每条边都有反向边"""
    maps = load_maps()
    for region, nodes in maps.items():
        for node_id, node in nodes.items():
            for to in node['links']:
                assert node_id in nodes[to]['links'], \
                    f'{region}: {to} -> {node_id} 缺少反向边'


def test_regions_are_connected():
    """每个区域的图从任意节点出发可达全部节点"""
    maps = load_maps()
    for region, nodes in maps.items():
        start = next(iter(nodes))
        visited = {start}
        queue = [start]
        while queue:
            cur = queue.pop()
            for to in nodes[cur]['links']:
                if to not in visited:
                    visited.add(to)
                    queue.append(to)
        assert visited == set(nodes), f'{region} 存在不可达节点: {set(nodes) - visited}'


def test_find_path_same_region():
    """同区域寻路：home 客厅到厨房直连 1 分钟"""
    mm = MapManager()
    steps = mm.find_path('home', 'living_room', 'home', 'kitchen')
    assert len(steps) == 1
    assert steps[0] == {"region": "home", "node": "kitchen", "time": 1}
    assert sum(s['time'] for s in steps) == 1


def test_find_path_same_region_through_intermediate():
    """同区域寻路可途经中间节点：白鹰宿舍 laffey_room 到 oklahoma_room 经走廊"""
    mm = MapManager()
    steps = mm.find_path('eagle_union_dorm', 'laffey_room', 'eagle_union_dorm', 'oklahoma_room')
    assert len(steps) == 2
    assert [s['node'] for s in steps] == ['corridor', 'oklahoma_room']
    assert sum(s['time'] for s in steps) == 2


def test_find_path_cross_region():
    """跨区域寻路：leave_time + 目标区域入口到目标节点"""
    mm = MapManager()
    steps = mm.find_path('home', 'living_room', 'ironblood_dorm', 'z1_room')
    # home -> ironblood_dorm 3 分钟 + corridor -> z1_room 1 分钟
    assert sum(s['time'] for s in steps) == 4
    assert [s['node'] for s in steps] == ['corridor', 'z1_room']


def test_find_path_unknown_node_raises():
    """契约收紧：find_path 不再返回 None，不存在的节点直接 KeyError（fail-fast）。
    图的全连通性由 test_floyd_table_complete_and_symmetric 保证"""
    mm = MapManager()
    with pytest.raises(KeyError):
        mm.find_path('home', 'living_room', 'home', 'nonexistent')


def test_map_view_with_art():
    """有字符画的区域返回 lines/tokens，记号带节点标签，出口记号标记 exit"""
    mm = MapManager()
    view = mm.get_map_view('home')
    assert view['has_art'] is True
    assert len(view['lines']) > 0
    assert view['tokens']['01'] == {'node': 'living_room', 'label': '客厅'}
    assert view['tokens']['02'] == {'node': 'bedroom', 'label': '卧室'}
    assert view['tokens']['离开'] == {'exit': True, 'label': '离开'}
    assert view['region_name'] == '指挥官的家'


def test_map_view_without_art():
    """无字符画的区域 has_art=False，lines 为空"""
    mm = MapManager()
    view = mm.get_map_view('eagle_union_dorm')
    assert view['has_art'] is False
    assert view['lines'] == []


def test_load_maps_strips_meta_keys():
    """load_maps 剥离 lines/tokens 元数据，节点遍历不会混入伪节点"""
    maps = load_maps()
    for region, nodes in maps.items():
        assert 'lines' not in nodes
        assert 'tokens' not in nodes
        for node_id, node in nodes.items():
            assert 'name' in node, f'{region}/{node_id} 不是有效节点'


def test_art_files_are_consistent():
    """字符画记号（方括号约定 [xxx]）都指向本区域真实节点"""
    maps = load_maps()
    for json_file in MAPS_DIR.glob('*.json'):
        if json_file.name.startswith('_'):
            continue
        data = json.loads(json_file.read_text('utf-8'))
        tokens = data.get('tokens', {})
        if not tokens:
            continue
        art = ''.join(data.get('lines', []))
        for token, meta in tokens.items():
            assert f'[{token}]' in art, \
                f'{json_file.stem}: 记号 [{token}] 未出现在字符画中'
            if meta.get('node'):
                assert meta['node'] in maps[json_file.stem], \
                    f'{json_file.stem}: 记号 {token} 指向不存在的节点 {meta["node"]}'


# ==================== Floyd 全局最短路表 ====================

def _all_node_pairs(mm: MapManager):
    """产出 (src_reg, src_node, dst_reg, dst_node) 全节点对"""
    pairs = []
    for s_reg, s_nodes in mm.maps.items():
        for s_node in s_nodes:
            for d_reg, d_nodes in mm.maps.items():
                for d_node in d_nodes:
                    pairs.append((s_reg, s_node, d_reg, d_node))
    return pairs


def test_floyd_table_complete_and_symmetric():
    """Floyd 表全连通（任意节点对可达），且时耗对称（无向图）"""
    mm = MapManager()
    for s_reg, s_node, d_reg, d_node in _all_node_pairs(mm):
        u = mm._node_index[(s_reg, s_node)]
        v = mm._node_index[(d_reg, d_node)]
        assert mm._dist[u][v] != _INF, \
            f'不可达: {s_reg}/{s_node} -> {d_reg}/{d_node}'
        # 无向：dist 对称
        assert mm._dist[u][v] == mm._dist[v][u], \
            f'不对称: {s_reg}/{s_node} <-> {d_reg}/{d_node}'


def test_floyd_path_reconstruction_matches_dist():
    """由 nxt 重建的路径总耗时 == dist[u][v]，且路径片段都为真实节点"""
    mm = MapManager()
    for s_reg, s_node, d_reg, d_node in _all_node_pairs(mm):
        u = mm._node_index[(s_reg, s_node)]
        v = mm._node_index[(d_reg, d_node)]
        expected = mm._dist[u][v]
        steps = mm.find_path(s_reg, s_node, d_reg, d_node)
        assert sum(s['time'] for s in steps) == expected
        if (s_reg, s_node) != (d_reg, d_node):
            assert len(steps) > 0
            assert steps[-1]['node'] == d_node, '路径终点应为目标节点'
            assert steps[-1]['region'] == d_reg, '路径终点区域应为目标区域'
        else:
            assert len(steps) == 0


def test_find_path_cross_region_includes_entry():
    """跨区寻路（查表）时耗正确，路径含目标区入口节点跳点"""
    mm = MapManager()
    # home/living_room -> ironblood_dorm/z1_room：home 内 0 + leave 3 + corridor->z1 1 = 4
    steps = mm.find_path('home', 'living_room', 'ironblood_dorm', 'z1_room')
    assert sum(s['time'] for s in steps) == 4
    # 目标区入口 corridor（ironblood_dorm）应在路径中
    assert steps[0]['node'] == 'corridor'
    assert steps[-1]['node'] == 'z1_room'


def test_find_path_cross_region_accounts_for_src_walk():
    """跨区时源区域内部走到入口节点的耗时计入总耗时"""
    mm = MapManager()
    # home/bedroom -> bedroom->living(1) + leave home->ironblood(3) + corridor->z1(1) = 5
    steps = mm.find_path('home', 'bedroom', 'ironblood_dorm', 'z1_room')
    assert sum(s['time'] for s in steps) == 5
    assert [s['node'] for s in steps] == ['living_room', 'corridor', 'z1_room']


def test_floyd_build_time_reasonable():
    """建表耗时应在合理范围（规模 129 节点，亚秒级）"""
    import time
    start = time.perf_counter()
    MapManager()
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f'Floyd 建表耗时异常: {elapsed:.3f}s'

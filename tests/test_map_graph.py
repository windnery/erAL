"""地图图模型测试：links 邻接完整性、Dijkstra 寻路、字符画地图视图"""
import json
from pathlib import Path

from data.data_loader import load_maps
from game_engine.managers.MapManager import MapManager

MAPS_DIR = Path(__file__).parent.parent / 'data' / 'maps'


def test_all_nodes_have_valid_links():
    """所有区域节点都声明 links，且边指向同区域的真实节点"""
    maps = load_maps()
    for region, nodes in maps.items():
        for node_id, node in nodes.items():
            assert 'links' in node, f'{region}/{node_id} 缺少 links'
            for link in node['links']:
                assert link['to'] in nodes, f'{region}/{node_id} -> {link["to"]} 不是本区域节点'
                assert isinstance(link['time'], int) and link['time'] > 0, \
                    f'{region}/{node_id} -> {link["to"]} 通行时间非法'


def test_links_are_bidirectional():
    """无向连通图：每条边都有反向边"""
    maps = load_maps()
    for region, nodes in maps.items():
        for node_id, node in nodes.items():
            for link in node['links']:
                back_targets = [l['to'] for l in nodes[link['to']]['links']]
                assert node_id in back_targets, \
                    f'{region}: {link["to"]} -> {node_id} 缺少反向边'


def test_regions_are_connected():
    """每个区域的图从任意节点出发可达全部节点"""
    maps = load_maps()
    for region, nodes in maps.items():
        start = next(iter(nodes))
        visited = {start}
        queue = [start]
        while queue:
            cur = queue.pop()
            for link in nodes[cur]['links']:
                if link['to'] not in visited:
                    visited.add(link['to'])
                    queue.append(link['to'])
        assert visited == set(nodes), f'{region} 存在不可达节点: {set(nodes) - visited}'


def test_find_path_same_region():
    """同区域寻路：home 客厅到厨房直连 1 分钟"""
    mm = MapManager()
    result = mm.find_path('home', 'living_room', 'home', 'kitchen')
    assert result is not None
    assert result['total_time'] == 1
    assert result['path'] == ['living_room', 'kitchen']
    assert result['cross_region'] is False


def test_find_path_same_region_through_intermediate():
    """同区域寻路可途经中间节点：白鹰宿舍 laffey_room 到 oklahoma_room 经走廊"""
    mm = MapManager()
    result = mm.find_path('eagle_union_dorm', 'laffey_room', 'eagle_union_dorm', 'oklahoma_room')
    assert result is not None
    assert result['total_time'] == 2
    assert result['path'] == ['laffey_room', 'corridor', 'oklahoma_room']


def test_find_path_cross_region():
    """跨区域寻路：leave_time + 目标区域入口到目标节点"""
    mm = MapManager()
    result = mm.find_path('home', 'living_room', 'ironblood_dorm', 'z1_room')
    assert result is not None
    # home -> ironblood_dorm 3 分钟 + corridor -> z1_room 1 分钟
    assert result['total_time'] == 4
    assert result['cross_region'] is True
    assert result['path'] == ['corridor', 'z1_room']


def test_find_path_unreachable_returns_none():
    """不可达目标返回 None（不存在的节点）"""
    mm = MapManager()
    assert mm.find_path('home', 'living_room', 'home', 'nonexistent') is None


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

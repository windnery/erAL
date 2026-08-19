from typing import Any

from data.data_loader import load_maps, load_regions
from data.time.time_data import leave_time_data, move_time_data


class MapManager:
    """地图管理器"""

    def __init__(self):
        # 地图库
        self.maps: dict[str, dict[str, dict[str, Any]]] = load_maps()

        # 区域地图
        self.regions: dict[str, dict[str, str]] = load_regions()

    def get_current_loc(self, character):
        """获取当前位置信息"""
        region_name = self.regions[character.location['region']]['name']
        node_name = self.maps[character.location['region']][character.location['node']]['name']
        mes = f'{region_name} · {node_name}'

        return mes

    def get_available_nodes(self, region: str, node: str):
        """获取当前区域可前往的节点"""
        nodes: list[dict[str, str]] = []
        for node_id in self.maps[region].keys():
            if node_id != node and node in move_time_data and node_id in move_time_data[node]:  # 仅显示有通行时间的节点
                nodes.append(
                    {'key': node_id, 'name': self.maps[region][node_id]['name'], 'time': move_time_data[node][node_id]})
        nodes.append({'key': 'return', 'name': '返回'})  # 添加返回选项
        return nodes

    def get_available_regions(self, region: str):
        """获取可前往的区域"""
        regions: list[dict[str, str]] = []
        for r_id in self.regions.keys():
            if r_id != region:  # 移除当前区域
                regions.append(
                    {'key': r_id, 'name': self.regions[r_id]['name'], 'time': leave_time_data[region][r_id]})
        regions.append({'key': 'return', 'name': '返回'})  # 添加返回选项
        return regions

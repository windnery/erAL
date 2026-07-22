import json
from typing import Any

from data.data_loader import load_maps
from data.time.time_data import leave_time_data, move_time_data


class MapManager:
    '''地图管理器'''

    def __init__(self):
        self.region: str = 'home'       # 当前区域
        self.node: str = 'living_room'  # 当前节点

        # 地图库
        self.maps: dict[str, dict[str, dict[str, Any]]] = load_maps()

        # 区域地图
        with open('data/maps/_regions.json', 'r', encoding='utf-8') as f:
            self.regions: dict[str, dict[str, str]] = json.load(f)

    def get_current_loc(self):
        '''获取当前位置信息'''
        region = self.regions[self.region]['name']
        node = self.maps[self.region][self.node]['name']
        mes = f'{region}--{node}'

        return mes

    def get_available_nodes(self):
        '''获取当前区域可前往的节点'''
        nodes: list[dict[str, str]] = []
        for node_id in self.maps[self.region].keys():
            if node_id != self.node:  # 移除当前节点
                nodes.append(
                    {'key': node_id, 'name': self.maps[self.region][node_id]['name'], 'time': move_time_data[self.node][node_id]})
        nodes.append({'key': 'return', 'name': '返回'})  # 添加返回选项
        return nodes

    def get_available_regions(self):
        '''获取可前往的区域'''
        regions: list[dict[str, str]] = []
        for r_id in self.regions.keys():
            if r_id != self.region:  # 移除当前区域
                regions.append(
                    {'key': r_id, 'name': self.regions[r_id]['name'], 'time': leave_time_data[self.region][r_id]})
        regions.append({'key': 'return', 'name': '返回'})  # 添加返回选项
        return regions

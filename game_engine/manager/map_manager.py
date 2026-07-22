import json
from typing import Any

from data.data_loader import load_maps


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
        mes = f'当前位置：{region}--{node}'

        return mes
    
    def get_current_loc_cmd(self):
        '''获取当前位置显示的命令'''

        # 通用指令
        cmd = [
            {'key': 'leave', 'name': '离开当前区域'},
            {'key': 'move', 'name': '移动到其他地点'},
            {'key': 'show_chara_info', 'name': '查看角色信息'},
            {'key': 'save', 'name': '存档'},
            {'key': 'load', 'name': '读档'}
        ]

        # TODO: 根据当前区域和节点添加特定指令

        return cmd
    
    def get_available_nodes(self):
        '''获取当前区域可前往的节点'''
        nodes: list[dict[str, str]] = []
        for node_id in self.maps[self.region].keys():
            if node_id != self.node:  # 移除当前节点
                nodes.append({'key': node_id, 'name': self.maps[self.region][node_id]['name']})
        nodes.append({'key': 'return', 'name': '返回'})  # 添加返回选项
        return nodes
    
    def get_available_regions(self):
        '''获取可前往的区域'''
        regions: list[dict[str, str]] = []
        for r_id in self.regions.keys():
            if r_id != self.region:  # 移除当前区域
                regions.append({'key': r_id, 'name': self.regions[r_id]['name']})
        regions.append({'key': 'return', 'name': '返回'})  # 添加返回选项
        return regions
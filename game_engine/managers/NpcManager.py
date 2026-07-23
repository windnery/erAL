from random import randint, choice

from data.data_loader import load_shipgirls
from game_engine.models.shipgirl import ShipGirl

class NpcManager:
    '''NPC管理器类'''
    def __init__(self):
        # 所有舰娘的初始化数据
        self.shipgirls_db = load_shipgirls()
        # 初始化所有舰娘对象
        self.shipgirls = {sg_id: ShipGirl(**sg_data) for sg_id, sg_data in self.shipgirls_db.items()}

    def set_loc(self, shipgirl_id: str, region: str, node: str):
        '''设置舰娘位置'''
        self.shipgirls[shipgirl_id].location = {'region': region, 'node': node}

    def get_npcs_at(self, region: str, node: str):
        '''获取指定位置的NPC列表'''
        return [sg for sg in self.shipgirls.values()
            if sg.location['region'] == region and sg.location['node'] == node]

    def update_positions(self, hour: int, minutes: int, map_manager):
        '''根据当前时间和推进时长更新所有舰娘位置
        hour: 当前小时（用于判断睡觉/工作）
        minutes: 本次推进的分钟数（影响自由行动时的移动概率）
        map_manager: 地图管理器（用于查询可前往的节点/区域）
        '''
        for sg in self.shipgirls.values():
            # 睡觉时间：回家
            if hour >= sg.schedule['sleep'][0] or hour < sg.schedule['sleep'][1]:
                sleep_region = self.shipgirls_db[sg.id]['location']['region']
                sleep_node = self.shipgirls_db[sg.id]['location']['node']
                self.set_loc(sg.id, sleep_region, sleep_node)
                continue

            # 工作时间：去工作地点
            work_time: list[list[int]] = sg.schedule['work']['time']
            is_work = False
            for time_range in work_time:
                if time_range[0] <= hour < time_range[1]:
                    work_region = sg.schedule['work']['location']['region']
                    work_node = sg.schedule['work']['location']['node']
                    self.set_loc(sg.id, work_region, work_node)
                    is_work = True
                    break
            if is_work:
                continue

            # 自由行动：根据推进时长影响移动概率
            # 基础概率：移动节点15%，离开区域5%，留在原地80%
            # 每推进1分钟，移动节点概率+1%（离开区域概率不变）
            move_chance = min(15 + minutes, 95)  # 上限95%，保证离开区域至少有5%空间
            leave_chance = 5
            p = randint(1, 100)
            if p <= move_chance:
                # 去当前区域的其他节点
                nodes = map_manager.get_available_nodes(sg.location['region'], sg.location['node'])
                nodes = nodes[:-1]  # 移除返回选项
                if nodes:
                    target_node = choice(nodes)
                    self.set_loc(sg.id, sg.location['region'], target_node['key'])
            elif p <= move_chance + leave_chance:
                # 去别的区域
                regions = map_manager.get_available_regions(sg.location['region'])
                regions = regions[:-1]  # 移除返回选项
                if regions:
                    target_region = choice(regions)
                    # 直接从目标区域的地图中随机选一个节点（不依赖 move_time_data）
                    target_nodes = list(map_manager.maps[target_region['key']].keys())
                    if target_nodes:
                        target_node = choice(target_nodes)
                        self.set_loc(sg.id, target_region['key'], target_node)

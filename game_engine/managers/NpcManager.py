from random import randint, choice

from config.secretary_ship import SECRETARY_FOLLOWING_END_TIME
from data.data_loader import load_shipgirls
from game_engine.managers import MapManager
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl


class NpcManager:
    """NPC管理器类"""

    def __init__(self):
        # 所有舰娘的初始化数据
        self.shipgirls_db = load_shipgirls()
        # 初始化所有舰娘对象
        self.shipgirls = {sg_id: ShipGirl(**sg_data) for sg_id, sg_data in self.shipgirls_db.items()}
        # 秘书舰
        self.secretary_ship: ShipGirl | None = None

    def set_loc(self, shipgirl_id: str, region: str, node: str):
        """设置舰娘位置"""
        self.shipgirls[shipgirl_id].location = {'region': region, 'node': node}

    def get_npcs_at(self, region: str, node: str):
        """获取指定位置的NPC列表"""
        return [sg for sg in self.shipgirls.values()
                if sg.location['region'] == region and sg.location['node'] == node]

    def get_all_npcs(self):
        """获取所有NPC列表"""
        return list(self.shipgirls.values())

    def set_secretary_ship_proc(self, sg_id: str, player: Player):
        """设置秘书舰处理"""
        if self.secretary_ship:
            """当前有秘书舰的情况"""
            # 移除当前秘书舰
            self.secretary_ship.cflag['following'] = False
            self.secretary_ship.cflag['secretary_ship'] = False

        self.secretary_ship = self.shipgirls[sg_id]
        self.secretary_ship.cflag['following'] = True
        self.secretary_ship.cflag['secretary_ship'] = True

    def update_positions(self, hour: int, minutes: int, map_manager: MapManager, player: Player):
        """根据当前时间和推进时长更新所有舰娘位置
        hour: 当前小时（用于判断睡觉/工作）
        minutes: 本次推进的分钟数（影响自由行动时的移动概率）
        map_manager: 地图管理器（用于查询可前往的节点/区域）
        """
        # 更新秘书舰情况
        if self.secretary_ship:
            self.secretary_ship.cflag['following'] = True
            self.secretary_ship.cflag['secretary_ship'] = True

        for sg in self.shipgirls.values():
            # 睡觉时间：回家
            if ((hour >= sg.schedule['sleep']['hour'] and minutes >= sg.schedule['sleep']['minute']) or
                    (hour < sg.schedule['wake_up']['hour']) or
                    (hour == sg.schedule['sleep']['hour'] and minutes < sg.schedule['sleep']['minute'])
            ):
                sleep_region = self.shipgirls_db[sg.id]['location']['region']
                sleep_node = self.shipgirls_db[sg.id]['location']['node']
                self.set_loc(sg.id, sleep_region, sleep_node)
                sg.cflag['sleeping'] = True
                continue
            else:
                sg.cflag['sleeping'] = False

            # 工作时间：去工作地点
            # TODO: 改成新时间系统
            work = sg.schedule.get('work') or {}
            work_time: list[list[int]] = work.get('time', [])
            for time_range in work_time:
                if time_range[0] <= hour < time_range[1]:
                    work_region = sg.schedule['work']['location']['region']
                    work_node = sg.schedule['work']['location']['node']
                    self.set_loc(sg.id, work_region, work_node)
                    sg.cflag['working'] = True
                    break
                else:
                    sg.cflag['working'] = False

            if sg == self.secretary_ship:
                if hour > SECRETARY_FOLLOWING_END_TIME['hour'] or (
                        hour == SECRETARY_FOLLOWING_END_TIME['hour'] and minutes >= SECRETARY_FOLLOWING_END_TIME[
                    'minute']):
                    # 取消秘书舰同行状态
                    self.secretary_ship.cflag['following'] = False

            if sg.is_working():
                continue

            if sg.is_following():
                # 同行中
                self.set_loc(sg.id, player.location['region'], player.location['node'])
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

    def get_npc_by_id(self, shipgirl_id: str):
        """根据舰娘ID获取舰娘对象
        shipgirl_id: 舰娘ID
        return: ShipGirl对象
        """
        return self.shipgirls[shipgirl_id]

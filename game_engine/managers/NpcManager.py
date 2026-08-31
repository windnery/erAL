from __future__ import annotations

from random import randint, choice
from typing import TYPE_CHECKING, Any

from config.base_config import TALK_FATIGUE_RECOVER_THRESHOLD
from config.cflag_config import EXCEPT_MAPPING, NOT_MAPPING
from config.time_config import SECRETARY_FOLLOWING_END_TIME, DATING_END_TIME
from data.data_loader import load_shipgirls
from game_engine.managers.MapManager import MapManager
from game_engine.models.player import Player
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def time_check(hour: int, minute: int, start: list[int], end: list[int]) -> bool:
    """判断当前时间 (hour, minute) 是否在 [start, end) 时段内
    start/end: [时, 分] 列表，如 [8, 30]
    支持：常规时段（8:30-19:30）、同小时时段（9:00-9:30）、跨天时段（22:00-2:00）
    """
    cur = hour * 60 + minute
    s = start[0] * 60 + start[1]
    e = end[0] * 60 + end[1]
    if s <= e:  # 常规或同小时时段：左闭右开 [s, e)
        return s <= cur < e
    else:  # 跨天时段（如 22:00-2:00）：越过午夜
        return cur >= s or cur < e


class NpcManager:
    """NPC管理器类"""
    # 所有舰娘的初始化数据
    shipgirls_db = load_shipgirls()
    # 初始化所有舰娘对象
    shipgirls = {sg_id: ShipGirl(**sg_data) for sg_id, sg_data in shipgirls_db.items()}

    def __init__(self, world: World):
        # 秘书舰
        self.secretary_ship: ShipGirl | None = None
        self.world = world

    def set_loc(self, shipgirl_id: str, region: str, node: str):
        """设置舰娘位置"""
        self.shipgirls[shipgirl_id].location = {'region': region, 'node': node}

    @staticmethod
    def get_npcs_at(region: str, node: str):
        """获取指定位置的NPC列表"""
        return [sg for sg in NpcManager.shipgirls.values()
                if sg.location['region'] == region and sg.location['node'] == node]

    def get_all_npcs(self):
        """获取所有NPC列表"""
        return list(self.shipgirls.values())

    def set_secretary_ship_proc(self, sg_id: str, player: Player):
        """设置秘书舰处理"""
        if self.secretary_ship:
            """当前有秘书舰的情况"""
            # 移除当前秘书舰
            self.secretary_ship.cflag['secretary_ship'] = False
            self.secretary_ship.cflag['secretary_ship_following'] = False

        self.secretary_ship = self.shipgirls[sg_id]
        self.secretary_ship.cflag['secretary_ship'] = True
        self.secretary_ship.cflag['secretary_ship_following'] = True

    def update_positions(self, elapsed_minutes: int, map_manager: MapManager, player: Player):
        """根据当前时间和推进时长更新所有舰娘位置
        elapsed_minutes: 本次推进的分钟数（仅用于自由行动时的移动概率）
        map_manager: 地图管理器（用于查询可前往的节点/区域）
        player: 玩家对象（秘书舰/约会舰娘跟随需要）

        当前时间（hour/minute）直接读 self.world.time_manager，不靠参数传入
        """
        hour = self.world.time_manager.hour
        minute = self.world.time_manager.minute

        # 更新秘书舰情况
        if self.secretary_ship:
            self.secretary_ship.cflag['secretary_ship_following'] = True
            self.secretary_ship.cflag['secretary_ship'] = True

        for sg in self.shipgirls.values():
            # 情绪&理性&心情自然变化
            sg.emotion_natural_change(elapsed_minutes)
            sg.rationality_natural_change(elapsed_minutes)
            sg.mood_natural_change(elapsed_minutes)

            # 会话疲劳值衰减 1分钟减2点
            sg.talk_fatigue_decay(elapsed_minutes * 2)
            if sg.talk_fatigue < TALK_FATIGUE_RECOVER_THRESHOLD:
                sg.is_talk_fatigue = False

            # 调教状态下忽略所有调度
            if self.world.is_training():
                continue

            # 睡觉时间：回家（睡觉优先级除调教外最高）
            sleep_start_time: list[int] = sg.schedule['sleep']['start']
            sleep_end_time: list[int] = sg.schedule['sleep']['end']
            if time_check(hour, minute, sleep_start_time, sleep_end_time):
                sleep_region = self.shipgirls_db[sg.id]['location']['region']
                sleep_node = self.shipgirls_db[sg.id]['location']['node']
                self.set_loc(sg.id, sleep_region, sleep_node)
                # 清除sleeping覆盖掉的cflag
                sg.cflag_clear_except(EXCEPT_MAPPING['sleeping'])
                sg.cflag['sleeping'] = True
                continue
            else:
                sg.cflag['sleeping'] = False

            # 工作时间：去工作地点
            sg.cflag['working'] = False
            if all(sg.cflag.get(key, False) is False for key in NOT_MAPPING['working']):
                works: list[dict[str, Any]] = sg.schedule.get('works') or []
                for work in works:
                    work_region: str = work['location']['region']
                    work_node: str = work['location']['node']
                    work_start_time: list[int] = work['time']['start']
                    work_end_time: list[int] = work['time']['end']
                    if time_check(hour, minute, work_start_time, work_end_time):
                        # 工作时间
                        self.set_loc(sg.id, work_region, work_node)
                        sg.cflag['working'] = True
                        break

            # 秘书舰
            if sg == self.secretary_ship:
                # 设置秘书舰的附属状态
                sg.cflag_set_attach('secretary_ship')
                current = hour * 60 + minute
                secretary_end_time = SECRETARY_FOLLOWING_END_TIME
                if current >= secretary_end_time:
                    # 取消秘书舰同行状态
                    self.secretary_ship.cflag['secretary_ship_following'] = False

            # 约会中
            if sg.is_dating():
                # 设置约会的附属状态
                sg.cflag_set_attach('dating')
                # 判断约会是否已到期
                current = self.world.time_manager.day * 24 * 60 + hour * 60 + minute
                dating_day = sg.cflag.get('dating_day')
                if dating_day is None:
                    dating_day = self.world.time_manager.day
                end_time = dating_day * 24 * 60 + DATING_END_TIME
                if current >= end_time:
                    # 取消约会状态
                    from game_engine.commands.interact.end_date import end_date
                    end_date(self.world, sg.id, True)

            if sg.is_following():
                # 同行中
                self.set_loc(sg.id, player.location['region'], player.location['node'])

            # 自由行动：根据推进时长影响移动概率
            # 基础概率：移动节点15%，离开区域5%，留在原地80%
            # 每推进1分钟，移动节点概率+1%（离开区域概率不变）
            if all(sg.cflag.get(key, False) is False for key in NOT_MAPPING['free']):
                move_chance = min(15 + elapsed_minutes, 95)  # 上限95%，保证离开区域至少有5%空间
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

    @staticmethod
    def get_npc_by_id(shipgirl_id: str):
        """根据舰娘ID获取舰娘对象
        shipgirl_id: 舰娘ID
        return: ShipGirl对象
        """
        return NpcManager.shipgirls[shipgirl_id]

    @staticmethod
    def with_mob(region: str, node: str) -> bool:
        """判断是否有旁人在场"""
        if len(NpcManager.get_npcs_at(region, node)) > 1:
            return True
        return False

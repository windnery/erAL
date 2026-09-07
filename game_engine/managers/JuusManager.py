from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from world import World


# 阵营映射字典
ALIGNMENT_MAP = {
    "0": "白鹰",
    "1": "重樱",
    "2": "铁血",
    "3": "鸢尾",
    "4": "维希教廷",
    "5": "撒丁帝国",
    "6": "皇家",
    "7": "东煌",
    "8": "北方联合",
    "9": "郁金王国",
    "10": "META",
    "11": "飓风",
}

# 舰种映射字典
SHIP_TYPE_MAP = {
    "0": "驱逐",
    "1": "轻巡",
    "2": "重巡",
    "3": "战列",
    "4": "航母",
    "5": "潜艇",
    "6": "维修",
    "7": "航战",
    "8": "轻航",
    "9": "运输",
    "10": "重炮",
    "11": "战巡",
    "12": "超巡",
}


class JuusManager:
    """港区战术终端（啾信）管理器：负责全港区通讯录与即时状态雷达"""

    def __init__(self, world: World):
        self.world = world

    def get_contacts_list(self) -> list[dict[str, Any]]:
        """获取所有已登记且已相识舰娘的即时状态列表（通讯录）"""
        contacts = []
        for sg in self.world.npc_manager.get_all_npcs():
            # 只有已相识的舰娘才会在通讯录中显示
            if not sg.cflag.get("have_encountered", False):
                continue
            # 实时位置文字解析
            r_key = sg.location.get("region", "")
            n_key = sg.location.get("node", "")
            r_name = self.world.map_manager.regions.get(r_key, {}).get("name", r_key)
            n_name = (
                self.world.map_manager.maps.get(r_key, {})
                .get(n_key, {})
                .get("name", n_key)
            )
            loc_str = f"{r_name} - {n_name}" if r_name and n_name else "未知区域"

            # 纯文字状态标签
            status_tags: list[str] = []
            if sg.is_sleeping():
                status_tags.append("睡眠中")
            elif sg.is_working():
                status_tags.append("工作中")
            elif sg.cflag.get("resting", False):
                status_tags.append("休息中")
            elif sg.cflag.get("dating", False):
                status_tags.append("约会中")
            elif sg.is_following():
                status_tags.append("同行中")
            else:
                status_tags.append("自由行动")

            if sg.cflag.get("secretary_ship", False):
                status_tags.append("秘书舰")
            if sg.cflag.get("tired", False):
                status_tags.append("疲倦")

            # 在线/通讯状态（工作中是忙碌，睡觉时是离线，其余都是在线）
            if sg.is_sleeping():
                chat_status = "🔴离线"
                chat_status_type = "offline"
            elif sg.is_working():
                chat_status = "🟡忙碌"
                chat_status_type = "busy"
            else:
                chat_status = "🟢在线"
                chat_status_type = "online"

            align_val = sg.talent["alignment"]
            type_val = sg.talent["ship_type"]

            # 皮肤与立绘路径
            skin_paths = self.world.skin_manager.get_ship_skin_paths(sg.id)

            rel_label = sg.get_talent_name("relationship")
            is_met = sg.cflag.get("have_encountered", False)

            contacts.append(
                {
                    "id": sg.id,
                    "name": sg.name,
                    "alignment": align_val,
                    "alignment_name": ALIGNMENT_MAP.get(align_val, "其他"),
                    "ship_type": type_val,
                    "ship_type_name": SHIP_TYPE_MAP.get(type_val, "未知"),
                    "avatar": skin_paths["avatar"],
                    "portrait": skin_paths["portrait"],
                    "location_region": r_key,
                    "location_node": n_key,
                    "location_region_name": r_name,
                    "location_node_name": n_name,
                    "location_text": loc_str,
                    "status_tags": status_tags,
                    "mood": sg.get_mood(),
                    "mood_label": sg.get_mood_label(),
                    "mood_color": sg.get_mood_color(),
                    "favor": sg.favor,
                    "trust": sg.trust,
                    "relationship_label": rel_label,
                    "first_met": is_met,
                    "first_met_label": rel_label if is_met else "未相识",
                    "chat_status": chat_status,
                    "chat_status_type": chat_status_type,
                }
            )

        return contacts

    def get_contact_detail(self, shipgirl_id: str) -> dict[str, Any] | None:
        """获取单个舰娘的即时详细档案与排班数据"""
        sg = self.world.npc_manager.get_npc_by_id(shipgirl_id)
        if not sg or not sg.cflag.get("have_encountered", False):
            return None

        # 构造作息概况纯文本
        sleep_start = sg.schedule.get("sleep", {}).get("start", [23, 0])
        sleep_end = sg.schedule.get("sleep", {}).get("end", [7, 0])
        sleep_str = f"{sleep_start[0]:02d}:{sleep_start[1]:02d} ~ {sleep_end[0]:02d}:{sleep_end[1]:02d}"

        works = sg.schedule.get("works") or []
        work_entries = []
        for w in works:
            w_start = w["time"]["start"]
            w_end = w["time"]["end"]
            raw_desc = w.get("desc", "港区日常勤务")
            w_desc = raw_desc.replace("{name}", sg.name)
            w_r = self.world.map_manager.regions.get(w["location"]["region"], {}).get(
                "name", ""
            )
            w_n = (
                self.world.map_manager.maps.get(w["location"]["region"], {})
                .get(w["location"]["node"], {})
                .get("name", "")
            )
            work_entries.append(
                f"{w_start[0]:02d}:{w_start[1]:02d} ~ {w_end[0]:02d}:{w_end[1]:02d} {w_desc}（{w_r}-{w_n}）"
            )

        work_str = "、".join(work_entries) if work_entries else "无"

        schedule_list = [f"睡眠作息：{sleep_str}", f"工作安排：{work_str}"]

        # 查找当前在 contacts 里的即时基础信息
        all_contacts = self.get_contacts_list()
        contact_base = next((c for c in all_contacts if c["id"] == shipgirl_id), None)
        if not contact_base:
            return None

        player = self.world.player
        contact_base["is_current_location"] = player.location.get(
            "region"
        ) == sg.location.get("region") and player.location.get(
            "node"
        ) == sg.location.get("node")
        contact_base["sleep_schedule"] = sleep_str
        contact_base["work_schedule"] = work_str
        contact_base["schedule_list"] = schedule_list
        return contact_base

    def _calc_travel_time(
        self, src_reg: str, src_node: str, dst_reg: str, dst_node: str
    ) -> int:
        """计算玩家从当前地点前往目标地点的通行时间（统一走 MapManager 图寻路）"""
        path = self.world.map_manager.find_path(src_reg, src_node, dst_reg, dst_node)
        if path is None:
            return 3  # 兜底：不可达时按最短跨区域时间估算
        return max(path["total_time"], 1)

    def navigate_to_contact(self, shipgirl_id: str) -> dict[str, Any]:
        """前往指定舰娘所在位置，计算通行时间并推进时间"""
        sg = self.world.npc_manager.get_npc_by_id(shipgirl_id)
        if not sg or not sg.cflag.get("have_encountered", False):
            return {"success": False, "message": "未相识该舰娘或目标不存在"}

        player = self.world.player
        p_reg = player.location["region"]
        p_node = player.location["node"]
        t_reg = sg.location["region"]
        t_node = sg.location["node"]

        map_mgr = self.world.map_manager
        t_reg_name = map_mgr.get_region_name(t_reg)
        t_node_name = map_mgr.get_node_name(t_reg, t_node)
        loc_desc = f"{t_reg_name} - {t_node_name}"

        if p_reg == t_reg and p_node == t_node:
            return {"success": False, "message": f"你已经在此处（{loc_desc}）了"}

        minutes = self._calc_travel_time(p_reg, p_node, t_reg, t_node)

        # 更新玩家位置
        player.location["region"] = t_reg
        player.location["node"] = t_node

        # 推进时间并获取沿途/目的地的 NPC 事件
        npc_events = self.world.advance_time_with_events(minutes)

        messages = [f"花费了 {minutes} 分钟，来到了{loc_desc}。"]
        if npc_events:
            messages.extend(npc_events)

        return {
            "success": True,
            "minutes": minutes,
            "location_text": loc_desc,
            "messages": messages,
        }

    def serialize(self) -> dict[str, Any]:
        """序列化供 SaveManager 保存"""
        return {}

    def deserialize(self, data: dict[str, Any] | None):
        """反序列化读档"""

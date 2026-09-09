from __future__ import annotations
import pytest
from world import World
from data.time.time_data import LEAVE_TIME_DATA


class TestMovementPipeline:
    def test_local_move_direct_neighbor(self, world: World):
        """单区域直接相邻移动（无中继点）：一步到位，不触发中继弹窗"""
        world.player.location = {"region": "home", "node": "living_room"}
        res = world.command_manager.do_cmd("move", "kitchen")
        assert world.player.location["region"] == "home"
        assert world.player.location["node"] == "kitchen"
        assert world.movement_manager.session is None
        assert world.event_manager.pending_choice is None

    def test_local_move_same_location(self, world: World):
        """移动到当前所在节点：提示已经在该地点"""
        world.player.location = {"region": "home", "node": "living_room"}
        res = world.command_manager.do_cmd("move", "living_room")
        assert res == ["已经在该地点"]

    def test_local_move_multi_step_encounter_and_stop(self, world: World):
        """单区域多步移动遇到舰娘拦截并选择停下"""
        # eagle_union_dorm 中 laffey_room -> corridor -> oklahoma_room
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"
        dest_node = "oklahoma_room"

        # 在走廊放置清醒的舰娘
        bogue = world.npc_manager.get_npc_by_id("bogue")
        bogue.location = {"region": "eagle_union_dorm", "node": corridor_node}
        bogue.cflag["sleeping"] = False
        bogue.cflag["following"] = False
        bogue.cflag["unconscious"] = False

        res = world.command_manager.do_cmd("move", dest_node)
        # 应在走廊触发偶遇中断，返回空列表等待弹窗选择
        assert res == []
        assert world.movement_manager.session is not None
        assert world.event_manager.pending_choice is not None
        assert world.event_manager.pending_choice.event_id == "movement_encounter"
        assert corridor_node in world.player.location["node"]

        # 玩家选择【停下】
        choice_res = world.event_manager.choose_option("stop")
        assert world.player.location["node"] == corridor_node
        assert world.movement_manager.session is None
        assert world.event_manager.pending_choice is None

    def test_local_move_multi_step_greet_and_continue(self, world: World):
        """单区域多步移动遇到舰娘打招呼并继续直到目的地"""
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"
        dest_node = "oklahoma_room"

        bogue = world.npc_manager.get_npc_by_id("bogue")
        bogue.location = {"region": "eagle_union_dorm", "node": corridor_node}
        bogue.cflag["sleeping"] = False
        bogue.cflag["following"] = False

        world.command_manager.do_cmd("move", dest_node)
        assert world.event_manager.pending_choice is not None

        # 玩家选择【打个招呼继续】
        choice_res = world.event_manager.choose_option("greet_and_continue")
        assert world.player.location["node"] == dest_node
        assert world.movement_manager.session is None
        assert any("打了声招呼" in msg for msg in choice_res)

    def test_local_move_multi_step_continue_to_end(self, world: World):
        """单区域多步移动选择直达目的地"""
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"
        dest_node = "oklahoma_room"

        bogue = world.npc_manager.get_npc_by_id("bogue")
        bogue.location = {"region": "eagle_union_dorm", "node": corridor_node}
        bogue.cflag["sleeping"] = False
        bogue.cflag["following"] = False

        world.command_manager.do_cmd("move", dest_node)
        assert world.event_manager.pending_choice is not None

        # 玩家选择【继续直到目的地】
        choice_res = world.event_manager.choose_option("continue_to_end")
        assert world.player.location["node"] == dest_node
        assert world.movement_manager.session is None

    def test_leave_from_deep_room_encounter_and_cancel(self, world: World):
        """从深处房间离开途中选择停下，取消本次离开"""
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"

        bogue = world.npc_manager.get_npc_by_id("bogue")
        bogue.location = {"region": "eagle_union_dorm", "node": corridor_node}
        bogue.cflag["sleeping"] = False
        bogue.cflag["following"] = False

        res = world.command_manager.do_cmd("leave", "shop_street")
        assert res == []
        assert world.event_manager.pending_choice is not None

        # 玩家选择【停下】
        choice_res = world.event_manager.choose_option("stop")
        assert world.player.location["region"] == "eagle_union_dorm"
        assert world.player.location["node"] == corridor_node
        assert world.movement_manager.session is None

    def test_leave_from_deep_room_rush_to_end(self, world: World):
        """从深处房间发起离开并顺利完成三阶段流转"""
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"

        # 清空宿舍 NPC 避免走廊偶遇
        for sg in world.npc_manager.get_all_npcs():
            if sg.location["region"] == "eagle_union_dorm":
                sg.location = {"region": "home", "node": "living_room"}

        start_time = world.time_manager.get_total_minutes()
        res = world.command_manager.do_cmd("leave", "shop_street")
        end_time = world.time_manager.get_total_minutes()

        assert world.player.location["region"] == "shop_street"
        shop_entry = world.map_manager.regions["shop_street"]["entry_node"]
        assert world.player.location["node"] == shop_entry
        assert world.movement_manager.session is None

        # 耗时包含出境步数 + 通勤耗时
        commute = LEAVE_TIME_DATA["eagle_union_dorm"]["shop_street"]
        assert end_time - start_time >= commute
        assert any("来到了" in msg for msg in res)

    def test_leave_from_entry_node_direct_commute(self, world: World):
        """直接在出入口发起离开：直接进入通勤与入境阶段"""
        home_entry = world.map_manager.regions["home"]["entry_node"]
        world.player.location = {"region": "home", "node": home_entry}

        commute = LEAVE_TIME_DATA["home"]["shop_street"]
        start_time = world.time_manager.get_total_minutes()
        res = world.command_manager.do_cmd("leave", "shop_street")
        end_time = world.time_manager.get_total_minutes()

        assert world.player.location["region"] == "shop_street"
        assert end_time - start_time == commute
        assert any("来到了" in msg for msg in res)

    def test_sleeping_or_unconscious_npc_does_not_intercept(self, world: World):
        """睡着或失去意识的舰娘不会触发偶遇拦截"""
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"
        dest_node = "oklahoma_room"

        # 单元方法测试验证
        bogue = world.npc_manager.get_npc_by_id("bogue")
        bogue.cflag["sleeping"] = True
        assert world.movement_manager._is_available_for_encounter(bogue) is False
        bogue.cflag["sleeping"] = False
        bogue.cflag["unconscious"] = True
        assert world.movement_manager._is_available_for_encounter(bogue) is False
        bogue.cflag["unconscious"] = False
        bogue.cflag["following"] = True
        assert world.movement_manager._is_available_for_encounter(bogue) is False
        bogue.cflag["following"] = False
        assert world.movement_manager._is_available_for_encounter(bogue) is True

        # 将白鹰宿舍其他未跟随角色暂时移到其他区域，避免随机游走到走廊
        for sg in world.npc_manager.get_all_npcs():
            if sg.location["region"] == "eagle_union_dorm":
                sg.location = {"region": "home", "node": "living_room"}

        # 仅将失去意识的 bogue 置于走廊
        bogue.location = {"region": "eagle_union_dorm", "node": corridor_node}
        bogue.cflag["unconscious"] = True

        world.command_manager.do_cmd("move", dest_node)
        # 不应被走廊失去意识的 bogue 拦截，直达目的地
        assert world.player.location["node"] == dest_node
        assert world.event_manager.pending_choice is None
        assert world.movement_manager.session is None

    def test_movement_save_and_restore(self, world: World, tmp_path):
        """在中途遇到舰娘挂起选择时存档并读档恢复"""
        world.player.location = {"region": "eagle_union_dorm", "node": "laffey_room"}
        corridor_node = "corridor"
        dest_node = "oklahoma_room"

        bogue = world.npc_manager.get_npc_by_id("bogue")
        bogue.location = {"region": "eagle_union_dorm", "node": corridor_node}
        bogue.cflag["sleeping"] = False
        bogue.cflag["following"] = False

        world.command_manager.do_cmd("move", dest_node)
        assert world.event_manager.pending_choice is not None
        assert world.movement_manager.session is not None

        world.save_manager.sav_dir = tmp_path
        world.save_manager.save_game(1)

        # 恢复到新世界
        from world import World as FreshWorld
        restored = FreshWorld()
        restored.save_manager.sav_dir = tmp_path
        err = restored.save_manager.load_game(1)
        assert err is None

        # 检查会话与挂起选择恢复正常
        assert restored.movement_manager.session is not None
        assert restored.event_manager.pending_choice is not None
        assert restored.event_manager.pending_choice.event_id == "movement_encounter"

        # 在恢复的世界中继续完成选择
        res = restored.event_manager.choose_option("greet_and_continue")
        assert restored.player.location["node"] == dest_node
        assert restored.movement_manager.session is None
        assert any("打了声招呼" in msg for msg in res)

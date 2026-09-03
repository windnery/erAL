# -*- coding: utf-8 -*-
"""啾信系统（JuusManager & Terminal）单元与集成测试"""

import pytest
from world import World


class TestJuusManager:
    @pytest.fixture
    def world_instance(self):
        return World()

    def test_juus_command_registered_in_ex_com(self, world_instance):
        """啾信指令已注册且在 Ex_COM 中可见"""
        ex_cmds = world_instance.command_manager.get_ex_com()
        keys = [c['key'] for c in ex_cmds]
        assert 'juus' in keys
        juus_cmd = next(c for c in ex_cmds if c['key'] == 'juus')
        assert juus_cmd['name'] == '☆啾信☆'
        assert juus_cmd['frontend'] is True

    def test_get_contacts_list_only_encountered(self, world_instance):
        """通讯录仅返回已相识（have_encountered=True）的舰娘"""
        # 开局未相识任何舰娘时，通讯录为空
        contacts = world_instance.juus_manager.get_contacts_list()
        assert len(contacts) == 0

        # 相识 Z23 后，通讯录仅有 Z23
        z23 = world_instance.npc_manager.shipgirls['Z23']
        z23.cflag['have_encountered'] = True

        contacts = world_instance.juus_manager.get_contacts_list()
        assert len(contacts) == 1
        assert contacts[0]['id'] == 'Z23'

        # 校验字段完整性
        sample = contacts[0]
        required_keys = [
            'id', 'name', 'alignment', 'alignment_name', 'ship_type', 'ship_type_name',
            'avatar', 'portrait', 'location_region', 'location_node', 'location_text',
            'status_tags', 'mood', 'mood_label', 'mood_color', 'favor', 'trust',
            'relationship_label', 'first_met',
            'first_met_label', 'chat_status', 'chat_status_type'
        ]
        for k in required_keys:
            assert k in sample, f'通讯录数据缺少键: {k}'

    def test_status_tags_and_chat_status_sleeping(self, world_instance):
        """睡觉状态纯文字标签与离线状态判定"""
        z23 = world_instance.npc_manager.shipgirls['Z23']
        z23.cflag['have_encountered'] = True
        z23.cflag['sleeping'] = True
        z23.cflag['working'] = False

        contacts = world_instance.juus_manager.get_contacts_list()
        z23_contact = next(c for c in contacts if c['id'] == 'Z23')

        assert '睡眠中' in z23_contact['status_tags']
        assert z23_contact['chat_status'] == '🔴离线'
        assert z23_contact['chat_status_type'] == 'offline'

    def test_status_tags_and_chat_status_working(self, world_instance):
        """工作状态纯文字标签与忙碌状态判定"""
        z23 = world_instance.npc_manager.shipgirls['Z23']
        z23.cflag['have_encountered'] = True
        z23.cflag['sleeping'] = False
        z23.cflag['working'] = True

        contacts = world_instance.juus_manager.get_contacts_list()
        z23_contact = next(c for c in contacts if c['id'] == 'Z23')

        assert '工作中' in z23_contact['status_tags']
        assert z23_contact['chat_status'] == '🟡忙碌'
        assert z23_contact['chat_status_type'] == 'busy'

    def test_status_tags_secretary_and_tired(self, world_instance):
        """秘书舰与疲倦标签联动"""
        z23 = world_instance.npc_manager.shipgirls['Z23']
        z23.cflag['have_encountered'] = True
        z23.cflag['secretary_ship'] = True
        z23.cflag['tired'] = True

        contacts = world_instance.juus_manager.get_contacts_list()
        z23_contact = next(c for c in contacts if c['id'] == 'Z23')

        assert '秘书舰' in z23_contact['status_tags']
        assert '疲倦' in z23_contact['status_tags']

    def test_encounter_relationship_status_label(self, world_instance):
        """未相识不入通讯录，相识后显示 relationship 阶段标签（如 陌生、友好）"""
        z23 = world_instance.npc_manager.shipgirls['Z23']

        # 1. 未相识：不在通讯录中
        z23.cflag['have_encountered'] = False
        contacts = world_instance.juus_manager.get_contacts_list()
        assert not any(c['id'] == 'Z23' for c in contacts)

        # 2. 已相识（relationship=0）：进入通讯录，显示 陌生
        z23.cflag['have_encountered'] = True
        z23.set_talent('relationship', '0')
        contacts = world_instance.juus_manager.get_contacts_list()
        z23_c = next(c for c in contacts if c['id'] == 'Z23')
        assert z23_c['first_met'] is True
        assert z23_c['first_met_label'] == '陌生'

        # 3. 关系提升为友好（relationship=1）
        z23.set_talent('relationship', '1')
        contacts = world_instance.juus_manager.get_contacts_list()
        z23_c = next(c for c in contacts if c['id'] == 'Z23')
        assert z23_c['first_met_label'] == '友好'

    def test_get_contact_detail_schedule(self, world_instance):
        """获取已相识即时档案包含作息概况列表，未相识返回 None"""
        # 未相识时返回 None
        shiranui = world_instance.npc_manager.shipgirls['shiranui']
        shiranui.cflag['have_encountered'] = False
        assert world_instance.juus_manager.get_contact_detail('shiranui') is None

        # 相识后正常获取
        shiranui.cflag['have_encountered'] = True
        detail = world_instance.juus_manager.get_contact_detail('shiranui')
        assert detail is not None
        assert 'sleep_schedule' in detail
        assert 'work_schedule' in detail
        assert 'schedule_list' in detail
        assert '23:00' in detail['sleep_schedule']
        # 确保不知火的工作描述中没有未被替换的 {name}
        assert '{name}' not in detail['work_schedule']
        assert '不知火' in detail['work_schedule']

    def test_navigate_to_contact_success(self, world_instance):
        """点击前往已相识舰娘，成功移动并推进时间"""
        world_instance.player.location = {'region': 'home', 'node': 'living_room'}
        initial_min = world_instance.time_manager.minute

        z23 = world_instance.npc_manager.shipgirls['Z23']
        z23.cflag['have_encountered'] = True
        z23.location = {'region': 'ironblood_dorm', 'node': 'z1_room'}

        res = world_instance.juus_manager.navigate_to_contact('Z23')
        assert res['success'] is True
        assert res['minutes'] >= 1
        assert world_instance.player.location == {'region': 'ironblood_dorm', 'node': 'z1_room'}
        assert world_instance.time_manager.minute == (initial_min + res['minutes']) % 60
        assert any('来到了' in m for m in res['messages'])

    def test_navigate_to_contact_already_there(self, world_instance):
        """已在当前地点时不可重复前往"""
        world_instance.player.location = {'region': 'ironblood_dorm', 'node': 'z1_room'}
        z23 = world_instance.npc_manager.shipgirls['Z23']
        z23.cflag['have_encountered'] = True
        z23.location = {'region': 'ironblood_dorm', 'node': 'z1_room'}

        detail = world_instance.juus_manager.get_contact_detail('Z23')
        assert detail['is_current_location'] is True

        res = world_instance.juus_manager.navigate_to_contact('Z23')
        assert res['success'] is False
        assert '已经在此处' in res['message']

    def test_navigate_to_unencountered_contact(self, world_instance):
        """未相识舰娘无法前往"""
        laffey = world_instance.npc_manager.shipgirls['laffey']
        laffey.cflag['have_encountered'] = False

        res = world_instance.juus_manager.navigate_to_contact('laffey')
        assert res['success'] is False

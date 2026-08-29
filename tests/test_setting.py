import pytest
from api import Api
from game_engine.models.player import Player
from game_engine.setting import (
    DEFAULT_ENERGY,
    DEFAULT_PLAYER_NAME,
    DEFAULT_STAMINA,
    ENERGY_MAX,
    ENERGY_MIN,
    STAMINA_MAX,
    STAMINA_MIN,
    SettingManager,
)
from world import World


class TestSettingManager:
    def test_setting_defs(self):
        """测试获取开局配置默认值与上下限区间"""
        sm = SettingManager()
        defs = sm.get_initial_setting_defs()
        assert defs['default_name'] == '指挥官'
        assert defs['stamina_min'] == 1800
        assert defs['stamina_max'] == 2500
        assert defs['default_stamina'] == 2000
        assert defs['energy_min'] == 1800
        assert defs['energy_max'] == 2500
        assert defs['default_energy'] == 2000

    def test_validate_and_apply_custom_values(self):
        """测试自定义姓名与体力气力数值应用"""
        player = Player()
        sm = SettingManager()
        res = sm.validate_and_apply_initial_settings(
            player, name='皇家总督', max_stamina=2200, max_energy=2400
        )
        assert res['success'] is True
        assert res['name'] == '皇家总督'
        assert res['max_stamina'] == 2200
        assert res['max_energy'] == 2400

        assert player.name == '皇家总督'
        assert player.base['max_stamina'] == 2200
        assert player.base['stamina'] == 2200
        assert player.base['max_energy'] == 2400
        assert player.base['energy'] == 2400

    def test_name_strip_and_empty_fallback(self):
        """测试姓名去除前后空格，留空时回退默认名称"""
        player = Player()
        sm = SettingManager()

        # 空字符串 -> 默认指挥官
        res = sm.validate_and_apply_initial_settings(player, name='   ')
        assert res['name'] == DEFAULT_PLAYER_NAME
        assert player.name == DEFAULT_PLAYER_NAME

        # None -> 默认指挥官
        res = sm.validate_and_apply_initial_settings(player, name=None)
        assert res['name'] == DEFAULT_PLAYER_NAME
        assert player.name == DEFAULT_PLAYER_NAME

        # 包含空格的有效名字
        res = sm.validate_and_apply_initial_settings(player, name='  港区长官  ')
        assert res['name'] == '港区长官'
        assert player.name == '港区长官'

    def test_stamina_energy_clamp_limits(self):
        """测试体力与气力越界时自动限制在 1800~2500 范围内"""
        player = Player()
        sm = SettingManager()

        # 低于 1800 -> 限制为 1800
        res = sm.validate_and_apply_initial_settings(
            player, max_stamina=1000, max_energy=500
        )
        assert res['max_stamina'] == STAMINA_MIN
        assert res['max_energy'] == ENERGY_MIN
        assert player.base['max_stamina'] == STAMINA_MIN
        assert player.base['max_energy'] == ENERGY_MIN

        # 高于 2500 -> 限制为 2500
        res = sm.validate_and_apply_initial_settings(
            player, max_stamina=3000, max_energy=9999
        )
        assert res['max_stamina'] == STAMINA_MAX
        assert res['max_energy'] == ENERGY_MAX
        assert player.base['max_stamina'] == STAMINA_MAX
        assert player.base['max_energy'] == ENERGY_MAX

    def test_invalid_types_fallback_to_default(self):
        """测试非法输入类型自动回退为默认数值"""
        player = Player()
        sm = SettingManager()
        res = sm.validate_and_apply_initial_settings(
            player, max_stamina='invalid', max_energy=None
        )
        assert res['max_stamina'] == DEFAULT_STAMINA
        assert res['max_energy'] == DEFAULT_ENERGY
        assert player.base['max_stamina'] == DEFAULT_STAMINA
        assert player.base['max_energy'] == DEFAULT_ENERGY

    def test_api_dispatch_setting_manager(self):
        """测试通过 Api 实例远程调用 setting_manager 流程"""
        api = Api()
        defs = api.call('setting_manager', 'get_initial_setting_defs')
        assert defs['default_name'] == '指挥官'

        apply_res = api.call(
            'setting_manager',
            'apply_initial_settings',
            '新任指挥官',
            2300,
            2100,
        )
        assert apply_res['success'] is True
        assert apply_res['name'] == '新任指挥官'
        assert apply_res['max_stamina'] == 2300
        assert apply_res['max_energy'] == 2100

        # 检查 world.player 状态同步
        st = api.call('world', 'get_state')
        assert st['player']['name'] == '新任指挥官'
        assert st['player']['base']['max_stamina'] == 2300
        assert st['player']['base']['stamina'] == 2300
        assert st['player']['base']['max_energy'] == 2100
        assert st['player']['base']['energy'] == 2100

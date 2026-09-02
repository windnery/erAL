# -*- coding: utf-8 -*-
"""皮肤系统测试：SkinManager 初始化 / 每日商店列表 / 购买流程 / 穿戴与换装"""
import pytest


@pytest.fixture
def skin_manager(world):
    """皮肤管理器"""
    return world.skin_manager


# ---------- 初始化 ----------

class TestSkinManagerInit:
    def test_default_skin_in_unlocked(self, skin_manager):
        """默认皮肤应自动进入已拥有集合"""
        assert 'laffey_default' in skin_manager.unlocked_skins

    def test_sale_skin_in_locked(self, skin_manager):
        """可购买皮肤应自动进入未购买集合"""
        assert 'laffey_lafei_3' in skin_manager.locked_skins

    def test_default_skin_not_in_locked(self, skin_manager):
        """默认皮肤不应出现在未购买集合"""
        assert 'laffey_default' not in skin_manager.locked_skins

    def test_today_shop_skins_count(self, skin_manager):
        """每日初始化的商店在售皮肤数不超过 18 个"""
        assert len(skin_manager.today_shop_skins) <= 18
        assert len(skin_manager.today_shop_skins) > 0


# ---------- 商店列表 ----------

class TestGetShopSkins:
    def test_shop_contains_only_locked(self, skin_manager):
        """商店列表只包含未购买皮肤，且不包含默认/改造/誓约皮肤"""
        shop = skin_manager.get_shop_skins()
        assert len(shop) <= 18
        ids = [s['skin_id'] for s in shop]
        assert 'laffey_default' not in ids
        assert 'laffey_retrofit' not in ids
        assert 'laffey_oath' not in ids

    def test_shop_item_structure(self, skin_manager):
        """商店条目结构：skin_id/chara_name/skin_name/price/avatar/portrait"""
        # 手动将雪兔皮肤加入今日货架进行结构测试
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        shop = skin_manager.get_shop_skins()
        item = next(s for s in shop if s['skin_id'] == 'laffey_lafei_3')
        assert item['chara_name'] == '拉菲'
        assert item['chara_id'] == 'laffey'
        assert item['skin_name'] == '雪兔与苹果糖'
        assert item['price'] == 800
        assert 'avatars' in item['avatar']
        assert 'portraits' in item['portrait']

    def test_shop_empty_after_buy_all(self, skin_manager, player):
        """买光今日货架上的所有在售皮肤后商店为空"""
        player.set_money(999999)
        for skin in list(skin_manager.get_shop_skins()):
            skin_manager.buy_skin(skin['skin_id'])
        assert skin_manager.get_shop_skins() == []

    def test_refresh_daily_shop_filters_unlocked(self, skin_manager):
        """每日刷新时，已拥有的皮肤绝不会被抽选上架"""
        skin_manager.unlocked_skins.add('laffey_lafei_3')
        skin_manager.refresh_daily_shop()
        assert 'laffey_lafei_3' not in skin_manager.today_shop_skins


# ---------- 购买 ----------

class TestBuySkin:
    def test_buy_success_deducts_money(self, skin_manager, player):
        """购买成功：扣钱 + 皮肤进已拥有 + 从今日货架移除"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(2000)
        ok, msg = skin_manager.buy_skin('laffey_lafei_3')
        assert ok is True
        assert player.money == 1200
        assert 'laffey_lafei_3' in skin_manager.unlocked_skins
        assert 'laffey_lafei_3' not in skin_manager.today_shop_skins

    def test_buy_fail_insufficient_money(self, skin_manager, player):
        """资金不足：购买失败、不扣钱、皮肤不变"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(500)
        ok, msg = skin_manager.buy_skin('laffey_lafei_3')
        assert ok is False
        assert '资金不足' in msg
        assert player.money == 500
        assert 'laffey_lafei_3' in skin_manager.today_shop_skins

    def test_buy_fail_already_owned(self, skin_manager, player):
        """重复购买：已拥有则拒绝"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(9999)
        skin_manager.buy_skin('laffey_lafei_3')
        ok, msg = skin_manager.buy_skin('laffey_lafei_3')
        assert ok is False
        assert '不在售或已拥有' in msg

    def test_buy_fail_default_skin(self, skin_manager, player):
        """默认皮肤不可购买（不在商店）"""
        player.set_money(9999)
        ok, msg = skin_manager.buy_skin('laffey_default')
        assert ok is False

    def test_buy_unknown_skin(self, skin_manager, player):
        """未知皮肤 id：拒绝"""
        player.set_money(9999)
        ok, msg = skin_manager.buy_skin('not_exist_skin')
        assert ok is False

    def test_money_never_negative(self, skin_manager, player):
        """set_money 钳制：扣款后不会为负"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(800)
        skin_manager.buy_skin('laffey_lafei_3')
        assert player.money == 0


# ---------- 指令注册 ----------

class TestAkashiShopCommand:
    def test_akashi_shop_registered_frontend(self):
        """明石商店指令已注册且为纯前端指令"""
        from game_engine.commands._commands import REGISTER_CMD, REGISTER_FRONTEND, REGISTER_CAT
        assert 'akashi_shop' in REGISTER_CMD
        assert REGISTER_FRONTEND.get('akashi_shop') is True
        assert REGISTER_CAT.get('akashi_shop') == '日常'

    def test_akashi_shop_can_only_when_working(self, world, npcs):
        """明石商店 can：仅明石工作中可执行"""
        from game_engine.commands.interact.akashi_shop import can
        akashi = npcs['akashi']
        akashi.cflag['working'] = True
        assert can(world, akashi) is True
        akashi.cflag['working'] = False
        assert can(world, akashi) is False

    def test_akashi_shop_other_npc_cannot(self, world, npcs):
        """非明石舰娘不能开商店"""
        from game_engine.commands.interact.akashi_shop import can
        z23 = npcs['Z23']
        z23.cflag['working'] = True
        try:
            assert can(world, z23) is False
        finally:
            z23.cflag['working'] = False


# ---------- 穿戴皮肤路径 ----------

class TestWearSkinPaths:
    def test_default_wear_skin_paths(self, skin_manager):
        """未换装时返回默认皮肤路径（default 皮肤自带真实图片路径）"""
        paths = skin_manager.get_ship_skin_paths('laffey')
        assert 'laffey_default' in paths['avatar']
        assert 'laffey_default' in paths['portrait']

    def test_wear_skin_paths_after_buy_and_wear(self, skin_manager, player):
        """购买并穿戴后，返回该皮肤的真实图片路径"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(9999)
        skin_manager.buy_skin('laffey_lafei_3')
        # 模拟更换皮肤：把 ships_wear_skin 指向新皮肤
        skin_manager.ships_wear_skin['laffey'] = 'laffey_lafei_3'
        paths = skin_manager.get_ship_skin_paths('laffey')
        assert 'laffey_lafei_3' in paths['avatar']
        assert 'laffey_lafei_3' in paths['portrait']

    def test_wear_skin_paths_unknown_ship(self, skin_manager):
        """未知舰娘 id：返回空路径"""
        paths = skin_manager.get_ship_skin_paths('not_exist')
        assert paths == {'avatar': '', 'portrait': ''}

    def test_get_state_injects_avatar_portrait(self, world):
        """get_state 的 nearby_npcs 应下发 avatar/portrait 字段"""
        state = world.get_state()
        assert 'nearby_npcs' in state
        for npc in state['nearby_npcs']:
            assert 'avatar' in npc
            assert 'portrait' in npc
            assert npc['avatar'] != ''
            assert npc['portrait'] != ''

    def test_get_state_reflects_worn_skin(self, world):
        """穿戴皮肤后 get_state 下发新路径（更换皮肤后立即可见）"""
        laffey = world.npc_manager.shipgirls['laffey']
        world.npc_manager.set_loc(laffey.id, world.player.location['region'], world.player.location['node'])
        world.skin_manager.today_shop_skins = ['laffey_lafei_3']
        world.player.set_money(9999)
        world.skin_manager.buy_skin('laffey_lafei_3')
        world.skin_manager.ships_wear_skin['laffey'] = 'laffey_lafei_3'
        state = world.get_state()
        npc = next(s for s in state['nearby_npcs'] if s['id'] == 'laffey')
        assert 'laffey_lafei_3' in npc['avatar']
        assert 'laffey_lafei_3' in npc['portrait']


# ---------- 已拥有皮肤 + 换装 ----------

class TestOwnedSkins:
    def test_owned_skins_contains_default(self, skin_manager):
        """默认皮肤在已拥有列表中，且标记为穿戴中"""
        owned = skin_manager.get_owned_skins('laffey')
        assert len(owned) >= 1
        default = next(s for s in owned if s['skin_id'] == 'laffey_default')
        assert default['is_wearing'] is True
        assert default['chara_name'] == '拉菲'

    def test_owned_skins_after_buy(self, skin_manager, player):
        """购买后皮肤进入已拥有列表，未穿戴"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(9999)
        skin_manager.buy_skin('laffey_lafei_3')
        owned = skin_manager.get_owned_skins('laffey')
        ids = [s['skin_id'] for s in owned]
        assert 'laffey_lafei_3' in ids
        bought = next(s for s in owned if s['skin_id'] == 'laffey_lafei_3')
        assert bought['is_wearing'] is False

    def test_owned_skins_unknown_ship(self, skin_manager):
        """未知舰娘返回空列表"""
        assert skin_manager.get_owned_skins('not_exist') == []

    def test_owned_skins_path_no_prefix(self, skin_manager):
        """返回的图片路径不带 frontend/ 前缀"""
        owned = skin_manager.get_owned_skins('laffey')
        for s in owned:
            assert not s['avatar'].startswith('frontend/')
            assert not s['portrait'].startswith('frontend/')


class TestEquipSkin:
    def test_equip_success(self, skin_manager, player):
        """换装成功：ships_wear_skin 更新 + is_wearing 翻转"""
        skin_manager.today_shop_skins = ['laffey_lafei_3']
        player.set_money(9999)
        skin_manager.buy_skin('laffey_lafei_3')
        ok, msg = skin_manager.equip_skin('laffey', 'laffey_lafei_3')
        assert ok is True
        assert '雪兔' in msg
        assert skin_manager.ships_wear_skin['laffey'] == 'laffey_lafei_3'
        owned = skin_manager.get_owned_skins('laffey')
        assert next(s for s in owned if s['skin_id'] == 'laffey_lafei_3')['is_wearing'] is True
        assert next(s for s in owned if s['skin_id'] == 'laffey_default')['is_wearing'] is False

    def test_equip_not_owned(self, skin_manager):
        """未拥有的皮肤不能换装"""
        ok, msg = skin_manager.equip_skin('laffey', 'laffey_lafei_3')
        assert ok is False
        assert '未拥有' in msg or '尚未拥有' in msg

    def test_equip_unknown_skin(self, skin_manager):
        """该舰娘没有的皮肤 id 不能换装"""
        ok, msg = skin_manager.equip_skin('laffey', 'not_exist_skin')
        assert ok is False

    def test_equip_unknown_ship(self, skin_manager):
        """未知舰娘不能换装"""
        ok, msg = skin_manager.equip_skin('not_exist', 'laffey_default')
        assert ok is False


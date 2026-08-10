from typing import Any

from data.data_loader import load_skins
from game_engine.managers.NpcManager import NpcManager


class SkinManager:
    """皮肤管理器

    skin_db 结构: {角色名(JSON文件名): {skin_id: {default/is_sale/price/name/avatar/portrait}}}
    skin_id 是稳定的英文唯一标识（如 laffey_default / snow_rabbit_and_apple_candy）
    图片路径 avatar/portrait 直接存于皮肤数据中，前端不自行拼接
    """

    def __init__(self, npc_manager: NpcManager):
        self.npc_manager = npc_manager
        # 皮肤数据库：{角色名: {skin_id: {...}}}
        self.skin_db: dict[str, dict[str, dict[str, Any]]] = load_skins()
        # 已有皮肤（默认皮肤/改造/誓约/已购买）
        self.unlocked_skins: set[str] = set()
        # 未购买皮肤（商店在售）
        self.locked_skins: set[str] = set()
        # 角色名 -> 舰娘 id 映射（用于把皮肤挂到舰娘身上）
        self._chara_name_to_id: dict[str, str] = {}
        for sg_id, sg_data in self.npc_manager.shipgirls_db.items():
            self._chara_name_to_id[sg_data.get('name', sg_id)] = sg_id
        # 舰娘穿戴皮肤
        self.ships_wear_skin: dict[str, str] = {}

        # 初始化：默认皮肤 -> 已有；可购买皮肤 -> 未购买
        for skins in self.skin_db.values():
            for skin, info in skins.items():
                if info.get('default', False):
                    self.unlocked_skins.add(skin)
                if info.get('is_sale', False):
                    self.locked_skins.add(skin)

        # 初始化舰娘穿戴皮肤
        for sg_id, sg_data in self.npc_manager.shipgirls_db.items():
            self.ships_wear_skin[sg_id] = f'{sg_id}_default'

    # ---------- 商店接口 ----------

    def get_ship_skin_paths(self, ship_id: str) -> dict[str, str]:
        """返回舰娘当前穿戴皮肤的图片路径 {avatar, portrait}

        从 ships_wear_skin 取当前皮肤 id，到皮肤库查路径。
        查不到时返回空路径（前端会用默认拼法兜底）。
        """
        skin_id = self.ships_wear_skin.get(ship_id, f'{ship_id}_default')
        # 舰娘 id -> 角色名（反向查 _chara_name_to_id）
        chara_name = None
        for name, sid in self._chara_name_to_id.items():
            if sid == ship_id:
                chara_name = name
                break
        if chara_name is None:
            return {'avatar': '', 'portrait': ''}
        info = self.skin_db.get(chara_name, {}).get(skin_id, {})
        raw_avatar = info.get('avatar', '')
        raw_portrait = info.get('portrait', '')
        # 皮肤 JSON 里路径含 'frontend/' 前缀，页面基准已是 frontend/ 目录，返回时去掉
        PREFIX = 'frontend/'
        return {
            'avatar': raw_avatar[len(PREFIX):] if raw_avatar.startswith(PREFIX) else raw_avatar,
            'portrait': raw_portrait[len(PREFIX):] if raw_portrait.startswith(PREFIX) else raw_portrait,
        }

    def get_shop_skins(self) -> list[dict[str, Any]]:
        """返回商店在售皮肤列表（未购买），按角色名+皮肤名组织

        每项: {skin_id, chara_id, chara_name, skin_name, price, avatar, portrait}
        展示名格式: chara_name-skin_name（如 拉菲-雪兔与苹果糖）
        """
        result: list[dict[str, Any]] = []
        for chara_name, skins in self.skin_db.items():
            chara_id = self._chara_name_to_id.get(chara_name, chara_name)
            for skin_id, info in skins.items():
                if skin_id not in self.locked_skins:
                    continue
                result.append({
                    'skin_id': skin_id,
                    'chara_id': chara_id,
                    'chara_name': chara_name,
                    'skin_name': info.get('name', skin_id),
                    'price': info.get('price', 0),
                    'avatar': info.get('avatar', '')[len('frontend/'):] if info.get('avatar', '').startswith('frontend/') else info.get('avatar', ''),
                    'portrait': info.get('portrait', '')[len('frontend/'):] if info.get('portrait', '').startswith('frontend/') else info.get('portrait', ''),
                })
        return result

    def buy_skin(self, skin_id: str, player) -> tuple[bool, str]:
        """购买皮肤。返回 (是否成功, 消息)

        - 皮肤不在 locked_skins -> (False, 消息)
        - 资金不足 -> (False, 消息)
        - 成功：扣钱 + gain_skin -> (True, 消息)
        """
        if skin_id not in self.locked_skins:
            # 找到皮肤名用于报错（找不到就显示 id）
            skin_name = skin_id
            for skins in self.skin_db.values():
                if skin_id in skins:
                    skin_name = skins[skin_id].get('name', skin_id)
                    break
            return False, f'该皮肤不可购买（{skin_name}）'

        price = 0
        for skins in self.skin_db.values():
            if skin_id in skins:
                price = skins[skin_id].get('price', 0)
                break

        money = player.money
        if money < price:
            return False, f'资金不足：需要 {price}，当前 {money}'

        player.set_money(money - price)
        self.gain_skin(skin_id)
        return True, f'购买成功！'

    # ---------- 皮肤获得 ----------

    def gain_skin(self, skin: str):
        if skin in self.locked_skins:
            # 购买获得
            self.locked_skins.remove(skin)
            self.unlocked_skins.add(skin)
        else:
            # 其他途径获得（改造/誓约等）
            self.unlocked_skins.add(skin)

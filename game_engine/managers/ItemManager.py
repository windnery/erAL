from typing import TYPE_CHECKING, Any

from data.data_loader import load_items
from game_engine.items import effect
from game_engine.models.player import Player

if TYPE_CHECKING:
    from game_engine.managers.NpcManager import NpcManager


class ItemManager:
    """道具管理器"""
    def __init__(self, player: Player, npc_manager: 'NpcManager|None'=None):
        # 玩家
        self.player = player
        # 舰娘管理器：按 id 解析「对选中目标使用」的目标
        self.npc_manager = npc_manager
        # 道具数据库
        self.items_db: dict[str, dict[str, Any]] = load_items()
        # 玩家的道具
        self.items: dict[str, int] = {}

    def get_state(self):
        """返回道具管理器状态（仅包含持有数量 > 0 的道具）"""
        return {
            item_id: {
                'name': self.items_db[item_id]['name'],
                'num': count,
                'desc': self.items_db[item_id]['desc'],
                'is_consumable': self.items_db[item_id]['is_consumable'],
                'is_usable': self.items_db[item_id]['is_usable'],
                'price': self.items_db[item_id]['price']
            } for item_id, count in self.items.items() if count > 0
        }

    def gain_items(self, item_id: str, num: int=1):
        """获得道具"""
        self.items[item_id] = self.items.get(item_id, 0) + num

    def use_items(self, item_id: str, num: int=1, target_id: str|None=None):
        """使用道具：返回 (是否成功, 消息列表)
        is_usable 校验由前端按钮 disabled 承担，后端不重复校验；
        is_consumable=True 使用时消耗。
        target_id 为舰娘 id 时对舰娘使用，否则默认对自己（玩家）使用。
        """
        mes_lst: list[str] = []
        info = self.items_db[item_id]
        if info.get('is_consumable', False) and self.items.get(item_id, 0) < num:
            return False, [f'{info["name"]} 数量不足']

        if target_id is not None:
            target = self.npc_manager.shipgirls.get(target_id) if self.npc_manager else None
            if target is None:
                return False, [f'目标不存在（{target_id}）']
        else:
            target = self.player
        if info.get('is_consumable', False):
            self.items[item_id] = self.items.get(item_id, 0) - num
            mes_lst.append(f'使用了 {info["name"]} x{num}')
        # 道具效果
        effect_func = getattr(effect, item_id, None)
        if effect_func:
            mes_lst += effect_func(target)

        return True, mes_lst

    def buy_items(self, item_id: str, num: int=1):
        """购买道具"""
        total_price = self.items_db[item_id]['price'] * num
        if self.player.get_money() >= total_price:
            self.player.set_money(self.player.get_money() - total_price)
            self.gain_items(item_id, num)
            return True, '购买成功！'
        return False, f'资金不足：需要 {total_price}，当前 {self.player.money}'


    def has_item(self, item_id: str):
        """检查是否拥有指定道具"""
        return self.items.get(item_id, 0) > 0

    def get_shop_items(self):
        """返回商店道具"""
        return self.items_db

    def get_item_name_by_id(self, item_id: str):
        """根据道具ID获取道具名称"""
        return self.items_db[item_id]['name']
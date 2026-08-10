from data.data_loader import load_items
from typing import Any

from game_engine.models.player import Player


class ItemManager:
    """道具管理器"""
    def __init__(self, player: Player):
        # 玩家
        self.player = player
        # 道具数据库
        self.items_db: dict[str, dict[str, Any]] = load_items()
        # 玩家的道具
        self.items: dict[str, int] = {}

    def get_state(self):
        """返回道具管理器状态"""
        return {
            item_id: {
                'name': self.items_db[item_id]['name'],
                'num': self.items[item_id],
                'desc': self.items_db[item_id]['desc'],
                'is_consumable': self.items_db[item_id]['is_consumable'],
                'is_usable': self.items_db[item_id]['is_usable'],
                'price': self.items_db[item_id]['price']
            } for item_id in self.items
        }

    def gain_items(self, item_id: str, num: int=1):
        """获得道具"""
        self.items[item_id] = self.items.get(item_id, 0) + num

    def use_items(self, item_id: str, num: int=1):
        """使用道具：返回 (是否成功, 消息)
        is_usable=False 的道具不可使用；is_consumable=True 使用时消耗
        """
        info = self.items_db[item_id]
        if info.get('is_consumable', False):
            self.items[item_id] = self.items.get(item_id, 0) - num
        # TODO: 道具的效果后续补充
        return True, ''

    def buy_items(self, item_id: str, num: int=1):
        """购买道具"""
        total_price = self.items_db[item_id]['price'] * num
        if self.player.money >= total_price:
            self.player.money -= total_price
            self.gain_items(item_id, num)
            return True, f'购买成功！'
        return False, f'资金不足：需要 {total_price}，当前 {self.player.money}'


    def has_item(self, item_id: str):
        """检查是否拥有指定道具"""
        return self.items.get(item_id, 0) > 0

    def get_shop_items(self):
        """返回商店道具"""
        return self.items_db

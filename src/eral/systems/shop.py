"""Shop listing and purchase semantics."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.items import ItemDefinition
from eral.content.shops import ShopfrontDefinition
from eral.domain.world import WorldState


@dataclass(frozen=True, slots=True)
class PurchaseResult:
    """Result of a purchase attempt."""

    success: bool
    item_key: str
    count: int
    total_price: int
    reason: str | None = None


@dataclass(slots=True)
class ShopService:
    """List shop stock and apply purchase semantics."""

    item_definitions: dict[str, ItemDefinition]
    shopfront_definitions: dict[str, ShopfrontDefinition]

    def _item_definition(self, item_key: str) -> ItemDefinition | None:
        return self.item_definitions.get(item_key)

    def _shopfront_definition(self, shopfront_key: str) -> ShopfrontDefinition | None:
        return self.shopfront_definitions.get(shopfront_key)

    def list_items(self, shopfront_key: str) -> tuple[ItemDefinition, ...]:
        """Return the items sold by the given shopfront."""

        shopfront = self._shopfront_definition(shopfront_key)
        if shopfront is None:
            return ()
        return tuple(
            item
            for item in self.item_definitions.values()
            if item.category in shopfront.item_categories
        )

    def purchase(self, world: WorldState, shopfront_key: str, item_key: str, count: int = 1) -> PurchaseResult:
        """Attempt to purchase an item from a shopfront."""

        if count <= 0:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=0, reason="购买数量非法。")

        shopfront = self._shopfront_definition(shopfront_key)
        if shopfront is None:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=0, reason="商店不存在。")

        item = self._item_definition(item_key)
        if item is None:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=0, reason="商品不存在。")

        if item.category not in shopfront.item_categories:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=0, reason="该商店不出售此商品。")

        total_price = item.price * count
        if world.personal_funds < total_price:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=total_price, reason="资金不足。")

        world.personal_funds -= total_price
        world.add_item(item_key, count)
        return PurchaseResult(True, item_key=item_key, count=count, total_price=total_price)

"""Shop listing and purchase semantics."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.items import ItemDefinition
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

    def _item_definition(self, item_key: str) -> ItemDefinition | None:
        return self.item_definitions.get(item_key)

    def list_items(self, shopfront_key: str | None = None) -> tuple[ItemDefinition, ...]:
        """Return all available items.

        ``shopfront_key`` is retained for API compatibility but no longer
        filters the catalog.
        """
        return tuple(self.item_definitions.values())

    def purchase(
        self,
        world: WorldState,
        shopfront_key: str | None,
        item_key: str,
        count: int = 1,
    ) -> PurchaseResult:
        """Attempt to purchase an item."""

        if count <= 0:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=0, reason="购买数量非法。")

        item = self._item_definition(item_key)
        if item is None:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=0, reason="商品不存在。")

        total_price = item.price * count
        if world.personal_funds < total_price:
            return PurchaseResult(False, item_key=item_key, count=count, total_price=total_price, reason="资金不足。")

        world.personal_funds -= total_price
        world.add_item(item_key, count)
        return PurchaseResult(True, item_key=item_key, count=count, total_price=total_price)

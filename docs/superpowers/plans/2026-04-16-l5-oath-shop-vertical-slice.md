# L5 Oath Shop Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal shop loop that sells `pledge_ring`, then connect that purchase to the existing `oath` command so the player can complete a full buy-to-oath gameplay slice.

**Architecture:** Keep shop data and purchase rules independent from any specific UI, location, or NPC. Introduce a small `ShopService` that lists goods by `shopfront_key` and purchases into the existing wallet and inventory systems, then extend the command/event pipeline so `oath` emits success and failure content hooks after resolution.

**Tech Stack:** Python 3.11, dataclasses, TOML loaders, `unittest`

---

### Task 1: Shopfront Content And Loader

**Files:**
- Modify: `data/base/items.toml`
- Create: `data/base/shopfronts.toml`
- Create: `src/eral/content/shops.py`
- Modify: `src/eral/content/__init__.py`
- Test: `tests/test_content_loading.py`

- [ ] **Step 1: Write the failing shop content loading tests**

Add these tests to `tests/test_content_loading.py`:

```python
from pathlib import Path

from eral.content.items import load_item_definitions
from eral.content.shops import load_shopfront_definitions


class ShopContentLoadingTests(unittest.TestCase):
    def test_items_file_exposes_complete_pledge_ring_fields(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        items = {
            item.key: item
            for item in load_item_definitions(repo_root / "data" / "base" / "items.toml")
        }

        ring = items["pledge_ring"]
        self.assertEqual(ring.display_name, "誓约之戒")
        self.assertEqual(ring.category, "general_shop")
        self.assertEqual(ring.price, 1000)
        self.assertIn("誓约", ring.description)

    def test_shopfronts_file_exposes_general_and_skin_shop(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        shopfronts = {
            shop.key: shop
            for shop in load_shopfront_definitions(repo_root / "data" / "base" / "shopfronts.toml")
        }

        self.assertEqual(shopfronts["general_shop"].display_name, "日常用品店")
        self.assertEqual(shopfronts["general_shop"].item_categories, ("general_shop",))
        self.assertEqual(shopfronts["skin_shop"].display_name, "皮肤商店")
        self.assertEqual(shopfronts["skin_shop"].item_categories, ("skin_shop",))
```

- [ ] **Step 2: Run the loading tests and verify they fail**

Run:

```bash
python -m unittest tests.test_content_loading -v
```

Expected: FAIL because `items.toml` is incomplete, `shopfronts.toml` does not exist, and there is no shop content loader.

- [ ] **Step 3: Fill the item data and add shopfront definitions**

Update `data/base/items.toml` to include full fields for the existing ring:

```toml
[[items]]
key = "pledge_ring"
display_name = "誓约之戒"
category = "general_shop"
description = "用于正式誓约的戒指。成功誓约时消耗，失败不会消耗。"
price = 1000
```

Create `data/base/shopfronts.toml`:

```toml
[[shopfronts]]
key = "general_shop"
display_name = "日常用品店"
item_categories = ["general_shop"]

[[shopfronts]]
key = "skin_shop"
display_name = "皮肤商店"
item_categories = ["skin_shop"]
```

- [ ] **Step 4: Add the shopfront loader**

Create `src/eral/content/shops.py`:

```python
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ShopfrontDefinition:
    key: str
    display_name: str
    item_categories: tuple[str, ...]


def load_shopfront_definitions(path: Path) -> tuple[ShopfrontDefinition, ...]:
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        ShopfrontDefinition(
            key=str(entry["key"]),
            display_name=str(entry["display_name"]),
            item_categories=tuple(str(category) for category in entry.get("item_categories", [])),
        )
        for entry in raw_data.get("shopfronts", [])
    )
```

Export it from `src/eral/content/__init__.py`:

```python
from eral.content.shops import ShopfrontDefinition, load_shopfront_definitions
```

- [ ] **Step 5: Run the loading tests and verify they pass**

Run:

```bash
python -m unittest tests.test_content_loading -v
```

Expected: PASS for the new item-field and shopfront loading tests.

- [ ] **Step 6: Commit the content layer**

```bash
git add data/base/items.toml data/base/shopfronts.toml src/eral/content/shops.py src/eral/content/__init__.py tests/test_content_loading.py
git commit -m "feat: add shopfront content definitions"
```

### Task 2: Shop Service And Purchase Semantics

**Files:**
- Create: `src/eral/systems/shop.py`
- Modify: `src/eral/app/bootstrap.py`
- Modify: `src/eral/app/application.py`
- Test: `tests/test_shop_service.py`

- [ ] **Step 1: Write the failing shop service tests**

Create `tests/test_shop_service.py`:

```python
from __future__ import annotations

import unittest

from tests.support.stages import make_app


class ShopServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = make_app()

    def test_general_shop_lists_pledge_ring(self) -> None:
        goods = self.app.shop_service.list_items("general_shop")
        keys = [item.key for item in goods]
        self.assertIn("pledge_ring", keys)

    def test_skin_shop_does_not_list_pledge_ring(self) -> None:
        goods = self.app.shop_service.list_items("skin_shop")
        keys = [item.key for item in goods]
        self.assertNotIn("pledge_ring", keys)

    def test_purchase_requires_enough_personal_funds(self) -> None:
        self.app.world.personal_funds = 0

        result = self.app.shop_service.purchase(
            self.app.world,
            shopfront_key="general_shop",
            item_key="pledge_ring",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.reason, "资金不足。")
        self.assertEqual(self.app.world.item_count("pledge_ring"), 0)

    def test_purchase_adds_item_and_deducts_funds(self) -> None:
        self.app.world.personal_funds = 1200

        result = self.app.shop_service.purchase(
            self.app.world,
            shopfront_key="general_shop",
            item_key="pledge_ring",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.total_price, 1000)
        self.assertEqual(self.app.world.personal_funds, 200)
        self.assertEqual(self.app.world.item_count("pledge_ring"), 1)
```

- [ ] **Step 2: Run the shop service tests and verify they fail**

Run:

```bash
python -m unittest tests.test_shop_service -v
```

Expected: FAIL because there is no `ShopService` on the application and no purchase implementation.

- [ ] **Step 3: Implement the service**

Create `src/eral/systems/shop.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from eral.content.items import ItemDefinition
from eral.content.shops import ShopfrontDefinition
from eral.domain.world import WorldState


@dataclass(frozen=True, slots=True)
class PurchaseResult:
    success: bool
    item_key: str
    count: int
    total_price: int
    reason: str | None = None


@dataclass(slots=True)
class ShopService:
    item_definitions: dict[str, ItemDefinition]
    shopfront_definitions: dict[str, ShopfrontDefinition]

    def list_items(self, shopfront_key: str) -> tuple[ItemDefinition, ...]:
        shopfront = self.shopfront_definitions[shopfront_key]
        return tuple(
            item
            for item in self.item_definitions.values()
            if item.category in shopfront.item_categories
        )

    def purchase(
        self,
        world: WorldState,
        shopfront_key: str,
        item_key: str,
        count: int = 1,
    ) -> PurchaseResult:
        if count <= 0:
            return PurchaseResult(False, item_key, count, 0, "购买数量非法。")
        if shopfront_key not in self.shopfront_definitions:
            return PurchaseResult(False, item_key, count, 0, "商店不存在。")
        if item_key not in self.item_definitions:
            return PurchaseResult(False, item_key, count, 0, "商品不存在。")

        item = self.item_definitions[item_key]
        shopfront = self.shopfront_definitions[shopfront_key]
        if item.category not in shopfront.item_categories:
            return PurchaseResult(False, item_key, count, 0, "该商店不出售此商品。")

        total_price = item.price * count
        if world.personal_funds < total_price:
            return PurchaseResult(False, item_key, count, total_price, "资金不足。")

        world.personal_funds -= total_price
        world.add_item(item_key, count)
        return PurchaseResult(True, item_key, count, total_price)
```

- [ ] **Step 4: Wire the service into bootstrap**

In `src/eral/app/bootstrap.py`, load and register shopfronts:

```python
from eral.content import load_item_definitions, load_shopfront_definitions
from eral.systems.shop import ShopService
```

```python
    shopfronts_path = root_path / "data" / "base" / "shopfronts.toml"
    shopfronts = load_shopfront_definitions(shopfronts_path)
    shopfront_definitions = {shop.key: shop for shop in shopfronts}
```

```python
    shop_service = ShopService(
        item_definitions=item_definitions,
        shopfront_definitions=shopfront_definitions,
    )
```

Add `shop_service` to the `Application` dataclass and return object in `create_application()`.

- [ ] **Step 5: Run the shop service tests and verify they pass**

Run:

```bash
python -m unittest tests.test_shop_service -v
```

Expected: PASS for listing, insufficient funds, and successful purchase.

- [ ] **Step 6: Commit the service layer**

```bash
git add src/eral/systems/shop.py src/eral/app/bootstrap.py src/eral/app/application.py tests/test_shop_service.py
git commit -m "feat: add minimal shop purchase service"
```

### Task 3: Buy To Oath Integration

**Files:**
- Modify: `tests/test_commands.py`
- Modify: `src/eral/systems/commands.py`
- Modify: `src/eral/domain/actions.py`

- [ ] **Step 1: Write the failing buy-to-oath tests**

Add these tests to `tests/test_commands.py`:

```python
    def test_purchased_ring_can_be_used_for_oath_success(self) -> None:
        actor = self._actor()
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.world.personal_funds = 1200
        self.app.shop_service.purchase(
            self.app.world,
            shopfront_key="general_shop",
            item_key="pledge_ring",
        )
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dock")
        actor.location_key = "dock"
        self.app.command_service.resolution_service.roll = lambda: 0.0

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="oath",
        )

        self.assertTrue(result.resolution_success)
        self.assertEqual(self.app.world.item_count("pledge_ring"), 0)
        self.assertEqual(actor.relationship_stage.key, "oath")

    def test_failed_oath_after_purchase_keeps_ring(self) -> None:
        actor = self._actor()
        seed_like(actor)
        self.app.relationship_service.update_actor(actor)
        self.app.world.personal_funds = 1200
        self.app.shop_service.purchase(
            self.app.world,
            shopfront_key="general_shop",
            item_key="pledge_ring",
        )
        self.app.world.current_time_slot = self.app.world.current_time_slot.MORNING
        self.app.navigation_service.move_player(self.app.world, "main_corridor")
        self.app.navigation_service.move_player(self.app.world, "dock")
        actor.location_key = "dock"
        self.app.command_service.resolution_service.roll = lambda: 0.99

        result = self.app.command_service.execute(
            self.app.world,
            actor_key=actor.key,
            command_key="oath",
        )

        self.assertFalse(result.resolution_success)
        self.assertEqual(self.app.world.item_count("pledge_ring"), 1)
        self.assertNotEqual(actor.relationship_stage.key, "oath")
```

- [ ] **Step 2: Run the command tests and verify the integration gap**

Run:

```bash
python -m unittest tests.test_commands -v
```

Expected: FAIL if the application bootstrap does not yet expose `shop_service`, or if `oath` execution cannot be driven from a real purchased item end-to-end.

- [ ] **Step 3: Tighten the action result contract if needed**

If `ActionResult` does not already expose enough information for the full loop, extend `src/eral/domain/actions.py` with purchase-neutral resolution metadata only:

```python
    resolution_success: bool | None = None
    resolution_chance: float | None = None
```

Do not add shop-specific fields to `ActionResult`; purchase behavior belongs in `PurchaseResult`.

- [ ] **Step 4: Ensure command execution remains compatible with real purchased inventory**

Update `src/eral/systems/commands.py` only if the integration test shows an actual gap. The acceptable implementation is:

- `oath` still reads required items from `world.inventory`
- the existing gate continues to reject missing items
- successful execution still consumes the purchased ring
- failed execution still keeps the purchased ring

If no code change is needed after wiring the service in Task 2, leave this file untouched.

- [ ] **Step 5: Re-run the command tests and verify the full slice passes**

Run:

```bash
python -m unittest tests.test_commands -v
python -m unittest tests.test_shop_service tests.test_commands tests.test_save_load -v
```

Expected: PASS for buy-to-oath success and failure while preserving the existing oath semantics.

- [ ] **Step 6: Commit the vertical slice integration**

```bash
git add tests/test_commands.py src/eral/systems/commands.py src/eral/domain/actions.py
git commit -m "feat: connect shop purchases to oath flow"
```

### Task 4: Oath Success And Failure Content Hooks

**Files:**
- Modify: `src/eral/systems/commands.py`
- Modify: content event/dialogue files currently used by oath-capable actors
- Test: `tests/test_dialogue_service.py`
- Test: `tests/test_events.py`

- [ ] **Step 1: Write the failing content hook tests**

Add focused tests to `tests/test_events.py` and `tests/test_dialogue_service.py` that verify:

```python
    def test_oath_success_emits_oath_success_hook(self) -> None:
        ...
        self.assertIn("oath_success", matched_tags)

    def test_oath_failure_emits_oath_failure_hook(self) -> None:
        ...
        self.assertIn("oath_failure", matched_tags)
```

Use the same actor and purchased-ring setup from the command tests so the hook tests exercise the real command path.

- [ ] **Step 2: Run the focused hook tests and verify they fail**

Run:

```bash
python -m unittest tests.test_events tests.test_dialogue_service -v
```

Expected: FAIL because the current command pipeline does not emit dedicated oath result hooks.

- [ ] **Step 3: Emit dedicated result tags from oath execution**

Update `src/eral/systems/commands.py` so the command pipeline emits one explicit content tag after resolution:

- on success: `oath_success`
- on failure: `oath_failure`

Keep the implementation narrow:

- do not add a generic event framework refactor
- do not change non-oath commands
- only surface the extra tags that current event/dialogue matching can already consume

- [ ] **Step 4: Add one actor's success and failure content**

Update the existing event/dialogue content for one formal actor, preferably `enterprise`, with:

- one `oath_success` branch
- one `oath_failure` branch

If the current content system supports fallback tags, add a minimal generic fallback as well.

- [ ] **Step 5: Re-run the hook tests and verify they pass**

Run:

```bash
python -m unittest tests.test_events tests.test_dialogue_service -v
python -m unittest tests.test_shop_service tests.test_commands tests.test_events tests.test_dialogue_service tests.test_save_load -v
```

Expected: PASS for dedicated oath success/failure content plus the end-to-end purchase-to-oath slice.

- [ ] **Step 6: Commit the content hooks**

```bash
git add src/eral/systems/commands.py tests/test_events.py tests/test_dialogue_service.py data
git commit -m "feat: add oath result content hooks"
```

### Task 5: Full Regression And TODO Sync

**Files:**
- Modify: `docs/TODO.md`

- [ ] **Step 1: Update TODO to reflect the completed slice**

After Tasks 1-4 pass, update `docs/TODO.md` so it records:

- L5 item/oath foundation as done
- oath-shop vertical slice as done
- skin shop and NPC shop entry as next

- [ ] **Step 2: Run the regression pack**

Run:

```bash
python -m unittest discover -s tests -t .
```

Expected: PASS with the full suite green.

- [ ] **Step 3: Commit the TODO sync**

```bash
git add docs/TODO.md
git commit -m "docs: update todo for oath shop slice"
```

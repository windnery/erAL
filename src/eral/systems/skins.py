"""Skin and appearance runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.skins import AppearanceDefinition, SkinDefinition
from eral.domain.world import CharacterState, WorldState


@dataclass(slots=True)
class SkinService:
    """Manage skin defaults and appearance lookup."""

    skin_definitions: dict[str, SkinDefinition]
    appearance_definitions: dict[str, AppearanceDefinition]

    @staticmethod
    def default_skin_key_for_actor(actor_key: str) -> str:
        """Return the canonical default skin key for one actor."""

        return f"{actor_key}_default"

    def ensure_default_skin_state(self, actor: CharacterState) -> None:
        """Guarantee that a freshly loaded actor has a default skin equipped."""

        default_skin_key = self.default_skin_key_for_actor(actor.key)
        if default_skin_key in self.skin_definitions:
            actor.unlock_skin(default_skin_key)
            if actor.equipped_skin_key is None:
                actor.equip_skin(default_skin_key)

    def appearance_for_actor(self, actor: CharacterState) -> AppearanceDefinition | None:
        """Resolve the current appearance definition for one actor."""

        skin_key = actor.equipped_skin_key
        if skin_key is None:
            return None
        skin = self.skin_definitions.get(skin_key)
        if skin is None:
            return None
        return self.appearance_definitions.get(skin.appearance_key)

    def visible_shop_skins(self, actor_key: str) -> tuple[SkinDefinition, ...]:
        """Return currently purchasable skins for one actor."""

        return tuple(
            skin
            for skin in self.skin_definitions.values()
            if skin.actor_key == actor_key
            and skin.grant_mode == "shop"
            and skin.shop_visibility == "always"
        )

    def purchase_skin(
        self,
        world: WorldState,
        actor: CharacterState,
        skin_key: str,
    ) -> tuple[bool, str | None]:
        """Attempt to unlock one shop skin for an actor."""

        skin = self.skin_definitions.get(skin_key)
        if skin is None:
            return False, "皮肤不存在。"
        if skin.actor_key != actor.key:
            return False, "该角色无法使用此皮肤。"
        if skin.grant_mode != "shop":
            return False, "该皮肤不能通过商店获得。"
        if skin.shop_visibility != "always":
            return False, "该皮肤当前未上架。"
        if actor.has_skin(skin_key):
            return False, "已拥有该皮肤。"
        if world.personal_funds < skin.price:
            return False, "资金不足。"

        world.personal_funds -= skin.price
        actor.unlock_skin(skin_key)
        return True, None

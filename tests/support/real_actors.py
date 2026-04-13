"""Helpers for tests that should use real characters instead of starter placeholders."""

from __future__ import annotations

from eral.app.bootstrap import Application
from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from eral.domain.world import CharacterState

PRIMARY_REAL_KEY = "enterprise"
SECONDARY_REAL_KEY = "laffey"


def actor_by_key(app: Application, key: str = PRIMARY_REAL_KEY):
    return next(actor for actor in app.world.characters if actor.key == key)


def place_player_with_actor(app: Application, actor) -> None:
    location = app.port_map.location_by_key(actor.location_key)
    app.world.active_location.key = location.key
    app.world.active_location.display_name = location.display_name
    app.companion_service.refresh_world(app.world)
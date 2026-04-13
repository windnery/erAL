"""Helpers for tests that should use real characters instead of starter placeholders."""

from __future__ import annotations

from eral.app.bootstrap import Application
from eral.domain.compat_semantics import CFLAGKey, actor_cflag

PRIMARY_REAL_KEY = "enterprise"
SECONDARY_REAL_KEY = "laffey"


def actor_by_key(app: Application, key: str = PRIMARY_REAL_KEY):
    return next(actor for actor in app.world.characters if actor.key == key)


def place_player_with_actor(app: Application, actor) -> None:
    location = app.port_map.location_by_key(actor.location_key)
    app.world.active_location.key = location.key
    app.world.active_location.display_name = location.display_name
    app.companion_service.refresh_world(app.world)


def reset_progress(actor) -> None:
    actor.stats.base.clear()
    actor.stats.palam.clear()
    actor.stats.source.clear()
    actor.affection = 0
    actor.trust = 0
    actor.obedience = 0
    actor.relationship_stage = None
    actor.is_following = False
    actor.follow_ready = False
    actor.is_same_room = False
    actor.is_on_date = False
    actor.marks.clear()
    actor_cflag.set(actor, CFLAGKey.AFFECTION, 0)
    actor_cflag.set(actor, CFLAGKey.TRUST, 0)
    actor_cflag.set(actor, CFLAGKey.OBEDIENCE, 0)
    actor_cflag.set(actor, CFLAGKey.ON_DATE, 0)
    actor_cflag.set(actor, CFLAGKey.SAME_ROOM, 0)
    actor_cflag.set(actor, CFLAGKey.FOLLOWING, 0)
    actor_cflag.set(actor, CFLAGKey.FOLLOW_READY, 0)
    actor.sync_derived_fields()

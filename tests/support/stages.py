"""Test helpers for seeding relationship stages.

Reads thresholds directly from relationship_stages.toml so tests never
hard-code magic numbers.  Change the TOML and every test adapts automatically.
"""

from __future__ import annotations

from pathlib import Path

from eral.app.bootstrap import create_application
from eral.content.relationships import load_relationship_stages
from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from eral.domain.world import CharacterState

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STAGES = load_relationship_stages(_REPO_ROOT / "data" / "base" / "relationship_stages.toml")

ABL_INTIMACY_INDEX = 12

_STAGE_BY_KEY = {s.key: s for s in _STAGES}


def _stage(key: str):
    return _STAGE_BY_KEY[key]


def seed_stranger(actor: CharacterState) -> None:
    reset_progress(actor)


def seed_friendly(
    actor: CharacterState,
    margin: int = 10,
) -> None:
    s = _stage("friendly")
    actor_cflag.set(actor, CFLAGKey.AFFECTION, s.min_affection + margin)
    actor_cflag.set(actor, CFLAGKey.TRUST, s.min_trust + margin)
    actor.sync_derived_fields()


def seed_like(
    actor: CharacterState,
    margin: int = 20,
    intimacy: int | None = None,
) -> None:
    s = _stage("like")
    actor_cflag.set(actor, CFLAGKey.AFFECTION, s.min_affection + margin)
    actor_cflag.set(actor, CFLAGKey.TRUST, s.min_trust + margin)
    actor.stats.compat.abl.set(ABL_INTIMACY_INDEX, s.min_intimacy if intimacy is None else intimacy)
    actor.sync_derived_fields()


def seed_love(
    actor: CharacterState,
    margin: int = 50,
    intimacy: int | None = None,
) -> None:
    s = _stage("love")
    actor_cflag.set(actor, CFLAGKey.AFFECTION, s.min_affection + margin)
    actor_cflag.set(actor, CFLAGKey.TRUST, s.min_trust + margin)
    actor.stats.compat.abl.set(ABL_INTIMACY_INDEX, s.min_intimacy if intimacy is None else intimacy)
    if "dislike_mark" in actor.marks:
        del actor.marks["dislike_mark"]
    actor.sync_derived_fields()


def seed_oath(
    actor: CharacterState,
    margin: int = 100,
    intimacy: int | None = None,
) -> None:
    s = _stage("oath")
    actor_cflag.set(actor, CFLAGKey.AFFECTION, s.min_affection + margin)
    actor_cflag.set(actor, CFLAGKey.TRUST, s.min_trust + margin)
    actor.stats.compat.abl.set(ABL_INTIMACY_INDEX, s.min_intimacy if intimacy is None else intimacy)
    if "dislike_mark" in actor.marks:
        del actor.marks["dislike_mark"]
    actor.sync_derived_fields()


def reset_progress(actor) -> None:
    actor.stats.base.clear()
    actor.stats.palam.clear()
    actor.stats.source.clear()
    actor.stats.base.set("stamina", 2000)
    actor.stats.base.set("spirit", 1500)
    actor.affection = 0
    actor.trust = 0
    actor.obedience = 0
    actor.relationship_stage = None
    actor.is_following = False
    actor.follow_ready = False
    actor.is_same_room = False
    actor.is_on_date = False
    actor.fatigue = 0
    actor.marks.clear()
    actor.stats.compat.abl.set(ABL_INTIMACY_INDEX, 0)
    actor_cflag.set(actor, CFLAGKey.AFFECTION, 0)
    actor_cflag.set(actor, CFLAGKey.TRUST, 0)
    actor_cflag.set(actor, CFLAGKey.OBEDIENCE, 0)
    actor_cflag.set(actor, CFLAGKey.ON_DATE, 0)
    actor_cflag.set(actor, CFLAGKey.SAME_ROOM, 0)
    actor_cflag.set(actor, CFLAGKey.FOLLOWING, 0)
    actor_cflag.set(actor, CFLAGKey.FOLLOW_READY, 0)
    actor.sync_derived_fields()


def stage_threshold(key: str):
    return _stage(key)


def make_app():
    return create_application(_REPO_ROOT)
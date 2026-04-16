"""Save/load helpers for the erAL runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from eral.content.stat_axes import StatAxisCatalog
from eral.content.tw_axis_registry import TwAxisRegistry
from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState, PortLocation, TimeSlot, WorldState
from eral.engine.paths import RuntimePaths
from eral.engine.runtime_logger import RuntimeLogger


@dataclass(slots=True)
class SaveService:
    """Serialize and restore world state using a single quicksave slot."""

    paths: RuntimePaths
    stat_axes: StatAxisCatalog
    tw_axes: TwAxisRegistry
    runtime_logger: RuntimeLogger | None = None

    def quicksave_path(self) -> Path:
        return self.paths.saves / "quicksave.json"

    def has_quicksave(self) -> bool:
        return self.quicksave_path().exists()

    def save_world(self, world: WorldState) -> Path:
        path = self.quicksave_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "current_day": world.current_day,
            "current_time_slot": world.current_time_slot.value,
            "player_name": world.player_name,
            "active_location": {
                "key": world.active_location.key,
                "display_name": world.active_location.display_name,
            },
            "world_conditions": world.conditions,
            "personal_funds": world.personal_funds,
            "port_funds": world.port_funds,
            "facility_levels": dict(world.facility_levels),
            "characters": [self._serialize_actor(actor) for actor in world.characters],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if self.runtime_logger is not None:
            self.runtime_logger.append(
                kind="save",
                action_key="save",
                actor_key=None,
                day=world.current_day,
                time_slot=world.current_time_slot.value,
                location_key=world.active_location.key,
                save_path=path.name,
                triggered_events=[],
            )
        return path

    def load_world(self) -> WorldState:
        payload = json.loads(self.quicksave_path().read_text(encoding="utf-8"))
        world = WorldState(
            current_day=int(payload["current_day"]),
            current_time_slot=TimeSlot.from_name(payload["current_time_slot"]),
            player_name=payload["player_name"],
            active_location=PortLocation(
                key=payload["active_location"]["key"],
                display_name=payload["active_location"]["display_name"],
            ),
            characters=[],
        )
        world.conditions = {str(k): int(v) for k, v in payload.get("world_conditions", {}).items()}
        world.personal_funds = int(payload.get("personal_funds", 0))
        world.port_funds = int(payload.get("port_funds", 0))
        world.facility_levels = {str(k): int(v) for k, v in payload.get("facility_levels", {}).items()}

        for actor_payload in payload["characters"]:
            stats = ActorNumericState.zeroed(self.stat_axes, self.tw_axes)
            stats.base.values.update({str(k): int(v) for k, v in actor_payload["stats"]["base"].items()})
            stats.palam.values.update({str(k): int(v) for k, v in actor_payload["stats"]["palam"].items()})
            stats.source.values.update({str(k): int(v) for k, v in actor_payload["stats"]["source"].items()})
            stats.compat.abl.values.update({int(k): int(v) for k, v in actor_payload["stats"]["abl"].items()})
            stats.compat.talent.values.update({int(k): int(v) for k, v in actor_payload["stats"]["talent"].items()})
            stats.compat.cflag.values.update({int(k): int(v) for k, v in actor_payload["stats"]["cflag"].items()})
            stats.abl_exp.update({int(k): int(v) for k, v in actor_payload["stats"].get("abl_exp", {}).items()})

            actor = CharacterState(
                key=actor_payload["key"],
                display_name=actor_payload["display_name"],
                location_key=actor_payload["location_key"],
                stats=stats,
                tags=tuple(actor_payload.get("tags", [])),
            )
            actor.previous_location_key = actor_payload.get("previous_location_key")
            actor.encounter_location_key = actor_payload.get("encounter_location_key")
            actor.affection = int(actor_payload.get("affection", stats.compat.cflag.get(2)))
            actor.trust = int(actor_payload.get("trust", stats.compat.cflag.get(4)))
            actor.obedience = int(actor_payload.get("obedience", stats.compat.cflag.get(6)))
            actor.is_same_room = bool(actor_payload.get("is_same_room", stats.compat.cflag.get(319) > 0))
            actor.is_following = bool(actor_payload.get("is_following", stats.compat.cflag.get(320) > 0))
            actor.follow_ready = bool(actor_payload.get("follow_ready", stats.compat.cflag.get(329) > 0))
            actor.is_on_date = bool(actor_payload.get("is_on_date", stats.compat.cflag.get(12) > 0))
            actor.is_on_commission = bool(actor_payload.get("is_on_commission", False))
            actor.fatigue = int(actor_payload.get("fatigue", 0))
            actor.marks = {str(k): int(v) for k, v in actor_payload.get("marks", {}).items()}
            actor.conditions = {str(k): int(v) for k, v in actor_payload.get("conditions", {}).items()}
            actor.sync_compat_from_runtime()
            world.characters.append(actor)

        return world

    @staticmethod
    def _serialize_actor(actor: CharacterState) -> dict[str, object]:
        return {
            "key": actor.key,
            "display_name": actor.display_name,
            "location_key": actor.location_key,
            "tags": list(actor.tags),
            "previous_location_key": actor.previous_location_key,
            "encounter_location_key": actor.encounter_location_key,
            "affection": actor.affection,
            "trust": actor.trust,
            "obedience": actor.obedience,
            "is_same_room": actor.is_same_room,
            "is_following": actor.is_following,
            "follow_ready": actor.follow_ready,
            "is_on_date": actor.is_on_date,
            "is_on_commission": actor.is_on_commission,
            "fatigue": actor.fatigue,
            "marks": actor.marks,
            "conditions": actor.conditions,
            "stats": {
                "base": actor.stats.base.values,
                "palam": actor.stats.palam.values,
                "source": actor.stats.source.values,
                "abl": actor.stats.compat.abl.values,
                "talent": actor.stats.compat.talent.values,
                "cflag": actor.stats.compat.cflag.values,
                "abl_exp": actor.stats.abl_exp,
            },
        }

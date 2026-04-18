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
            "current_year": world.current_year,
            "current_month": world.current_month,
            "current_day": world.current_day,
            "current_weekday": world.current_weekday,
            "current_hour": world.current_hour,
            "current_minute": world.current_minute,
            "current_time_slot": world.derive_time_slot().value,
            "player_name": world.player_name,
            "active_location": {
                "key": world.active_location.key,
                "display_name": world.active_location.display_name,
            },
            "world_conditions": world.conditions,
            "personal_funds": world.personal_funds,
            "port_funds": world.port_funds,
            "training_active": world.training_active,
            "training_actor_key": world.training_actor_key,
            "training_position_key": world.training_position_key,
            "training_step_index": world.training_step_index,
            "training_flags": dict(world.training_flags),
            "inventory": dict(world.inventory),
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
        current_hour = int(payload.get("current_hour", 8))
        current_minute = int(payload.get("current_minute", 0))
        current_time_slot = payload.get("current_time_slot")
        active_location_payload = payload.get("active_location", {})
        active_location_key = str(active_location_payload.get("key", "command_office"))
        active_location_name = str(
            active_location_payload.get("display_name", active_location_key)
        )
        world = WorldState(
            current_year=int(payload.get("current_year", 1)),
            current_month=int(payload.get("current_month", 1)),
            current_day=int(payload["current_day"]),
            current_time_slot=TimeSlot.from_name(
                str(current_time_slot) if current_time_slot is not None else "morning"
            ),
            current_weekday=str(payload.get("current_weekday", "mon")),
            current_hour=current_hour,
            current_minute=current_minute,
            player_name=payload["player_name"],
            active_location=PortLocation(
                key=active_location_key,
                display_name=active_location_name,
            ),
            characters=[],
        )
        if current_time_slot is None:
            world.sync_time_slot_from_clock()
        world.conditions = {str(k): int(v) for k, v in payload.get("world_conditions", {}).items()}
        world.personal_funds = int(payload.get("personal_funds", 0))
        world.port_funds = int(payload.get("port_funds", 0))
        world.training_active = bool(payload.get("training_active", False))
        training_actor_key = payload.get("training_actor_key")
        world.training_actor_key = (
            str(training_actor_key) if training_actor_key is not None else None
        )
        training_position_key = payload.get("training_position_key")
        world.training_position_key = (
            str(training_position_key) if training_position_key is not None else None
        )
        world.training_step_index = int(payload.get("training_step_index", 0))
        training_flags_payload = payload.get("training_flags", {})
        world.training_flags = {}
        if isinstance(training_flags_payload, dict):
            for key, value in training_flags_payload.items():
                try:
                    world.training_flags[str(key)] = int(value)
                except (TypeError, ValueError):
                    continue
        world.inventory = self._load_inventory(payload.get("inventory", {}))
        world.facility_levels = {str(k): int(v) for k, v in payload.get("facility_levels", {}).items()}

        for actor_payload in payload["characters"]:
            stats = ActorNumericState.zeroed(self.stat_axes, self.tw_axes)
            actor_stats_payload = actor_payload.get("stats", {})
            stats.base.values.update(
                {str(k): int(v) for k, v in actor_stats_payload.get("base", {}).items()}
            )
            stats.palam.values.update(
                {str(k): int(v) for k, v in actor_stats_payload.get("palam", {}).items()}
            )
            stats.source.values.update(
                {str(k): int(v) for k, v in actor_stats_payload.get("source", {}).items()}
            )
            stats.compat.abl.values.update(
                {int(k): int(v) for k, v in actor_stats_payload.get("abl", {}).items()}
            )
            stats.compat.talent.values.update(
                {int(k): int(v) for k, v in actor_stats_payload.get("talent", {}).items()}
            )
            stats.compat.cflag.values.update(
                {int(k): int(v) for k, v in actor_stats_payload.get("cflag", {}).items()}
            )
            stats.abl_exp.update(
                {int(k): int(v) for k, v in actor_stats_payload.get("abl_exp", {}).items()}
            )

            actor = CharacterState(
                key=actor_payload["key"],
                display_name=actor_payload["display_name"],
                location_key=str(actor_payload.get("location_key", active_location_key)),
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
            actor.owned_skins = {
                str(skin_key) for skin_key in actor_payload.get("owned_skins", [])
            }
            actor.equipped_skin_key = actor_payload.get("equipped_skin_key")
            actor.removed_slots = tuple(
                str(slot) for slot in actor_payload.get("removed_slots", [])
            )
            if not actor.owned_skins:
                actor.owned_skins = {f"{actor.key}_default"}
            if actor.equipped_skin_key is None:
                actor.equipped_skin_key = f"{actor.key}_default"
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
            "owned_skins": sorted(actor.owned_skins),
            "equipped_skin_key": actor.equipped_skin_key,
            "removed_slots": list(actor.removed_slots),
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

    @staticmethod
    def _load_inventory(payload: object) -> dict[str, int]:
        if not isinstance(payload, dict):
            return {}
        inventory: dict[str, int] = {}
        for key, value in payload.items():
            try:
                count = int(value)
            except (TypeError, ValueError):
                continue
            if count <= 0:
                continue
            inventory[str(key)] = count
        return inventory

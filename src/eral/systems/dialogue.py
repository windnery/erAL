"""Dialogue selection from event or action keys with scene-condition filtering."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.dialogue import DialogueEntry
from eral.domain.scene import SceneContext


@dataclass(slots=True)
class DialogueService:
    """Pick dialogue lines for a resolved event or action.

    When multiple entries match the same key and actor, the one with the
    highest ``priority`` wins.  Entries with scene conditions that do not
    match the current context are skipped.
    """

    entries: tuple[DialogueEntry, ...]

    def lines_for(self, scene: SceneContext, triggered_events: tuple[str, ...]) -> tuple[str, ...]:
        for event_key in triggered_events:
            event_lines = self._lookup(event_key, scene)
            if event_lines:
                return event_lines
        return self._lookup(scene.action_key, scene)

    def _lookup(self, key: str, scene: SceneContext) -> tuple[str, ...]:
        best: DialogueEntry | None = None
        fallback: DialogueEntry | None = None
        for entry in self.entries:
            if entry.key != key:
                continue
            if entry.actor_key == "_any":
                if not self._matches(entry, scene):
                    continue
                if fallback is None or entry.priority > fallback.priority:
                    fallback = entry
                continue
            if entry.actor_key != scene.actor_key:
                continue
            if not self._matches(entry, scene):
                continue
            if best is None or entry.priority > best.priority:
                best = entry
        if best is not None:
            return best.lines
        return fallback.lines if fallback is not None else ()

    @staticmethod
    def _matches(entry: DialogueEntry, scene: SceneContext) -> bool:
        if entry.required_stage is not None and scene.relationship_stage != entry.required_stage:
            return False
        if entry.time_slots and scene.time_slot not in entry.time_slots:
            return False
        if entry.location_keys and scene.location_key not in entry.location_keys:
            return False
        if entry.min_affection is not None and scene.affection < entry.min_affection:
            return False
        if entry.min_trust is not None and scene.trust < entry.min_trust:
            return False
        if entry.min_obedience is not None and scene.obedience < entry.min_obedience:
            return False
        if entry.requires_private is not None and scene.is_private != entry.requires_private:
            return False
        if entry.requires_date is not None and scene.is_on_date != entry.requires_date:
            return False
        if entry.requires_following is not None and scene.is_following != entry.requires_following:
            return False
        if entry.required_skin_key is not None and scene.equipped_skin_key != entry.required_skin_key:
            return False
        if entry.required_skin_tags and not all(
            tag in scene.equipped_skin_tags for tag in entry.required_skin_tags
        ):
            return False
        if entry.required_removed_slots and not all(
            slot in scene.removed_slots for slot in entry.required_removed_slots
        ):
            return False
        if entry.forbidden_removed_slots and any(
            slot in scene.removed_slots for slot in entry.forbidden_removed_slots
        ):
            return False
        if entry.requires_training is not None and scene.is_training != entry.requires_training:
            return False
        if entry.required_training_results and not all(
            r in scene.training_results for r in entry.required_training_results
        ):
            return False
        for mark_key, min_level in entry.required_marks.items():
            if scene.marks.get(mark_key, 0) < min_level:
                return False
        for memory_key, min_count in entry.required_memories.items():
            if scene.memories.get(memory_key, 0) < min_count:
                return False
        return True

"""Persistent state and body slot domain models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SlotDefinition:
    key: str
    display_name: str
    capacity: int = 1
    blocked_by: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PersistentStateDefinition:
    key: str
    display_name: str
    occupies_slots: tuple[str, ...] = ()
    source_per_turn: dict[str, int] = field(default_factory=dict)
    clear_on: tuple[str, ...] = ()


def occupied_slot_counts(
    active_states: set[str],
    definitions: dict[str, PersistentStateDefinition],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for ps_key in active_states:
        ps_def = definitions.get(ps_key)
        if ps_def is None:
            continue
        for slot in ps_def.occupies_slots:
            result[slot] = result.get(slot, 0) + 1
    return result


def is_slot_available(
    slot_key: str,
    occupied: dict[str, int],
    slot_defs: dict[str, SlotDefinition],
) -> bool:
    slot_def = slot_defs.get(slot_key)
    if slot_def is None:
        return True
    if occupied.get(slot_key, 0) >= slot_def.capacity:
        return False
    for blocker in slot_def.blocked_by:
        if occupied.get(blocker, 0) > 0:
            return False
    return True


def can_activate(
    ps_key: str,
    active_states: set[str],
    ps_defs: dict[str, PersistentStateDefinition],
    slot_defs: dict[str, SlotDefinition],
) -> bool:
    if ps_key in active_states:
        return True
    ps_def = ps_defs.get(ps_key)
    if ps_def is None:
        return False
    occupied = occupied_slot_counts(active_states, ps_defs)
    for slot in ps_def.occupies_slots:
        if not is_slot_available(slot, occupied, slot_defs):
            return False
    return True


def persistent_source(
    active_states: set[str],
    definitions: dict[str, PersistentStateDefinition],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for ps_key in active_states:
        ps_def = definitions.get(ps_key)
        if ps_def is None:
            continue
        for source_key, value in ps_def.source_per_turn.items():
            result[source_key] = result.get(source_key, 0) + value
    return result


def clear_states_by_event(
    active_states: set[str],
    event: str,
    definitions: dict[str, PersistentStateDefinition],
) -> set[str]:
    to_remove = set()
    for ps_key in active_states:
        ps_def = definitions.get(ps_key)
        if ps_def is not None and event in ps_def.clear_on:
            to_remove.add(ps_key)
    return active_states - to_remove

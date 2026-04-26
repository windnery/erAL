"""Load declarative command effects from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourcePayload:
    """Raw SOURCE values for the settlement pipeline."""

    target: dict[int, int] = field(default_factory=dict)
    player: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VitalsPayload:
    """Vitals deltas (stamina/spirit/energy costs) routed through VitalService."""

    target: dict[int, int] = field(default_factory=dict)
    player: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExperienceGain:
    """Declarative EXP deltas."""

    target: dict[int, int] = field(default_factory=dict)
    player: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuntimeConditionDelta:
    """Declarative runtime-condition deltas keyed by erAL condition names."""

    target: dict[str, int] = field(default_factory=dict)
    player: dict[str, int] = field(default_factory=dict)
    world: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CommandEffect:
    """Declarative effect bundle for one train command index."""

    command_index: int
    source: SourcePayload = field(default_factory=SourcePayload)
    vitals: VitalsPayload | None = None
    experience: ExperienceGain | None = None
    conditions: RuntimeConditionDelta | None = None


def _parse_int_dict(raw: dict) -> dict[int, int]:
    return {int(k): int(v) for k, v in raw.items()}


def _parse_str_int_dict(raw: dict) -> dict[str, int]:
    return {str(k): int(v) for k, v in raw.items()}


def load_command_effects(path: Path) -> dict[int, CommandEffect]:
    """Load command effects keyed by command index.

    ``command_effects.toml`` is intentionally limited to declarative payloads.
    Command metadata belongs in ``train.toml`` and complex operations/gates stay
    in Python orchestration code.
    """

    if not path.exists():
        return {}

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: dict[int, CommandEffect] = {}
    for item in raw.get("effect", []):
        cmd_index = int(item["command_index"])

        raw_source = item.get("source", {})
        source = SourcePayload(
            target=_parse_int_dict(raw_source.get("target", {})),
            player=_parse_int_dict(raw_source.get("player", {})),
        )

        raw_vitals = item.get("vitals")
        vitals = None
        if raw_vitals:
            vitals = VitalsPayload(
                target=_parse_int_dict(raw_vitals.get("target", {})),
                player=_parse_int_dict(raw_vitals.get("player", {})),
            )

        raw_exp = item.get("experience")
        experience = None
        if raw_exp:
            experience = ExperienceGain(
                target=_parse_int_dict(raw_exp.get("target", {})),
                player=_parse_int_dict(raw_exp.get("player", {})),
            )

        raw_cond = item.get("conditions")
        conditions = None
        if raw_cond:
            conditions = RuntimeConditionDelta(
                target=_parse_str_int_dict(raw_cond.get("target", {})),
                player=_parse_str_int_dict(raw_cond.get("player", {})),
                world=_parse_str_int_dict(raw_cond.get("world", {})),
            )

        effect = CommandEffect(
            command_index=cmd_index,
            source=source,
            vitals=vitals,
            experience=experience,
            conditions=conditions,
        )
        result[effect.command_index] = effect

    return result

"""Load command effect definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourcePayload:
    """Raw SOURCE values for settlement pipeline."""

    target: dict[int, int] = field(default_factory=dict)
    player: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VitalsCost:
    """DOWNBASE deltas (stamina / energy / etc.)."""

    target: dict[int, int] = field(default_factory=dict)
    player: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExperienceGain:
    """EXP deltas."""

    target: dict[int, int] = field(default_factory=dict)
    player: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConditionSet:
    """Temporary flags for current command execution."""

    tcvar: dict[int, int] = field(default_factory=dict)
    tflag: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CommandEffect:
    """Complete effect bundle for a single command."""

    command_index: int
    source: SourcePayload = field(default_factory=SourcePayload)
    vitals: VitalsCost | None = None
    experience: ExperienceGain | None = None
    conditions: ConditionSet | None = None
    # Future categories (stains, resources, scene, equipment) added here


def _parse_int_dict(raw: dict) -> dict[int, int]:
    return {int(k): int(v) for k, v in raw.items()}


def load_command_effects(path: Path) -> dict[int, CommandEffect]:
    """Load command effects keyed by command index."""

    if not path.exists():
        return {}

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: dict[int, CommandEffect] = {}
    for item in raw.get("effect", []):
        cmd_index = int(item["command_index"])

        # [source] table
        raw_source = item.get("source", {})
        source = SourcePayload(
            target=_parse_int_dict(raw_source.get("target", {})),
            player=_parse_int_dict(raw_source.get("player", {})),
        )

        # [vitals] table
        raw_vitals = item.get("vitals")
        vitals = None
        if raw_vitals:
            vitals = VitalsCost(
                target=_parse_int_dict(raw_vitals.get("target", {})),
                player=_parse_int_dict(raw_vitals.get("player", {})),
            )

        # [experience] table
        raw_exp = item.get("experience")
        experience = None
        if raw_exp:
            experience = ExperienceGain(
                target=_parse_int_dict(raw_exp.get("target", {})),
                player=_parse_int_dict(raw_exp.get("player", {})),
            )

        # [conditions] table
        raw_cond = item.get("conditions")
        conditions = None
        if raw_cond:
            conditions = ConditionSet(
                tcvar=_parse_int_dict(raw_cond.get("tcvar", {})),
                tflag=_parse_int_dict(raw_cond.get("tflag", {})),
            )

        eff = CommandEffect(
            command_index=cmd_index,
            source=source,
            vitals=vitals,
            experience=experience,
            conditions=conditions,
        )
        result[eff.command_index] = eff

    return result

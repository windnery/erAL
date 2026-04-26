"""Load ABL upgrade definitions matching eraTW multi-route semantics."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AblRequirement:
    """Cross-ABL dependency: required ABL must be >= current level + offset."""

    abl_index: int
    min_level_offset: int


@dataclass(frozen=True, slots=True)
class AblDiscount:
    """Dynamic JUEL demand discount based on an EXP axis."""

    exp_key: str
    numerator: int = 1
    denominator_offset: int = 0
    level_numerator_offset: int = 0


@dataclass(frozen=True, slots=True)
class AblRoute:
    """One upgrade route consuming specific JUEL types.

    ``juel_costs`` maps juel_key -> per-level demand table.
    Most routes have a single entry; some TW routes require multiple
    JUEL types simultaneously (e.g. 受虐属性 route 0 needs both
    欲情珠 and 苦痛珠).
    """

    juel_costs: dict[str, tuple[int, ...]]
    exp_requirements: dict[str, tuple[int, ...]]
    discount_factors: tuple[AblDiscount, ...]


@dataclass(frozen=True, slots=True)
class AblDefinition:
    """Per-ABL upgrade configuration."""

    abl_index: int
    label: str
    upgrade_mode: str  # "juel_exp" or "exp_direct"
    rate: float
    requirements: tuple[AblRequirement, ...]
    routes: tuple[AblRoute, ...]
    # For exp_direct mode
    exp_direct_key: str | None = None
    exp_direct_offset: int = 3


@dataclass(frozen=True, slots=True)
class AblUpgradeConfig:
    """Top-level ABL upgrade configuration."""

    max_level_without_love: int
    max_level_with_love: int
    max_level_with_oath: int
    explv: tuple[int, ...]
    definitions: tuple[AblDefinition, ...]


def _parse_discounts(raw_list: list[dict]) -> tuple[AblDiscount, ...]:
    return tuple(
        AblDiscount(
            exp_key=str(item["exp_key"]),
            numerator=int(item.get("numerator", 1)),
            denominator_offset=int(item.get("denominator_offset", 0)),
            level_numerator_offset=int(item.get("level_numerator_offset", 0)),
        )
        for item in raw_list
    )


def _parse_routes(raw_list: list[dict]) -> tuple[AblRoute, ...]:
    routes: list[AblRoute] = []
    for item in raw_list:
        exp_reqs: dict[str, tuple[int, ...]] = {}
        for k, v in item.get("exp_requirements", {}).items():
            if isinstance(v, list):
                exp_reqs[str(k)] = tuple(int(x) for x in v)
            else:
                exp_reqs[str(k)] = (int(v),)
        discounts = _parse_discounts(item.get("discount", []))
        # Support both legacy single-key "juel_key"/"juel_table" and
        # multi-key "juel_costs" for routes that need several JUELs.
        if "juel_costs" in item:
            juel_costs = {
                str(k): tuple(int(vv) for vv in v)
                for k, v in item["juel_costs"].items()
            }
        else:
            juel_table = tuple(int(v) for v in item.get("juel_table", []))
            juel_costs = {str(item["juel_key"]): juel_table}
        routes.append(
            AblRoute(
                juel_costs=juel_costs,
                exp_requirements=exp_reqs,
                discount_factors=discounts,
            )
        )
    return tuple(routes)


def _parse_requirements(raw_list: list[dict]) -> tuple[AblRequirement, ...]:
    return tuple(
        AblRequirement(
            abl_index=int(item["abl_index"]),
            min_level_offset=int(item.get("min_level_offset", 1)),
        )
        for item in raw_list
    )


def load_abl_upgrade_config(path: Path) -> AblUpgradeConfig:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    max_level_without_love = int(raw.get("max_level_without_love", 5))
    max_level_with_love = int(raw.get("max_level_with_love", 10))
    max_level_with_oath = int(raw.get("max_level_with_oath", 99))

    explv_raw = raw.get("explv", {})
    max_level = max(int(k) for k in explv_raw.keys()) if explv_raw else 0
    explv = tuple(explv_raw.get(str(i), 10000) for i in range(max_level + 2))

    definitions = []
    for item in raw.get("abl", []):
        mode = item.get("upgrade_mode", "juel_exp")
        definitions.append(
            AblDefinition(
                abl_index=int(item["abl_index"]),
                label=item["label"],
                upgrade_mode=mode,
                rate=float(item.get("rate", 1.0)),
                requirements=_parse_requirements(item.get("requirements", [])),
                routes=_parse_routes(item.get("routes", [])),
                exp_direct_key=item.get("exp_direct_key"),
                exp_direct_offset=int(item.get("exp_direct_offset", 3)),
            )
        )

    return AblUpgradeConfig(
        max_level_without_love=max_level_without_love,
        max_level_with_love=max_level_with_love,
        max_level_with_oath=max_level_with_oath,
        explv=explv,
        definitions=tuple(definitions),
    )

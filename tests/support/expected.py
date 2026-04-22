"""Expected-value factories for settlement, FAVOR_CALC, and TRUST_CALC.

Tests should call these functions instead of hard-coding numeric results.
When formulas or thresholds change, only this file needs updating.
"""

from __future__ import annotations

from eral.content.relationships import RelationshipStageDefinition
from eral.systems.favor_calc import GrowthFormula, compute_favor_delta, compute_trust_delta
from eral.domain.stats import ActorNumericState

_STAGES_TUPLE = None
_FAVOR_FORMULA = None
_TRUST_FORMULA = None
_REPO_ROOT = None


def _ensure_loaded():
    global _STAGES_TUPLE, _FAVOR_FORMULA, _TRUST_FORMULA, _REPO_ROOT
    if _STAGES_TUPLE is not None:
        return
    from pathlib import Path
    from eral.content.relationships import load_relationship_stages
    from eral.systems.favor_calc import load_growth_formula as _load_favor, load_trust_formula as _load_trust
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    _STAGES_TUPLE = load_relationship_stages(_REPO_ROOT / "data" / "base" / "relationship_stages.toml")
    _FAVOR_FORMULA = _load_favor(_REPO_ROOT / "data" / "base" / "relationship_growth.toml")
    _TRUST_FORMULA = _load_trust(_REPO_ROOT / "data" / "base" / "relationship_growth.toml")


def favor_delta(source_dict: dict[str, int], stage_key: str = "stranger") -> int:
    _ensure_loaded()
    stats = _make_zero_stats()
    for k, v in source_dict.items():
        stats.source.set(k, v)
    return compute_favor_delta(stats, stage_key, _FAVOR_FORMULA)


def trust_delta(source_dict: dict[str, int], stage_key: str = "stranger") -> int:
    _ensure_loaded()
    stats = _make_zero_stats()
    for k, v in source_dict.items():
        stats.source.set(k, v)
    return compute_trust_delta(stats, stage_key, _TRUST_FORMULA)


def stage_affection(key: str) -> int:
    _ensure_loaded()
    for s in _STAGES_TUPLE:
        if s.key == key:
            return s.min_affection
    raise KeyError(key)


def stage_trust(key: str) -> int:
    _ensure_loaded()
    for s in _STAGES_TUPLE:
        if s.key == key:
            return s.min_trust
    raise KeyError(key)


def stage_intimacy(key: str) -> int:
    _ensure_loaded()
    for s in _STAGES_TUPLE:
        if s.key == key:
            return s.min_intimacy
    raise KeyError(key)


def favor_stage_multiplier(stage_key: str) -> float:
    _ensure_loaded()
    return _FAVOR_FORMULA.relationship_stage_multiplier.get(stage_key, 1.0)


def trust_stage_multiplier(stage_key: str) -> float:
    _ensure_loaded()
    return _TRUST_FORMULA.relationship_stage_multiplier.get(stage_key, 1.0)


_OBEDIENCE_SCALE = 0.05


def cflag_obedience_delta(source_obedience: int) -> int:
    return int(source_obedience * _OBEDIENCE_SCALE)


def _make_zero_stats() -> ActorNumericState:
    from eral.content.stat_axes import load_stat_axis_catalog
    _ensure_loaded()
    stat_axes = load_stat_axis_catalog(_REPO_ROOT / "data" / "base" / "axes")
    return ActorNumericState.zeroed(stat_axes)
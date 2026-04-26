"""Apply command effects to actor state."""

from __future__ import annotations

from eral.domain.stats import ActorNumericState
from eral.content.command_effects import CommandEffect
from eral.domain.world import CharacterState
from eral.systems.vital import VitalService


def apply_command_effect(
    actor: CharacterState,
    effect: CommandEffect | None,
    player: CharacterState | ActorNumericState | None = None,
    vital_service: VitalService | None = None,
) -> None:
    """Write command effect values into actor/player state.

    * source.target → actor.stats.source
    * source.player → player.stats.source (if player provided)
    * vitals.target → actor base deductions (via VitalService if available)
    * vitals.player → player base deductions
    * experience.target → actor.abl_exp
    * experience.player → player.abl_exp
    * conditions.target/player/world → runtime condition deltas
    """

    if effect is None:
        return

    actor_stats = actor.stats
    player_stats = _resolve_stats_block(player)

    # SOURCE payload (settlement pipeline input)
    for source_index, value in effect.source.target.items():
        actor_stats.source.add(str(source_index), value)

    if player_stats is not None:
        for source_index, value in effect.source.player.items():
            player_stats.source.add(str(source_index), value)

    # VITALS payload (stamina/spirit/energy costs)
    if effect.vitals is not None:
        _apply_vitals(actor, effect.vitals.target, vital_service)
        if player_stats is not None:
            _apply_vitals(_resolve_character(player), effect.vitals.player, vital_service)

    # EXPERIENCE payload (writes into the EXP stat block)
    if effect.experience is not None:
        for exp_index, value in effect.experience.target.items():
            actor_stats.exp.add(str(exp_index), value)
        if player_stats is not None:
            for exp_index, value in effect.experience.player.items():
                player_stats.exp.add(str(exp_index), value)

    # CONDITIONS payload
    if effect.conditions is not None:
        for cond_key, value in effect.conditions.target.items():
            actor.add_condition(cond_key, value)
        if player_stats is not None:
            player_char = _resolve_character(player)
            if player_char is not None:
                for cond_key, value in effect.conditions.player.items():
                    player_char.add_condition(cond_key, value)
        for cond_key, value in effect.conditions.world.items():
            # world conditions are handled by the caller; skip here
            pass


def _apply_vitals(
    actor: CharacterState,
    vitals: dict[int, int],
    vital_service: VitalService | None = None,
) -> None:
    """Apply vitals deltas to actor."""
    vitals_str = {str(k): v for k, v in vitals.items()}
    if vital_service is not None:
        vital_service.apply_downbase(actor, vitals_str)
    else:
        for base_key, delta in vitals_str.items():
            current = actor.stats.base.get(base_key)
            new_val = max(0, current - delta)
            actor.stats.base.set(base_key, new_val)


def _resolve_stats_block(
    actor_or_stats: CharacterState | ActorNumericState | None,
) -> ActorNumericState | None:
    if actor_or_stats is None:
        return None
    if isinstance(actor_or_stats, ActorNumericState):
        return actor_or_stats
    return actor_or_stats.stats


def _resolve_character(
    actor_or_stats: CharacterState | ActorNumericState | None,
) -> CharacterState | None:
    if actor_or_stats is None or isinstance(actor_or_stats, CharacterState):
        return actor_or_stats
    return None

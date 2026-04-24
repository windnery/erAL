"""Apply command effects to actor state."""

from __future__ import annotations

from eral.domain.stats import ActorNumericState
from eral.content.command_effects import CommandEffect
from eral.domain.world import CharacterState


def apply_command_effect(
    actor: CharacterState,
    effect: CommandEffect | None,
    player: CharacterState | ActorNumericState | None = None,
) -> None:
    """Write command effect values into actor/player state.

    * source.target → actor.stats.source
    * source.player → player.stats.source (if player provided)
    * vitals.target → actor base deductions (TODO: wire to VitalService)
    * vitals.player → player base deductions (TODO)
    * experience.target → actor exp gains (TODO)
    * experience.player → player exp gains (TODO)
    * conditions.tcvar/tflag → world temp flags (TODO)
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

    # TODO: apply vitals, experience, conditions when systems are ready


def _resolve_stats_block(
    actor_or_stats: CharacterState | ActorNumericState | None,
) -> ActorNumericState | None:
    if actor_or_stats is None:
        return None
    if isinstance(actor_or_stats, ActorNumericState):
        return actor_or_stats
    return actor_or_stats.stats

"""Commission system: dispatch, tick, and finalize dispatched commissions."""

from __future__ import annotations

from dataclasses import dataclass, field

from eral.content.commissions import CommissionDefinition
from eral.domain.world import CharacterState, WorldState
from eral.systems.facilities import FacilityService
from eral.systems.wallet import WalletService


@dataclass(slots=True)
class CommissionAssignment:
    """Tracks an active commission assignment on a character."""

    commission_key: str
    remaining_slots: int
    start_day: int
    start_slot: str


@dataclass(slots=True)
class CommissionService:
    """Coordinate commission dispatch, time advancement, and reward settlement."""

    definitions: tuple[CommissionDefinition, ...]
    wallet: WalletService | None = None
    facility_service: FacilityService | None = None

    def _def_by_key(self, key: str) -> CommissionDefinition | None:
        for d in self.definitions:
            if d.key == key:
                return d
        return None

    def dispatch(
        self,
        world: WorldState,
        actor: CharacterState,
        commission_key: str,
    ) -> bool:
        """Dispatch an actor on a commission. Returns False if not possible."""
        if actor.is_on_commission or actor.is_following or actor.is_on_date:
            return False
        cdef = self._def_by_key(commission_key)
        if cdef is None:
            return False

        actor.is_on_commission = True
        actor.commission_assignment = CommissionAssignment(
            commission_key=commission_key,
            remaining_slots=cdef.duration_slots,
            start_day=world.current_day,
            start_slot=world.current_time_slot.value,
        )
        return True

    def tick_slot(self, world: WorldState) -> list[str]:
        """Advance all active commissions by one slot. Returns list of finalized keys."""
        finalized: list[str] = []
        for actor in world.characters:
            if not actor.is_on_commission or actor.commission_assignment is None:
                continue
            actor.commission_assignment.remaining_slots -= 1
            if actor.commission_assignment.remaining_slots <= 0:
                key = actor.commission_assignment.commission_key
                self._finalize(world, actor, key)
                finalized.append(key)
        return finalized

    def _finalize(
        self,
        world: WorldState,
        actor: CharacterState,
        commission_key: str,
    ) -> None:
        """Finalize a commission: pay rewards and clear assignment."""
        cdef = self._def_by_key(commission_key)
        if cdef is not None and self.wallet is not None and cdef.port_income > 0:
            income = cdef.port_income
            if self.facility_service is not None:
                income = int(income * self.facility_service.income_multiplier(world))
            self.wallet.add_port(
                world, income, reason="commission", source_key=commission_key,
            )
        actor.is_on_commission = False
        actor.commission_assignment = None

"""Wallet service: unified interface for personal and port funds."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import WorldState


@dataclass(slots=True)
class WalletService:
    """All fund mutations go through this service."""

    def add_personal(
        self,
        world: WorldState,
        amount: int,
        reason: str = "",
        source_key: str | None = None,
    ) -> int:
        if amount <= 0:
            return 0
        world.personal_funds += amount
        return amount

    def add_port(
        self,
        world: WorldState,
        amount: int,
        reason: str = "",
        source_key: str | None = None,
    ) -> int:
        if amount <= 0:
            return 0
        world.port_funds += amount
        return amount

    def spend_personal(
        self,
        world: WorldState,
        amount: int,
        reason: str = "",
        source_key: str | None = None,
    ) -> bool:
        if amount <= 0 or world.personal_funds < amount:
            return False
        world.personal_funds -= amount
        return True

    def spend_port(
        self,
        world: WorldState,
        amount: int,
        reason: str = "",
        source_key: str | None = None,
    ) -> bool:
        if amount <= 0 or world.port_funds < amount:
            return False
        world.port_funds -= amount
        return True

    def transfer_to_port(self, world: WorldState, amount: int) -> bool:
        if amount <= 0 or world.personal_funds < amount:
            return False
        world.personal_funds -= amount
        world.port_funds += amount
        return True

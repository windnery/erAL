"""WalletService unit tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from tests.support.real_actors import actor_by_key

_REPO_ROOT = Path(__file__).resolve().parents[1]


class WalletServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_application(_REPO_ROOT)
        self.wallet = self.app.wallet_service

    def test_add_personal_increases_funds(self) -> None:
        result = self.wallet.add_personal(self.app.world, 50, reason="test")
        self.assertEqual(result, 50)
        self.assertEqual(self.app.world.personal_funds, 50)

    def test_add_personal_ignores_non_positive(self) -> None:
        self.assertEqual(self.wallet.add_personal(self.app.world, 0), 0)
        self.assertEqual(self.wallet.add_personal(self.app.world, -10), 0)
        self.assertEqual(self.app.world.personal_funds, 0)

    def test_add_port_increases_funds(self) -> None:
        result = self.wallet.add_port(self.app.world, 100, reason="test")
        self.assertEqual(result, 100)
        self.assertEqual(self.app.world.port_funds, 100)

    def test_spend_personal_success(self) -> None:
        self.wallet.add_personal(self.app.world, 100)
        self.assertTrue(self.wallet.spend_personal(self.app.world, 30))
        self.assertEqual(self.app.world.personal_funds, 70)

    def test_spend_personal_insufficient(self) -> None:
        self.wallet.add_personal(self.app.world, 20)
        self.assertFalse(self.wallet.spend_personal(self.app.world, 50))
        self.assertEqual(self.app.world.personal_funds, 20)

    def test_spend_personal_ignores_non_positive(self) -> None:
        self.wallet.add_personal(self.app.world, 100)
        self.assertFalse(self.wallet.spend_personal(self.app.world, 0))
        self.assertFalse(self.wallet.spend_personal(self.app.world, -5))

    def test_spend_port_success(self) -> None:
        self.wallet.add_port(self.app.world, 100)
        self.assertTrue(self.wallet.spend_port(self.app.world, 40))
        self.assertEqual(self.app.world.port_funds, 60)

    def test_spend_port_insufficient(self) -> None:
        self.wallet.add_port(self.app.world, 10)
        self.assertFalse(self.wallet.spend_port(self.app.world, 20))

    def test_transfer_to_port_success(self) -> None:
        self.wallet.add_personal(self.app.world, 100)
        self.assertTrue(self.wallet.transfer_to_port(self.app.world, 30))
        self.assertEqual(self.app.world.personal_funds, 70)
        self.assertEqual(self.app.world.port_funds, 30)

    def test_transfer_to_port_insufficient(self) -> None:
        self.wallet.add_personal(self.app.world, 10)
        self.assertFalse(self.wallet.transfer_to_port(self.app.world, 50))
        self.assertEqual(self.app.world.personal_funds, 10)
        self.assertEqual(self.app.world.port_funds, 0)

    def test_transfer_to_port_ignores_non_positive(self) -> None:
        self.wallet.add_personal(self.app.world, 100)
        self.assertFalse(self.wallet.transfer_to_port(self.app.world, 0))
        self.assertFalse(self.wallet.transfer_to_port(self.app.world, -10))

    def test_multiple_operations_accumulate(self) -> None:
        self.wallet.add_personal(self.app.world, 100)
        self.wallet.add_personal(self.app.world, 50)
        self.wallet.spend_personal(self.app.world, 30)
        self.assertEqual(self.app.world.personal_funds, 120)


if __name__ == "__main__":
    unittest.main()

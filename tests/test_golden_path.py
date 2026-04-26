"""Golden path integration test: new game → move → talk → wait → rest → save/load."""

from __future__ import annotations

import shutil
import unittest
import uuid
from dataclasses import replace
from pathlib import Path

from eral.app.bootstrap import create_application


class GoldenPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(self.repo_root)
        # Use a temporary save directory so we don't clobber real saves
        temp_saves = self.app.paths.runtime / f"golden_saves_{uuid.uuid4().hex}"
        temp_saves.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, temp_saves, True)
        self.app.paths.saves = temp_saves

        # Patch command metadata so system/daily commands can run without
        # requiring training mode.  This is a test fixture; the real data
        # should be updated in train.toml by the content author.
        cmds = self.app.command_service.commands
        # 200 = 会话 → daily
        if 200 in cmds:
            cmds[200] = replace(cmds[200], category="daily")
        # 252 = 休息 → system, operation=nap
        if 252 in cmds:
            cmds[252] = replace(cmds[252], category="system", operation="nap")
        # 264 = 等待 → system
        if 264 in cmds:
            cmds[264] = replace(cmds[264], category="system")

    def test_new_game_move_talk_wait_rest_save_load(self) -> None:
        world = self.app.world
        actor = next(c for c in world.characters if c.key == "enterprise")

        # 1. Move player and actor to main_corridor
        actor.location_key = "main_corridor"
        self.app.navigation_service.execute_move(world, "main_corridor")

        self.assertEqual(world.active_location.key, "main_corridor")
        self.assertEqual(actor.location_key, "main_corridor")

        # 2. Talk (index 200)
        result_talk = self.app.command_service.execute(world, actor.key, 200)
        self.assertTrue(result_talk.success)

        # 3. Wait (index 264)
        result_wait = self.app.command_service.execute(world, actor.key, 264)
        self.assertTrue(result_wait.success)

        # 4. Rest (index 252)
        pre_rest_stamina = actor.stats.base.get("0")
        pre_rest_spirit = actor.stats.base.get("1")
        result_rest = self.app.command_service.execute(world, actor.key, 252)
        self.assertTrue(result_rest.success)
        # Recovery should have occurred via the "nap" operation
        self.assertGreater(actor.stats.base.get("0"), pre_rest_stamina)

        # Capture pre-save state
        saved_location = world.active_location.key
        saved_day = world.current_day
        saved_actor_location = actor.location_key
        saved_stamina = actor.stats.base.get("0")
        saved_spirit = actor.stats.base.get("1")

        # 5. Save
        self.app.save_service.save_world(world)

        # 6. Load
        restored_world = self.app.save_service.load_world()

        # 7. Verify key state survived round-trip
        self.assertEqual(restored_world.active_location.key, saved_location)
        self.assertEqual(restored_world.current_day, saved_day)
        restored_actor = next(
            c for c in restored_world.characters if c.key == "enterprise"
        )
        self.assertEqual(restored_actor.location_key, saved_actor_location)
        self.assertEqual(restored_actor.stats.base.get("0"), saved_stamina)
        self.assertEqual(restored_actor.stats.base.get("1"), saved_spirit)


if __name__ == "__main__":
    unittest.main()

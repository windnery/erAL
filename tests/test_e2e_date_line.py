"""End-to-end tests: date line and light intimacy line must be playable without breaks."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.world import TimeSlot


class DateLineE2ETests(unittest.TestCase):
    """Test the full date line: advance relationship -> follow -> date -> hold_hands -> end_date."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return next(actor for actor in self.app.world.characters if actor.key == "enterprise")

    def _set_time(self, slot: TimeSlot) -> None:
        self.app.world.current_time_slot = slot

    def _move_to(self, key: str) -> None:
        self.app.navigation_service.move_player(self.app.world, key)

    def _set_stage_like(self, actor) -> None:
        """Ensure actor is at least at 'like' stage."""
        actor.stats.compat.cflag.set(2, 4)
        actor.stats.compat.cflag.set(4, 3)
        self.app.relationship_service.update_actor(actor)
        self.assertGreaterEqual(actor.relationship_stage.rank, 2)

    def test_full_date_line(self) -> None:
        actor = self._actor()
        self._set_stage_like(actor)

        # 1. 邀请同行
        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("dock")
        actor.location_key = "dock"
        result = self.app.command_service.execute(self.app.world, actor.key, "invite_follow")
        self.assertEqual(result.action_key, "invite_follow")
        self.assertTrue(actor.is_following)

        # 2. 邀请约会
        result = self.app.command_service.execute(self.app.world, actor.key, "invite_date")
        self.assertEqual(result.action_key, "invite_date")
        self.assertTrue(actor.is_on_date)

        # 3. 约会散步
        self._move_to("main_corridor")
        self._move_to("garden")
        actor.location_key = "garden"
        result = self.app.command_service.execute(self.app.world, actor.key, "date_stroll")
        self.assertEqual(result.action_key, "date_stroll")

        # 4. 牵手
        result = self.app.command_service.execute(self.app.world, actor.key, "hold_hands")
        self.assertEqual(result.action_key, "hold_hands")

        # 5. 一起用餐
        self._move_to("main_corridor")
        self._move_to("cafeteria")
        actor.location_key = "cafeteria"
        result = self.app.command_service.execute(self.app.world, actor.key, "date_meal")
        self.assertEqual(result.action_key, "date_meal")

        # 6. 买便当
        result = self.app.command_service.execute(self.app.world, actor.key, "takeout_bento")
        self.assertEqual(result.action_key, "takeout_bento")

        # 7. 花店
        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("garden")
        actor.location_key = "garden"
        result = self.app.command_service.execute(self.app.world, actor.key, "flower_shop")
        self.assertEqual(result.action_key, "flower_shop")

        # 8. 结束约会
        self._set_time(TimeSlot.EVENING)
        result = self.app.command_service.execute(self.app.world, actor.key, "end_date")
        self.assertEqual(result.action_key, "end_date")
        self.assertFalse(actor.is_on_date)

    def test_date_line_with_laffey(self) -> None:
        actor = next(a for a in self.app.world.characters if a.key == "laffey")
        self._set_stage_like(actor)

        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("cafeteria")
        actor.location_key = "cafeteria"

        result = self.app.command_service.execute(self.app.world, actor.key, "invite_follow")
        self.assertEqual(result.action_key, "invite_follow")
        self.assertTrue(actor.is_following)

        result = self.app.command_service.execute(self.app.world, actor.key, "invite_date")
        self.assertEqual(result.action_key, "invite_date")
        self.assertTrue(actor.is_on_date)

        # 约会互动
        result = self.app.command_service.execute(self.app.world, actor.key, "takeout_bento")
        self.assertEqual(result.action_key, "takeout_bento")

        # 结束约会
        self._set_time(TimeSlot.EVENING)
        result = self.app.command_service.execute(self.app.world, actor.key, "end_date")
        self.assertEqual(result.action_key, "end_date")
        self.assertFalse(actor.is_on_date)


class LightIntimacyLineE2ETests(unittest.TestCase):
    """Test the light intimacy line: love -> kiss -> confess -> sleep_together / night_visit."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        self.app = create_application(repo_root)

    def _actor(self):
        return next(actor for actor in self.app.world.characters if actor.key == "enterprise")

    def _set_time(self, slot: TimeSlot) -> None:
        self.app.world.current_time_slot = slot

    def _move_to(self, key: str) -> None:
        self.app.navigation_service.move_player(self.app.world, key)

    def _advance_to_love(self, actor) -> None:
        """Advance actor relationship to love stage."""
        actor.stats.compat.cflag.set(2, 6)
        actor.stats.compat.cflag.set(4, 4)
        actor.affection = 6
        actor.trust = 4
        self.app.relationship_service.update_actor(actor)
        self.assertEqual(actor.relationship_stage.key, "love")

    def test_light_intimacy_kiss_and_confess(self) -> None:
        actor = self._actor()
        self._advance_to_love(actor)

        # 1. 邀请同行
        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("dock")
        actor.location_key = "dock"
        result = self.app.command_service.execute(self.app.world, actor.key, "invite_follow")
        self.assertEqual(result.action_key, "invite_follow")
        self.assertTrue(actor.is_following)

        # 2. 邀请约会
        result = self.app.command_service.execute(self.app.world, actor.key, "invite_date")
        self.assertEqual(result.action_key, "invite_date")
        self.assertTrue(actor.is_on_date)

        # 3. 接吻
        self._set_time(TimeSlot.EVENING)
        self._move_to("main_corridor")
        self._move_to("garden")
        actor.location_key = "garden"
        result = self.app.command_service.execute(self.app.world, actor.key, "kiss")
        self.assertEqual(result.action_key, "kiss")
        self.assertTrue(actor.has_mark("kissed"))

        # 4. 告白
        result = self.app.command_service.execute(self.app.world, actor.key, "confess")
        self.assertEqual(result.action_key, "confess")
        self.assertTrue(actor.has_mark("confessed"))

    def test_sleep_together_line(self) -> None:
        actor = self._actor()
        self._advance_to_love(actor)

        # 同行 + 约会
        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("dock")
        actor.location_key = "dock"
        self.app.command_service.execute(self.app.world, actor.key, "invite_follow")
        self.app.command_service.execute(self.app.world, actor.key, "invite_date")

        # 进入私密地点
        self._move_to("main_corridor")
        self._move_to("dormitory_a")
        actor.location_key = "dormitory_a"

        # 一起入睡
        self._set_time(TimeSlot.NIGHT)
        result = self.app.command_service.execute(self.app.world, actor.key, "sleep_together")
        self.assertEqual(result.action_key, "sleep_together")

    def test_night_visit_line(self) -> None:
        actor = self._actor()
        self._advance_to_love(actor)

        # night_visit 只需 love + private + late_night，但导航到私密地点需要同行/约会
        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("dock")
        actor.location_key = "dock"
        self.app.command_service.execute(self.app.world, actor.key, "invite_follow")
        self.app.command_service.execute(self.app.world, actor.key, "invite_date")

        self._move_to("main_corridor")
        self._move_to("dormitory_a")
        actor.location_key = "dormitory_a"

        self._set_time(TimeSlot.LATE_NIGHT)
        result = self.app.command_service.execute(self.app.world, actor.key, "night_visit")
        self.assertEqual(result.action_key, "night_visit")
        self.assertTrue(actor.has_mark("night_visit"))

    def test_invite_dark_place_and_room_kiss(self) -> None:
        actor = self._actor()
        self._advance_to_love(actor)

        # 同行 + 约会
        self._set_time(TimeSlot.AFTERNOON)
        self._move_to("main_corridor")
        self._move_to("dock")
        actor.location_key = "dock"
        self.app.command_service.execute(self.app.world, actor.key, "invite_follow")
        self.app.command_service.execute(self.app.world, actor.key, "invite_date")

        # 邀请去暗处
        self._set_time(TimeSlot.EVENING)
        self._move_to("main_corridor")
        self._move_to("bathhouse")
        actor.location_key = "bathhouse"
        result = self.app.command_service.execute(self.app.world, actor.key, "invite_dark_place")
        self.assertEqual(result.action_key, "invite_dark_place")

        # 房间内接吻
        self._move_to("main_corridor")
        self._move_to("dormitory_a")
        actor.location_key = "dormitory_a"
        result = self.app.command_service.execute(self.app.world, actor.key, "room_kiss")
        self.assertEqual(result.action_key, "room_kiss")
        self.assertTrue(actor.has_mark("kissed"))


if __name__ == "__main__":
    unittest.main()

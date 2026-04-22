"""Tests for persistent state system — slots, SOURCE generation, clearing."""

import unittest
from pathlib import Path

from eral.app.bootstrap import create_application
from eral.domain.persistent import (
    PersistentStateDefinition,
    SlotDefinition,
    can_activate,
    clear_states_by_event,
    is_slot_available,
    occupied_slot_counts,
    persistent_source,
)
from eral.domain.relationship import RelationshipStage
from eral.domain.world import TimeSlot
from eral.content.persistent import load_persistent_state_definitions, load_slot_definitions


ROOT = Path(__file__).resolve().parent.parent


class SlotOccupancyTests(unittest.TestCase):
    def setUp(self):
        self.slot_defs = {
            "mouth": SlotDefinition(key="mouth", display_name="嘴", capacity=1),
            "hand_l": SlotDefinition(key="hand_l", display_name="左手", capacity=1, blocked_by=("arm",)),
            "hand_r": SlotDefinition(key="hand_r", display_name="右手", capacity=1, blocked_by=("arm",)),
            "arm": SlotDefinition(key="arm", display_name="双臂", capacity=1),
            "lower": SlotDefinition(key="lower", display_name="下半身", capacity=1),
            "equip_clit": SlotDefinition(key="equip_clit", display_name="阴蒂装备", capacity=1),
        }
        self.ps_defs = {
            "holding_hands": PersistentStateDefinition(
                key="holding_hands", display_name="牵手中",
                occupies_slots=("hand_l",),
                source_per_turn={"affection": 30, "joy": 20},
                clear_on=("end_date",),
            ),
            "kissing": PersistentStateDefinition(
                key="kissing", display_name="接吻中",
                occupies_slots=("mouth",),
                source_per_turn={"pleasure_m": 20, "temptation": 30},
                clear_on=("end_date", "end_training"),
            ),
            "hugging": PersistentStateDefinition(
                key="hugging", display_name="拥抱中",
                occupies_slots=("arm",),
                source_per_turn={"affection": 40, "joy": 30},
                clear_on=("end_date",),
            ),
            "inserted_v": PersistentStateDefinition(
                key="inserted_v", display_name="V插入中",
                occupies_slots=("lower",),
                source_per_turn={"pleasure_v": 30},
                clear_on=("end_training",),
            ),
            "inserted_a": PersistentStateDefinition(
                key="inserted_a", display_name="A插入中",
                occupies_slots=("lower",),
                source_per_turn={"pleasure_a": 30},
                clear_on=("end_training",),
            ),
            "clit_clamp": PersistentStateDefinition(
                key="clit_clamp", display_name="阴蒂夹",
                occupies_slots=("equip_clit",),
                source_per_turn={"pleasure_c": 15},
                clear_on=("end_training",),
            ),
            "leaning_shoulder": PersistentStateDefinition(
                key="leaning_shoulder", display_name="靠肩中",
                occupies_slots=(),
                source_per_turn={"affection": 15},
                clear_on=("end_date",),
            ),
        }

    def test_empty_states_no_occupation(self):
        occupied = occupied_slot_counts(set(), self.ps_defs)
        self.assertEqual(occupied, {})

    def test_single_state_occupies_correct_slots(self):
        occupied = occupied_slot_counts({"holding_hands"}, self.ps_defs)
        self.assertEqual(occupied, {"hand_l": 1})

    def test_multiple_states_stacking(self):
        occupied = occupied_slot_counts({"holding_hands", "kissing"}, self.ps_defs)
        self.assertEqual(occupied, {"hand_l": 1, "mouth": 1})

    def test_equipment_uses_own_slots(self):
        occupied = occupied_slot_counts({"clit_clamp"}, self.ps_defs)
        self.assertEqual(occupied, {"equip_clit": 1})
        self.assertNotIn("hand_l", occupied)
        self.assertNotIn("mouth", occupied)

    def test_no_slot_state(self):
        occupied = occupied_slot_counts({"leaning_shoulder"}, self.ps_defs)
        self.assertEqual(occupied, {})

    def test_can_activate_when_empty(self):
        self.assertTrue(can_activate("holding_hands", set(), self.ps_defs, self.slot_defs))

    def test_cannot_activate_conflicting_lower(self):
        self.assertFalse(can_activate(
            "inserted_a", {"inserted_v"}, self.ps_defs, self.slot_defs,
        ))

    def test_can_activate_different_slots(self):
        self.assertTrue(can_activate(
            "holding_hands", {"kissing"}, self.ps_defs, self.slot_defs,
        ))

    def test_arm_blocks_hands(self):
        occupied = occupied_slot_counts({"hugging"}, self.ps_defs)
        self.assertFalse(is_slot_available("hand_l", occupied, self.slot_defs))
        self.assertFalse(is_slot_available("hand_r", occupied, self.slot_defs))

    def test_can_activate_equipment_alongside_body(self):
        self.assertTrue(can_activate(
            "clit_clamp", {"holding_hands", "kissing"}, self.ps_defs, self.slot_defs,
        ))


class PersistentSourceTests(unittest.TestCase):
    def test_single_state_source(self):
        defs = {
            "holding_hands": PersistentStateDefinition(
                key="holding_hands", display_name="牵手中",
                source_per_turn={"affection": 30, "joy": 20},
            ),
        }
        result = persistent_source({"holding_hands"}, defs)
        self.assertEqual(result, {"affection": 30, "joy": 20})

    def test_multiple_states_stack(self):
        defs = {
            "holding_hands": PersistentStateDefinition(
                key="holding_hands", display_name="牵手中",
                source_per_turn={"affection": 30, "joy": 20},
            ),
            "kissing": PersistentStateDefinition(
                key="kissing", display_name="接吻中",
                source_per_turn={"affection": 10, "pleasure_m": 20},
            ),
        }
        result = persistent_source({"holding_hands", "kissing"}, defs)
        self.assertEqual(result["affection"], 40)
        self.assertEqual(result["joy"], 20)
        self.assertEqual(result["pleasure_m"], 20)

    def test_empty_states_no_source(self):
        result = persistent_source(set(), {})
        self.assertEqual(result, {})


class ClearStatesTests(unittest.TestCase):
    def test_clear_on_date_end(self):
        defs = {
            "holding_hands": PersistentStateDefinition(
                key="holding_hands", display_name="牵手中",
                clear_on=("end_date",),
            ),
            "kissing": PersistentStateDefinition(
                key="kissing", display_name="接吻中",
                clear_on=("end_date", "end_training"),
            ),
        }
        result = clear_states_by_event({"holding_hands", "kissing"}, "end_date", defs)
        self.assertEqual(result, set())

    def test_partial_clear(self):
        defs = {
            "holding_hands": PersistentStateDefinition(
                key="holding_hands", display_name="牵手中",
                clear_on=("end_date",),
            ),
            "inserted_v": PersistentStateDefinition(
                key="inserted_v", display_name="V插入中",
                clear_on=("end_training",),
            ),
        }
        result = clear_states_by_event({"holding_hands", "inserted_v"}, "end_training", defs)
        self.assertEqual(result, {"holding_hands"})

    def test_no_matching_clear(self):
        defs = {
            "holding_hands": PersistentStateDefinition(
                key="holding_hands", display_name="牵手中",
                clear_on=("end_date",),
            ),
        }
        result = clear_states_by_event({"holding_hands"}, "end_training", defs)
        self.assertEqual(result, {"holding_hands"})


class DataLoaderTests(unittest.TestCase):
    def test_load_slots(self):
        path = ROOT / "data" / "base" / "persistent_states.toml"
        slots = load_slot_definitions(path)
        keys = {s.key for s in slots}
        self.assertIn("mouth", keys)
        self.assertIn("hand_l", keys)
        self.assertIn("hand_r", keys)
        self.assertIn("arm", keys)
        self.assertIn("lower", keys)
        self.assertIn("equip_clit", keys)
        self.assertIn("equip_nipple", keys)
        hand_l = next(s for s in slots if s.key == "hand_l")
        self.assertIn("arm", hand_l.blocked_by)

    def test_load_persistent_states(self):
        path = ROOT / "data" / "base" / "persistent_states.toml"
        states = load_persistent_state_definitions(path)
        keys = {s.key for s in states}
        self.assertIn("holding_hands", keys)
        self.assertIn("kissing", keys)
        self.assertIn("hugging", keys)
        self.assertIn("inserted_v", keys)
        self.assertIn("inserted_a", keys)
        self.assertIn("clit_clamp", keys)
        self.assertIn("nipple_clamp", keys)
        self.assertIn("vibrator_active", keys)
        self.assertIn("anal_plug_active", keys)

    def test_holding_hands_definition(self):
        path = ROOT / "data" / "base" / "persistent_states.toml"
        states = {s.key: s for s in load_persistent_state_definitions(path)}
        hh = states["holding_hands"]
        self.assertEqual(hh.occupies_slots, ("hand_l",))
        self.assertEqual(hh.source_per_turn["affection"], 30)
        self.assertIn("end_date", hh.clear_on)


class IntegrationPersistentStateTests(unittest.TestCase):
    def setUp(self):
        self.app = create_application(ROOT)

    def test_character_starts_with_no_persistent_states(self):
        for actor in self.app.world.characters:
            self.assertEqual(actor.active_persistent_states, set())

    def _setup_date_actor(self, world, actor_key="enterprise", location="garden"):
        actor = next(a for a in world.characters if a.key == actor_key)
        world.active_location = self.app.port_map.location_by_key(location)
        actor.location_key = location
        actor.is_on_date = True
        world.date_partner_key = actor.key
        world.current_time_slot = TimeSlot.AFTERNOON
        actor.affection = 500
        actor.trust = 300
        actor.stats.compat.cflag.set(2, 500)
        actor.stats.compat.cflag.set(4, 300)
        actor.stats.compat.abl.set(9, 3)
        actor.relationship_stage = RelationshipStage(key="like", display_name="喜欢", rank=2)
        actor.sync_compat_from_runtime()
        return actor

    def _setup_training_actor(self, world, actor_key="enterprise"):
        actor = next(a for a in world.characters if a.key == actor_key)
        world.active_location = self.app.port_map.location_by_key("dormitory_a")
        actor.location_key = "dormitory_a"
        world.training_active = True
        world.training_actor_key = actor.key
        world.training_position_key = "standing"
        world.current_time_slot = TimeSlot.NIGHT
        actor.removed_slots = ("underwear_bottom",)
        return actor

    def test_hold_hands_activates_persistent_state(self):
        world = self.app.world
        actor = self._setup_date_actor(world)

        self.app.command_service.execute(world, actor.key, "hold_hands")
        self.assertIn("holding_hands", actor.active_persistent_states)

    def test_toggle_off_persistent_state(self):
        world = self.app.world
        actor = self._setup_date_actor(world)

        self.app.command_service.execute(world, actor.key, "hold_hands")
        self.assertIn("holding_hands", actor.active_persistent_states)
        world.current_time_slot = TimeSlot.AFTERNOON
        self.app.command_service.execute(world, actor.key, "hold_hands")
        self.assertNotIn("holding_hands", actor.active_persistent_states)

    def test_persistent_source_added_each_turn(self):
        world = self.app.world
        actor = self._setup_date_actor(world)

        self.app.command_service.execute(world, actor.key, "hold_hands")
        self.assertIn("holding_hands", actor.active_persistent_states)

        result = self.app.command_service.execute(world, actor.key, "date_stroll")
        self.assertTrue(result.success)
        self.assertIn("holding_hands", actor.active_persistent_states)

    def test_end_date_clears_date_states(self):
        world = self.app.world
        actor = self._setup_date_actor(world)
        actor.is_following = True

        self.app.command_service.execute(world, actor.key, "hold_hands")
        self.assertIn("holding_hands", actor.active_persistent_states)

        self.app.command_service.execute(world, actor.key, "end_date")
        self.assertNotIn("holding_hands", actor.active_persistent_states)

    def test_insertion_mutual_exclusion(self):
        world = self.app.world
        actor = self._setup_training_actor(world)

        self.app.command_service.execute(world, actor.key, "train_insert_v")
        self.assertIn("inserted_v", actor.active_persistent_states)

        with self.assertRaises(ValueError):
            self.app.command_service.execute(world, actor.key, "train_insert_a")

    def test_oral_blocked_by_kissing(self):
        world = self.app.world
        actor = self._setup_training_actor(world)
        actor.set_condition("abl_9", 1)

        self.app.command_service.execute(world, actor.key, "train_kiss")
        self.assertIn("kissing", actor.active_persistent_states)

        with self.assertRaises(ValueError):
            self.app.command_service.execute(world, actor.key, "train_oral")

    def test_end_training_clears_training_states(self):
        world = self.app.world
        actor = self._setup_training_actor(world)

        self.app.command_service.execute(world, actor.key, "train_insert_v")
        self.assertIn("inserted_v", actor.active_persistent_states)

        self.app.command_service.execute(world, actor.key, "end_training")
        self.assertNotIn("inserted_v", actor.active_persistent_states)

    def test_equipment_no_body_slot_conflict(self):
        world = self.app.world
        actor = self._setup_training_actor(world)
        actor.set_condition("abl_9", 1)

        self.app.command_service.execute(world, actor.key, "train_kiss")
        self.assertIn("kissing", actor.active_persistent_states)

        self.app.command_service.execute(world, actor.key, "use_clit_cap")
        self.assertIn("clit_clamp", actor.active_persistent_states)
        self.assertIn("kissing", actor.active_persistent_states)


class SaveCompatTests(unittest.TestCase):
    def test_old_save_loads_without_persistent_states(self):
        from eral.systems.save import SaveService
        from eral.engine.paths import RuntimePaths
        import json, tempfile

        app = create_application(ROOT)
        actor = app.world.characters[0]
        actor.active_persistent_states = {"holding_hands", "kissing"}

        save = SaveService(
            paths=RuntimePaths.from_root(ROOT),
            stat_axes=app.stat_axes,
        )

        save.save_world(app.world)

        loaded = save.load_world()
        loaded_actor = next(a for a in loaded.characters if a.key == actor.key)
        self.assertEqual(loaded_actor.active_persistent_states, {"holding_hands", "kissing"})

        old_payload = json.loads(save.quicksave_path().read_text(encoding="utf-8"))
        for char in old_payload["characters"]:
            char.pop("active_persistent_states", None)
        save.quicksave_path().write_text(
            json.dumps(old_payload, ensure_ascii=False, indent=2), encoding="utf-8",
        )

        loaded2 = save.load_world()
        loaded2_actor = next(a for a in loaded2.characters if a.key == actor.key)
        self.assertEqual(loaded2_actor.active_persistent_states, set())


class TrainingUndressAndStateTests(unittest.TestCase):
    def setUp(self):
        self.app = create_application(ROOT)

    def _setup_training(self, actor_key="enterprise"):
        world = self.app.world
        actor = next(a for a in world.characters if a.key == actor_key)
        world.active_location = self.app.port_map.location_by_key("dormitory_a")
        actor.location_key = "dormitory_a"
        world.training_active = True
        world.training_actor_key = actor.key
        world.training_position_key = "standing"
        world.current_time_slot = TimeSlot.NIGHT
        return actor

    def test_end_training_clears_removed_slots(self):
        actor = self._setup_training()
        actor.removed_slots = ("underwear_bottom", "top")

        self.app.command_service.execute(self.app.world, actor.key, "end_training")
        self.assertEqual(actor.removed_slots, ())

    def test_position_change_preserves_inserted_v(self):
        actor = self._setup_training()
        actor.removed_slots = ("underwear_bottom",)

        self.app.command_service.execute(self.app.world, actor.key, "train_insert_v")
        self.assertIn("inserted_v", actor.active_persistent_states)

        self.app.command_service.execute(self.app.world, actor.key, "change_position_missionary")
        self.assertIn("inserted_v", actor.active_persistent_states)
        self.assertEqual(self.app.world.training_position_key, "missionary")

    def test_position_change_preserves_inserted_a(self):
        actor = self._setup_training()
        actor.removed_slots = ("underwear_bottom",)
        actor.set_condition("train_c_develop", 10)
        actor.set_condition("train_v_develop", 5)

        self.app.command_service.execute(self.app.world, actor.key, "train_insert_a")
        self.assertIn("inserted_a", actor.active_persistent_states)

        self.app.command_service.execute(self.app.world, actor.key, "change_position_behind")
        self.assertIn("inserted_a", actor.active_persistent_states)
        self.assertEqual(self.app.world.training_position_key, "from_behind")

    def test_undress_does_not_clear_persistent_states(self):
        actor = self._setup_training()
        actor.set_condition("abl_9", 1)

        self.app.command_service.execute(self.app.world, actor.key, "train_kiss")
        self.assertIn("kissing", actor.active_persistent_states)

        self.app.command_service.execute(self.app.world, actor.key, "remove_underwear_bottom")
        self.assertIn("underwear_bottom", actor.removed_slots)
        self.assertIn("kissing", actor.active_persistent_states)

    def test_insert_blocked_without_undress(self):
        actor = self._setup_training()

        with self.assertRaises(ValueError) as ctx:
            self.app.command_service.execute(self.app.world, actor.key, "train_insert_v")
        self.assertIn("服装", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

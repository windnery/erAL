import unittest

from world import World
from game_engine.managers.SaveManager import SaveManager, SAVE_VERSION


class TestSerializeWorld(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.sm = SaveManager(self.world)

    def test_serialize_contains_runtime_fields(self):
        # 修改运行时字段
        self.world.player.money = 777
        self.world.player.base['stamina'] = 1234
        self.world.time_manager.day = 42
        self.world.time_manager.hour = 15
        self.world.time_manager.minute = 30
        self.world.work_manager.works = 500
        self.world.work_manager.works_done = 300
        self.world.menu_active = False
        laffey = self.world.npc_manager.shipgirls['laffey']
        laffey.favor = 999
        self.world.npc_manager.set_secretary_ship_proc('laffey', self.world.player)

        data = self.sm.serialize_world()

        self.assertEqual(data['version'], SAVE_VERSION)
        d = data['data']
        self.assertEqual(d['player']['money'], 777)
        self.assertEqual(d['player']['base']['stamina'], 1234)
        self.assertEqual(d['time'], {'day': 42, 'hour': 15, 'minute': 30})
        self.assertEqual(d['work'], {'works': 500, 'works_done': 300})
        self.assertFalse(d['menu_active'])
        self.assertEqual(d['secretary_ship_id'], 'laffey')
        self.assertEqual(d['shipgirls']['laffey']['favor'], 999)
        self.assertTrue(d['shipgirls']['laffey']['cflag']['secretary_ship'])

    def test_serialize_does_not_store_static_data(self):
        data = self.sm.serialize_world()
        sg = data['data']['shipgirls']['laffey']
        self.assertNotIn('lines', sg)
        self.assertNotIn('schedule', sg)
        self.assertNotIn('talent', sg)


class TestDeserializeWorld(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.sm = SaveManager(self.world)

    def _mutate_world(self, world):
        world.player.money = 555
        world.player.location = {'region': 'office', 'node': 'desk'}
        world.player.wake_time = {'hour': 8, 'minute': 0}
        world.player.base['energy'] = 888
        world.player.abl['talk_abl'] = 4
        world.time_manager.day = 10
        world.time_manager.hour = 20
        world.time_manager.minute = 5
        world.work_manager.works = 111
        world.work_manager.works_done = 99
        world.menu_active = False
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.favor = 2345
        laffey.trust = 678
        laffey.location = {'region': 'home', 'node': 'bedroom'}
        laffey.cflag['sleeping'] = True
        world.npc_manager.set_secretary_ship_proc('Z23', world.player)

    def test_roundtrip_restores_state(self):
        self._mutate_world(self.world)
        data = self.sm.serialize_world()

        new_world = World()
        err = SaveManager(new_world).deserialize_world(data)

        self.assertIsNone(err)
        p = new_world.player
        self.assertEqual(p.money, 555)
        self.assertEqual(p.location, {'region': 'office', 'node': 'desk'})
        self.assertEqual(p.wake_time, {'hour': 8, 'minute': 0})
        self.assertEqual(p.base['energy'], 888)
        self.assertEqual(p.abl['talk_abl'], 4)
        self.assertEqual(new_world.time_manager.day, 10)
        self.assertEqual(new_world.time_manager.hour, 20)
        self.assertEqual(new_world.time_manager.minute, 5)
        self.assertEqual(new_world.work_manager.works, 111)
        self.assertEqual(new_world.work_manager.works_done, 99)
        self.assertFalse(new_world.menu_active)
        laffey = new_world.npc_manager.shipgirls['laffey']
        self.assertEqual(laffey.favor, 2345)
        self.assertEqual(laffey.trust, 678)
        self.assertEqual(laffey.cflag['sleeping'], True)
        self.assertEqual(laffey.palam_lv['c_pleasure_palam'], 0)  # 派生值被重算
        self.assertEqual(new_world.npc_manager.secretary_ship.id, 'Z23')

    def test_deserialize_corrupt_data_returns_error(self):
        err = self.sm.deserialize_world({'data': {'time': {}}})
        self.assertIsNotNone(err)


import json
import tempfile
from pathlib import Path


class TestSlots(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.world = World()
        self.sm = SaveManager(self.world, sav_dir=Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_then_load_roundtrip(self):
        self.world.player.money = 4321
        self.world.time_manager.day = 7
        meta = self.sm.save_game(1)
        self.assertEqual(meta['day'], 7)
        self.assertTrue((Path(self.tmp.name) / 'slot_1.json').exists())

        new_world = World()
        err = SaveManager(new_world, sav_dir=Path(self.tmp.name)).load_game(1)
        self.assertIsNone(err)
        self.assertEqual(new_world.player.money, 4321)
        self.assertEqual(new_world.time_manager.day, 7)

    def test_get_save_list_marks_empty_slots(self):
        self.sm.save_game(2)
        slots = self.sm.get_save_list()
        self.assertEqual(len(slots), 3)
        self.assertFalse(slots[0]['has_save'])
        self.assertTrue(slots[1]['has_save'])
        self.assertEqual(slots[1]['slot'], 2)
        self.assertFalse(slots[2]['has_save'])

    def test_load_missing_slot_returns_error(self):
        err = self.sm.load_game(3)
        self.assertEqual(err, '该槽位没有存档')

    def test_load_corrupt_file_returns_error(self):
        (Path(self.tmp.name) / 'slot_1.json').write_text('{broken', encoding='utf-8')
        err = self.sm.load_game(1)
        self.assertIsNotNone(err)


if __name__ == '__main__':
    unittest.main()

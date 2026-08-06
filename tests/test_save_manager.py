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


if __name__ == '__main__':
    unittest.main()

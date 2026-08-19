
class TestTrainClosedLoop:
    @staticmethod
    def _make_train(world, actors, targets):
        from game_engine.managers.TrainManager import Train
        world.train_manager.train = Train(world.player.location, world.player)
        world.train_manager.train.actors = list(actors)
        world.train_manager.train.targets = list(targets)

    @staticmethod
    def _make_position_train(world):
        TestTrainClosedLoop._make_train(world, ['player'], ['laffey'])
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.abl.update({'desire_abl': 10, 'v_sen_abl': 10, 'servant_abl': 10})

    def test_vitality_clamp(self, world):
        world.player.set_vitality(9999)
        assert world.player.get_vitality() == world.player.base['max_vitality']
        world.player.set_vitality(-10)
        assert world.player.get_vitality() == 0

    def test_sleep_recovers_vitality(self, world):
        world.player.set_vitality(0)
        world.settle_day(sleep=True)
        assert world.player.get_vitality() > 0

    def test_ejaculation_check_threshold(self, world):
        from game_engine.data_pipeline.palam.ejaculation_calc import ejaculation_check
        world.player.palam['m_pleasure_palam'] = 4999
        assert ejaculation_check(world.player) is False
        world.player.palam['m_pleasure_palam'] = 5000
        assert ejaculation_check(world.player) is True

    def test_v_insert_in_train_commands(self, world):
        self._make_train(world, ['player', 'Z23'], ['laffey'])
        cmd = next(c for c in world.train_manager.get_train_commands() if c['key'] == 'common_position')
        assert cmd['name'] == '正常位'
        assert cmd['cat'] == '性交'

    def test_v_insert_not_in_act_commands(self, world):
        assert 'common_position' not in [c['key'] for c in world.command_manager.get_Act_COM()]

    def test_v_insert_breaks_both_virgins(self, world):
        self._make_position_train(world)
        world.command_manager.do_cmd('common_position')
        assert world.player.get_talent_value('male_virgin') == 0
        assert world.npc_manager.shipgirls['laffey'].get_talent_value('virgin') == 0

    def test_ejaculation_consumes_vitality_and_adds_semen_exp(self, world):
        self._make_position_train(world)
        world.player.palam['m_pleasure_palam'] = 5000
        laffey = world.npc_manager.shipgirls['laffey']
        world.command_manager.do_cmd('common_position')
        assert world.player.get_exp('ejaculation_exp') == 1
        from config.palam_config import EJACULATION_VITALITY_COST
        assert world.player.get_vitality() == world.player.base['max_vitality'] - EJACULATION_VITALITY_COST
        assert laffey.get_exp('v_semen_exp') == 1
        assert world.player.palam['m_pleasure_palam'] == 0

    def test_vitality_zero_forces_end_train(self, world):
        self._make_position_train(world)
        world.player.palam['m_pleasure_palam'] = 5000
        from config.palam_config import EJACULATION_VITALITY_COST
        world.player.set_vitality(EJACULATION_VITALITY_COST)
        world.command_manager.do_cmd('common_position')
        assert world.train_manager.train is None
        assert world.train_mode is False
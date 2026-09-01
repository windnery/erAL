
class TestTrainClosedLoop:
    @staticmethod
    def _make_train(world, actors, targets):
        from game_engine.managers.TrainManager import Train
        world.train_manager.train = Train(world.player.location, world.player)
        world.train_manager.train.actors = list(actors)
        world.train_manager.train.targets = list(targets)
        world.train_mode = True

    @staticmethod
    def _make_position_train(world):
        TestTrainClosedLoop._make_train(world, ['player'], ['laffey'])
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.abl.update({'desire_abl': 10, 'v_sen_abl': 10, 'servant_abl': 10})
        laffey.palam_lv['lubrication_palam'] = 3
        world.train_manager.train.initiative = {'player': 100, 'laffey': 50}

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
        self._make_train(world, ['player'], ['laffey'])
        cmd = next(c for c in world.train_manager.get_train_commands() if c['key'] == 'common_position')
        assert cmd['name'] == '正常位'
        assert cmd['cat'] == '性交'

    def test_v_insert_not_in_act_commands(self, world):
        assert 'common_position' not in [c['key'] for c in world.command_manager.get_act_com()]

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
        world.player.set_vitality(1)
        world.player.palam['m_pleasure_palam'] = 5000
        world.command_manager.do_cmd('common_position')
        assert world.player.get_vitality() == 0
        assert world.train_manager.train is None
        assert 'common_position' not in [c['key'] for c in world.command_manager.get_act_com()]

    def test_unconscious_on_energy_zero(self, world):
        self._make_position_train(world)
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.set_energy(10)
        world.command_manager.do_cmd('common_position')
        assert laffey.get_energy() == 0
        assert laffey.cflag.get('unconscious') is True
        assert world.train_manager.train.initiative['laffey'] == 0

    def test_initiative_display_in_palam_status(self, world):
        self._make_position_train(world)
        result = world.command_manager.do_cmd('common_position')
        assert isinstance(result, list)
        found = any('主导权' in line for line in result)
        assert found, "调教结算中应包含主导权变动消息"


class TestSourceProcBatch:
    """测试 source_proc_batch 的通用多角色结算能力"""

    def _run(self, world, pairs):
        from game_engine.commands._common import source_proc_batch
        from game_engine.commands._context import CommandContext
        ctx = CommandContext(world)
        source_proc_batch(pairs, ctx)
        return ctx

    def _lines(self, ctx, chara_name: str) -> list[str]:
        palam_lines = ctx.blocks.get('palam', [])
        return [l for l in palam_lines if l.startswith(chara_name)]

    def test_multi_actor_single_target_merges_output(self, world):
        """2调教者×1被调教者：target 的 palam 变化只输出一次，数值累计"""
        from game_engine.commands._common import new_source
        laffey = world.npc_manager.shipgirls['laffey']
        z23 = world.npc_manager.shipgirls['Z23']
        laffey.palam['c_pleasure_palam'] = 0
        laffey.palam['b_pleasure_palam'] = 0
        src = new_source({'c_pleasure_source': 100, 'b_pleasure_source': 100})
        ctx = self._run(world, [
            (src.copy(), world.player, laffey),
            (src.copy(), z23, laffey),
        ])
        laffey_lines = self._lines(ctx, laffey.name)
        assert len(laffey_lines) == 1, f'拉菲消息行数={len(laffey_lines)}，应为1（合并）'
        # 数值应累计两次 100
        assert laffey.palam['c_pleasure_palam'] > 100, f'c_pleasure 应累计 2 次，实际 {laffey.palam["c_pleasure_palam"]}'

    def test_forward_and_feedback_same_chara_merged(self, world):
        """正向+反馈：同一角色（拉菲）只输出一次"""
        from game_engine.commands._common import new_source
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.palam['c_pleasure_palam'] = 0
        src_forward = new_source({'c_pleasure_source': 50})
        src_feedback = new_source({'m_pleasure_source': 30})
        ctx = self._run(world, [
            (src_forward.copy(), world.player, laffey),
            (src_feedback.copy(), laffey, world.player),
        ])
        laffey_lines = self._lines(ctx, laffey.name)
        player_lines = self._lines(ctx, world.player.name)
        assert len(laffey_lines) == 1, f'拉菲消息行数={len(laffey_lines)}，应为1'
        assert len(player_lines) == 1, f'指挥官消息行数={len(player_lines)}，应为1'

    def test_kiss_scene_all_chara_once(self, world):
        """kiss 场景（2调教者×1被调教者+反馈）：每个角色只输出一次"""
        from game_engine.commands._common import new_source
        laffey = world.npc_manager.shipgirls['laffey']
        z23 = world.npc_manager.shipgirls['Z23']
        laffey.palam['c_pleasure_palam'] = 0
        laffey.palam['m_pleasure_palam'] = 0
        world.player.palam['m_pleasure_palam'] = 0
        z23.palam['m_pleasure_palam'] = 0
        src = new_source({'m_pleasure_source': 50, 'c_pleasure_source': 40})
        pairs = []
        for actor in (world.player, z23):
            pairs.append((src.copy(), actor, laffey))
            pairs.append((new_source({'m_pleasure_source': 30}), laffey, actor))
        ctx = self._run(world, pairs)
        for name in (world.player.name, z23.name, laffey.name):
            lines = self._lines(ctx, name)
            assert len(lines) == 1, f'{name}消息行数={len(lines)}，应为1'
        # 拉菲的 m_pleasure 应累计 2 次正向（单对时先测基线再对比）
        laffey.palam['m_pleasure_palam'] = 0
        src_single = new_source({'m_pleasure_source': 50, 'c_pleasure_source': 40})
        self._run(world, [(src_single, world.player, laffey)])
        single_val = laffey.palam['m_pleasure_palam']
        assert single_val > 0, '单对基线应为正'
        # 两对时累计（重跑两对，从 0 开始）
        laffey.palam['m_pleasure_palam'] = 0
        src2 = new_source({'m_pleasure_source': 50, 'c_pleasure_source': 40})
        pairs2 = []
        for actor in (world.player, z23):
            pairs2.append((src2.copy(), actor, laffey))
            pairs2.append((new_source({'m_pleasure_source': 30}), laffey, actor))
        self._run(world, pairs2)
        assert laffey.palam['m_pleasure_palam'] > single_val, \
            f'两对累计 {laffey.palam["m_pleasure_palam"]} 应大于单对 {single_val}'

    def test_orgasm_and_emotion_once_per_target(self, world):
        """绝顶/情绪理性：每个 target 只执行一次（去重）"""
        from game_engine.commands._common import new_source
        laffey = world.npc_manager.shipgirls['laffey']
        z23 = world.npc_manager.shipgirls['Z23']
        laffey.palam['c_pleasure_palam'] = 0
        # 情绪基线
        laffey.set_emotion(0)
        src = new_source({'c_pleasure_source': 1000})
        ctx = self._run(world, [
            (src.copy(), world.player, laffey),
            (src.copy(), z23, laffey),
        ])
        # 情绪/理性是静默修改，只验证不崩 + palam 正确累计
        assert laffey.palam['c_pleasure_palam'] > 0
        assert len(ctx.messages) > 0


class TestEjaculationAndOrgasmFormat:
    """验证绝顶粉色、射精苍白色、射精口上与结果按序展示"""

    def test_orgasm_message_colored_pink(self, world):
        from game_engine.data_pipeline.palam.orgasm_calc import orgasm_check
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.palam['v_pleasure_palam'] = 20000
        mes = orgasm_check(laffey)
        assert len(mes) > 0
        # 绝顶消息统一为粉色；快乐刻印获取消息为金色（与其他刻印一致）
        for m in mes:
            assert m.endswith('[[/c]]')
            assert m.startswith('[[c:#ff6fae]]') or m.startswith('[[c:#ffd400]]')

    def test_ejaculation_order_and_colors(self, world):
        TestTrainClosedLoop._make_position_train(world)
        laffey = world.npc_manager.shipgirls['laffey']
        laffey.favor = 1000
        laffey.set_talent('virgin', '0')
        laffey.exp['v_exp'] = 100
        laffey.palam['v_pleasure_palam'] = 14500
        world.player.palam['m_pleasure_palam'] = 5000

        result = world.command_manager.do_cmd('common_position')
        assert isinstance(result, list)

        # 顺序应为：基础palam -> 射精消息 -> 绝顶消息 -> 时间消息
        ejac_idx = -1
        time_idx = -1
        palam_idx = -1
        orgasm_idx = -1
        for i, line in enumerate(result):
            if '射精了' in line:
                ejac_idx = i
                assert '[[c:#f5f5f5]]' in line
            if '度过了' in line:
                time_idx = i
            if '快V' in line or '欲情' in line:
                if palam_idx == -1:
                    palam_idx = i
            if '绝顶！' in line:
                orgasm_idx = i
                assert '[[c:#ff6fae]]' in line

        assert ejac_idx != -1, "应包含射精消息"
        assert orgasm_idx != -1, "应包含绝顶消息"
        assert palam_idx < ejac_idx < orgasm_idx < time_idx, "顺序应为: 基础palam < 射精消息 < 绝顶消息 < 时间消息"

    def test_reverse_train_player_high_palam_no_orgasm_crash(self, world):
        """反向调教（舰娘为调教方，玩家为被调教方）：玩家快感达到阈值触发身体射精，不触发绝顶处理且不崩溃"""
        saratoga = world.npc_manager.shipgirls.get('saratoga') or world.npc_manager.shipgirls['laffey']
        TestTrainClosedLoop._make_train(world, [saratoga.id], ['player'])
        world.train_manager.train.initiative = {saratoga.id: 100, 'player': 50}

        # 玩家快感极高（超过射精阈值 5000 及绝顶阈值 10000）
        world.player.palam['c_pleasure_palam'] = 20000
        world.player.palam['m_pleasure_palam'] = 20000

        result = world.command_manager.do_cmd('caress')
        assert isinstance(result, list)
        # 确保玩家触发了通用身体射精
        assert any('射精了！（身体）' in line for line in result)
        # 确保玩家未触发绝顶消息（只有女性舰娘有绝顶）
        assert not any('绝顶！' in line for line in result)
        # 确保射精后快感被清空
        assert world.player.palam['c_pleasure_palam'] == 0
        assert world.player.palam['m_pleasure_palam'] == 0

    def test_orgasm_check_safely_ignores_player(self, world):
        """直接对 Player 对象调用 orgasm_check / orgasm_check_parts 应安全返回空"""
        from game_engine.data_pipeline.palam.orgasm_calc import orgasm_check, orgasm_check_parts
        world.player.palam['c_pleasure_palam'] = 20000
        world.player.palam['m_pleasure_palam'] = 20000

        mes, org_lv, org_num = orgasm_check_parts(world.player)
        assert mes == []
        assert org_lv == {}
        assert org_num == 0

        mes_compat = orgasm_check(world.player)
        assert mes_compat == []
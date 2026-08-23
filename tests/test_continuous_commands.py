from data.time.time_data import command_time_data


def elapsed_minutes(world) -> int:
    time = world.time_manager
    return time.day * 1440 + time.hour * 60 + time.minute


def test_caress_becomes_active_when_continuous_command_starts(world):
    # Given: an active training session with one actor and one target.
    world.train_manager.new_train(['player', 'Z23'], {'player': 100, 'Z23': 0})

    # When: the continuous caress command is selected.
    result = world.command_manager.do_cmd('caress')

    # Then: it executes once and remains active for later turns.
    assert isinstance(result, list)
    assert world.train_manager.train is not None
    assert world.train_manager.train.continuous_commands == ['caress']
    caress = next(cmd for cmd in world.train_manager.get_train_commands() if cmd['key'] == 'caress')
    assert caress['continuous'] is True
    assert caress['active'] is True


def test_active_continuous_command_stops_without_advancing_time(world):
    # Given: caress is already running continuously.
    world.train_manager.new_train(['player', 'Z23'], {'player': 100, 'Z23': 0})
    world.command_manager.do_cmd('caress')
    before = elapsed_minutes(world)

    # When: the active continuous command is selected again.
    result = world.command_manager.do_cmd('caress')

    # Then: it stops immediately without applying another turn.
    assert isinstance(result, list)
    assert elapsed_minutes(world) == before
    assert world.train_manager.train is not None
    assert world.train_manager.train.continuous_commands == []


def test_active_continuous_command_repeats_after_other_train_command(world):
    # Given: caress is active and the current time is captured after its first turn.
    world.train_manager.new_train(['player', 'Z23'], {'player': 100, 'Z23': 0})
    world.command_manager.do_cmd('caress')
    before = elapsed_minutes(world)

    # When: another training command is executed.
    result = world.command_manager.do_cmd('breast_caress')

    # Then: both the selected command and active caress consume their configured time.
    assert isinstance(result, list)
    assert elapsed_minutes(world) - before == (
        command_time_data['breast_caress'] + command_time_data['caress']
    )
    assert world.train_manager.train is not None
    assert world.train_manager.train.continuous_commands == ['caress']


def test_active_continuous_command_roundtrips_through_save(world, tmp_path):
    # Given: a saved training session with one active continuous command.
    world.train_manager.new_train(['player', 'Z23'], {'player': 100, 'Z23': 0})
    world.command_manager.do_cmd('caress')
    world.save_manager.sav_dir = tmp_path
    world.save_manager.save_game(1)

    # When: a fresh world loads that slot.
    from world import World

    restored = World()
    restored.save_manager.sav_dir = tmp_path
    error = restored.save_manager.load_game(1)

    # Then: the continuous command is still active in the restored session.
    assert error is None
    assert restored.train_manager.train is not None
    assert restored.train_manager.train.continuous_commands == ['caress']

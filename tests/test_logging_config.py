import json

from game_engine.logging_config import configure_logging, shutdown_logging


class SimulatedDiskError(RuntimeError):
    pass


def read_events(log_path):
    return [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines()]


def test_json_log_preserves_event_name_and_fields(tmp_path):
    # Given: a logger configured to write into an isolated directory.
    logger = configure_logging(tmp_path)

    # When: a stable event with structured fields is emitted.
    logger.info('save.completed', extra={'slot': 2, 'day': 5})
    shutdown_logging()

    # Then: the JSON line exposes machine-readable event data.
    payload = json.loads((tmp_path / 'eral.log').read_text(encoding='utf-8'))
    assert payload['event'] == 'save.completed'
    assert payload['level'] == 'INFO'
    assert payload['fields'] == {'day': 5, 'slot': 2}


def test_json_log_preserves_exception_details(tmp_path):
    # Given: a configured logger at an exception-handling boundary.
    logger = configure_logging(tmp_path)

    # When: the boundary records a real exception.
    try:
        raise SimulatedDiskError('disk unavailable')
    except SimulatedDiskError:
        logger.exception('save.failed', extra={'slot': 1})
    shutdown_logging()

    # Then: type, message, and traceback survive JSON serialization.
    payload = json.loads((tmp_path / 'eral.log').read_text(encoding='utf-8'))
    assert payload['exception']['type'] == 'SimulatedDiskError'
    assert payload['exception']['message'] == 'disk unavailable'
    assert 'SimulatedDiskError: disk unavailable' in payload['exception']['traceback']


def test_command_execution_emits_state_transition_event(world, tmp_path):
    # Given: runtime logging and a menu command that can execute.
    configure_logging(tmp_path)

    # When: the command manager executes the command.
    world.command_manager.do_cmd('open_your_eyes')
    shutdown_logging()

    # Then: the command transition is reconstructable from structured fields.
    events = read_events(tmp_path / 'eral.log')
    event = next(item for item in events if item['event'] == 'command.executed')
    assert event['fields']['command'] == 'open_your_eyes'
    assert event['fields']['category'] == '菜单'


def test_save_success_emits_slot_and_version_event(world, tmp_path):
    # Given: runtime logging and an isolated save directory.
    configure_logging(tmp_path / 'logs')
    world.save_manager.sav_dir = tmp_path / 'saves'

    # When: the world is saved successfully.
    world.save_manager.save_game(2)
    shutdown_logging()

    # Then: the persisted transition identifies its slot and schema version.
    events = read_events(tmp_path / 'logs' / 'eral.log')
    event = next(item for item in events if item['event'] == 'save.completed')
    assert event['fields']['slot'] == 2
    assert event['fields']['version'] == 3


def test_load_success_emits_slot_and_version_event(world, tmp_path):
    # Given: an existing slot and logging enabled only for the load boundary.
    world.save_manager.sav_dir = tmp_path / 'saves'
    world.save_manager.save_game(3)
    configure_logging(tmp_path / 'logs')

    # When: the slot is loaded successfully.
    error = world.save_manager.load_game(3)
    shutdown_logging()

    # Then: one load transition records the restored schema version.
    assert error is None
    events = read_events(tmp_path / 'logs' / 'eral.log')
    event = next(item for item in events if item['event'] == 'save.loaded')
    assert event['fields']['slot'] == 3
    assert event['fields']['version'] == 3

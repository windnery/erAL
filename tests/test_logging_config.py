import json
import logging

import pytest

from api import Api
from game_engine.logging_config import (
    LOG_FILE_NAME,
    configure_logging,
    report_crash,
    report_frontend_error,
    shutdown_logging,
)


def read_events(log_path):
    return [
        json.loads(line)
        for line in log_path.read_text(encoding='utf-8').splitlines()
    ]


def test_normal_runtime_events_are_not_persisted(tmp_path):
    logger = configure_logging(tmp_path)
    logger.info('application.started')
    logging.getLogger('eral.command').info(
        'command.executed',
        extra={'command': 'open_your_eyes'},
    )
    shutdown_logging()

    assert not (tmp_path / LOG_FILE_NAME).exists()


def test_crash_report_preserves_exception_details(tmp_path):
    configure_logging(tmp_path)

    try:
        raise RuntimeError('backend boom')
    except RuntimeError as error:
        assert report_crash(error, source='test')

    shutdown_logging()

    payload = read_events(tmp_path / LOG_FILE_NAME)[0]
    assert payload['event'] == 'game.crashed'
    assert payload['level'] == 'CRITICAL'
    assert payload['fields']['source'] == 'test'
    assert payload['exception']['type'] == 'RuntimeError'
    assert payload['exception']['message'] == 'backend boom'
    assert 'RuntimeError: backend boom' in payload['exception']['traceback']
    assert 'python' in payload['runtime']


def test_api_boundary_reports_backend_crash(tmp_path):
    class BrokenManager:
        def explode(self):
            raise LookupError('bad game state')

    configure_logging(tmp_path)
    api = Api.__new__(Api)
    api.managers = {'broken': BrokenManager()}

    with pytest.raises(LookupError, match='bad game state'):
        api.call('broken', 'explode')
    shutdown_logging()

    payload = read_events(tmp_path / LOG_FILE_NAME)[0]
    assert payload['fields']['source'] == 'api.call'
    assert payload['fields']['context']['api_manager'] == 'broken'
    assert payload['fields']['context']['api_function'] == 'explode'


def test_frontend_crash_report_includes_javascript_context(tmp_path):
    configure_logging(tmp_path)

    assert report_frontend_error(
        'Cannot read properties of undefined',
        source='main.js',
        line=42,
        column=7,
        stack='TypeError: Cannot read properties of undefined',
    )
    shutdown_logging()

    payload = read_events(tmp_path / LOG_FILE_NAME)[0]
    assert payload['fields']['source'] == 'frontend'
    assert payload['fields']['context']['client_source'] == 'main.js'
    assert payload['fields']['context']['line'] == 42
    assert payload['fields']['context']['javascript_stack'].startswith('TypeError:')
    assert payload['exception']['type'] == 'FrontendError'


def test_get_app_root_supports_frozen_environment(monkeypatch, tmp_path):
    from game_engine.logging_config import get_app_root
    import sys

    # 非打包模式：返回项目根目录
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert get_app_root().exists()

    # 打包模式（模拟 sys.frozen 为 True）
    fake_exe = tmp_path / 'dist' / 'erAL.exe'
    fake_exe.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(fake_exe))
    assert get_app_root() == tmp_path / 'dist'


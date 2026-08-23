import webview
from pathlib import Path

from api import Api
from game_engine.logging_config import configure_logging


FRONTEND_DIR = Path(__file__).parent / 'frontend'

logger = configure_logging()
logger.info('application.started')
api = Api()
webview.create_window('erAL', str(FRONTEND_DIR / 'index.html'), width=1024, height=860, js_api=api)
webview.start(debug=True)

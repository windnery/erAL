import webview
from pathlib import Path

from api import Api


FRONTEND_DIR = Path(__file__).parent / 'frontend'

api = Api()
webview.create_window('erAL', str(FRONTEND_DIR / 'index.html'), width=1024, height=768, js_api=api)
webview.start()
import webview

from api import Api


api = Api()
webview.create_window('erAL', 'frontend/index.html', width=1024, height=768, js_api=api)
webview.start()
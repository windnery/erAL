from pathlib import Path

from game_engine.logging_config import configure_logging


FRONTEND_DIR = Path(__file__).parent / 'frontend'


def main():
    # 收集崩溃日志
    configure_logging()

    import webview
    from api import Api

    api = Api()
    webview.create_window(
        'erAL',
        str(FRONTEND_DIR / 'index.html'),
        width=1600,
        height=900,
        js_api=api,
    )
    webview.start(debug=True)


if __name__ == '__main__':
    main()

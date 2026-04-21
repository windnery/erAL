"""Package entry point."""

from pathlib import Path

from .app.bootstrap import create_application
from .app.config import AppConfig
from .ui.cli import run_cli


def main() -> None:
    app = create_application()
    config = AppConfig.load(Path("config.ini"))
    if config.ui_mode == "web":
        from .ui.web_server import run_web_server

        run_web_server(app)
    else:
        run_cli(app)


if __name__ == "__main__":
    main()


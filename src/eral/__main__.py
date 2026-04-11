"""Package entry point."""

from .app.bootstrap import create_application
from .ui.cli import run_cli


def main() -> None:
    app = create_application()
    run_cli(app)


if __name__ == "__main__":
    main()


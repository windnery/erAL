"""Configuration loading for the erAL application."""

from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """User-editable runtime configuration."""

    game_title: str = "erAL"
    language: str = "zh_CN"
    ui_mode: str = "cli"
    start_time_slot: str = "morning"
    player_name: str = "Commander"

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        parser = ConfigParser()
        parser.read(path, encoding="utf-8")

        if not parser.sections():
            return cls()

        general = parser["general"] if parser.has_section("general") else {}
        player = parser["player"] if parser.has_section("player") else {}

        return cls(
            game_title=general.get("game_title", cls.game_title),
            language=general.get("language", cls.language),
            ui_mode=general.get("ui_mode", cls.ui_mode),
            start_time_slot=general.get("start_time_slot", cls.start_time_slot),
            player_name=player.get("name", cls.player_name),
        )


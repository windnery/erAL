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
    start_time_slot: str = "morning"
    player_name: str = "指挥官"
    player_gender: str = "male"

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
            start_time_slot=general.get("start_time_slot", cls.start_time_slot),
            player_name=player.get("name", cls.player_name),
            player_gender=player.get("gender", cls.player_gender),
        )

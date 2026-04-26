"""Tests for command and effect schema loaders/validators."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eral.content.commands import load_command_definitions
from eral.tools.validate_content import validate_command_effects, validate_commands


class CommandSchemaTests(unittest.TestCase):
    def test_load_command_definitions_reads_train_only_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "train.toml"
            path.write_text(
                "\n".join(
                    (
                        "[[train]]",
                        "index = 400",
                        'label = "移动"',
                        'category = "movement"',
                        'operation = "move"',
                        'target_mode = "world"',
                        "elapsed_minutes = 15",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            commands = load_command_definitions(path)

        self.assertEqual(len(commands), 1)
        command = commands[0]
        self.assertEqual(command.index, 400)
        self.assertEqual(command.display_name, "移动")
        self.assertEqual(command.category, "movement")
        self.assertEqual(command.operation, "move")
        self.assertEqual(command.target_mode, "world")
        self.assertEqual(command.elapsed_minutes, 15)

    def test_validate_commands_rejects_unknown_train_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commands_dir = root / "data" / "base" / "commands"
            commands_dir.mkdir(parents=True, exist_ok=True)
            (commands_dir / "train.toml").write_text(
                "\n".join(
                    (
                        "[[train]]",
                        "index = 1",
                        'label = "爱抚"',
                        'mystery = "x"',
                        "",
                    )
                ),
                encoding="utf-8",
            )

            errors = validate_commands(root)

        self.assertTrue(any("unknown fields: mystery" in error for error in errors))

    def test_validate_command_effects_rejects_unknown_indices(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commands_dir = root / "data" / "base" / "commands"
            effects_dir = root / "data" / "base" / "effects"
            commands_dir.mkdir(parents=True, exist_ok=True)
            effects_dir.mkdir(parents=True, exist_ok=True)
            (commands_dir / "train.toml").write_text(
                "\n".join(
                    (
                        "[[train]]",
                        "index = 1",
                        'label = "爱抚"',
                        "",
                    )
                ),
                encoding="utf-8",
            )
            (effects_dir / "command_effects.toml").write_text(
                "\n".join(
                    (
                        "[[effect]]",
                        "command_index = 2",
                        "source.target = { 0 = 40 }",
                        "",
                    )
                ),
                encoding="utf-8",
            )

            errors = validate_command_effects(root)

        self.assertTrue(any("unknown command_index '2'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

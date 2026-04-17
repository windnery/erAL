"""Tests for the starter port map."""

from __future__ import annotations

import unittest
from pathlib import Path

from eral.content.port_map import load_port_map


class PortMapTests(unittest.TestCase):
    def test_starter_map_loads_with_expected_connections(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        port_map = load_port_map(repo_root / "data" / "base" / "port_map.toml")

        self.assertEqual(port_map.key, "starter_port")
        self.assertEqual(port_map.starting_location().key, "command_office")
        self.assertIn("main_corridor", port_map.neighbors_of("command_office"))
        self.assertIn("dock", port_map.neighbors_of("main_corridor"))

    def test_starter_map_has_expanded_location_count_and_tags(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        port_map = load_port_map(repo_root / "data" / "base" / "port_map.toml")

        self.assertGreaterEqual(len(port_map.locations), 8)
        self.assertLessEqual(len(port_map.locations), 30)

        library = port_map.location_by_key("library")
        infirmary = port_map.location_by_key("infirmary")
        garden = port_map.location_by_key("garden")

        self.assertIn("study", library.tags)
        self.assertIn("medical", infirmary.tags)
        self.assertIn("social", garden.tags)

    def test_new_locations_are_connected_from_main_corridor(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        port_map = load_port_map(repo_root / "data" / "base" / "port_map.toml")
        neighbors = port_map.neighbors_of("main_corridor")

        self.assertIn("library", neighbors)
        self.assertIn("infirmary", neighbors)
        self.assertIn("garden", neighbors)

    def test_port_map_loads_area_and_sub_area_metadata(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        port_map = load_port_map(repo_root / "data" / "base" / "port_map.toml")

        self.assertIn("command_core", port_map.area_keys())
        self.assertIn("eagle_living", port_map.area_keys())
        self.assertEqual(port_map.sub_area_by_key("hq_command").area_key, "command_core")

    def test_port_map_location_exposes_layered_parent_keys(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        port_map = load_port_map(repo_root / "data" / "base" / "port_map.toml")
        command_office = port_map.location_by_key("command_office")

        self.assertEqual(command_office.area_key, "command_core")
        self.assertEqual(command_office.sub_area_key, "hq_command")


if __name__ == "__main__":
    unittest.main()

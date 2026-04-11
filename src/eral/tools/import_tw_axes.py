"""Import eraTW CSV axis definitions into JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eral.content.stat_axes import AxisFamily


FAMILY_FILES: tuple[tuple[AxisFamily, str], ...] = (
    (AxisFamily.BASE, "Base.csv"),
    (AxisFamily.PALAM, "Palam.csv"),
    (AxisFamily.SOURCE, "source.csv"),
    (AxisFamily.ABL, "Abl.csv"),
    (AxisFamily.TALENT, "Talent.csv"),
    (AxisFamily.FLAG, "FLAG.csv"),
    (AxisFamily.CFLAG, "CFLAG.csv"),
    (AxisFamily.TFLAG, "TFLAG.csv"),
)


def parse_axis_file(family: AxisFamily, path: Path) -> list[dict[str, object]]:
    """Parse a TW CSV axis file into structured entries."""

    current_section: str | None = None
    entries: list[dict[str, object]] = []

    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(";"):
            current_section = line[1:].strip() or current_section
            continue
        if line.startswith("\t;"):
            continue
        if line.startswith("\t"):
            continue

        parts = raw_line.split(",", 2)
        if len(parts) < 2:
            continue

        index_text = parts[0].strip().lstrip(";")
        if not index_text or not index_text.lstrip("-").isdigit():
            continue

        label = parts[1].strip()
        notes = parts[2].strip() if len(parts) > 2 else ""
        notes = notes if notes else None

        era_index = int(index_text)
        entries.append(
            {
                "key": f"{family.value}_{era_index}",
                "era_index": era_index,
                "label": label,
                "section": current_section,
                "notes": notes,
            }
        )

    return entries


def import_tw_axes(source_dir: Path, output_path: Path) -> None:
    """Import all supported axis files into one JSON registry."""

    payload: dict[str, list[dict[str, object]]] = {}
    for family, filename in FAMILY_FILES:
        payload[family.value] = parse_axis_file(family, source_dir / filename)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import eraTW axis CSV files.")
    parser.add_argument("--source", required=True, type=Path, help="Path to eraTW CSV directory.")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON path.")
    args = parser.parse_args()

    import_tw_axes(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()


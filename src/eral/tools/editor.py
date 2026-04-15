"""Web-based character and dialogue editor for erAL.

Launch with: python -m eral.tools.editor [--port PORT] [--root ROOT]

Opens a browser-based editor for creating and editing character packs,
including basic info, stats (BASE/PALAM/ABL/TALENT/CFLAG), dialogue, and events.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from eral.content.commands import load_command_definitions
from eral.content.marks import load_mark_definitions
from eral.content.port_map import load_port_map
from eral.content.relationships import load_relationship_stages
from eral.content.stat_axes import AxisFamily, load_stat_axis_catalog
from eral.content.tw_axis_registry import load_tw_axis_registry

TIME_SLOTS: tuple[str, ...] = ("dawn", "morning", "afternoon", "evening", "night", "late_night")

# ---------------------------------------------------------------------------
# TOML writer (minimal — covers the structures used in character packs)
# ---------------------------------------------------------------------------

def _toml_escape(s: str) -> str:
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", "\\n").replace("\t", "\\t")
    return f'"{s}"'


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return _toml_escape(v)
    raise TypeError(f"Unsupported TOML value type: {type(v)}")


def _dump_simple_table(d: dict, indent: str = "") -> list[str]:
    """Dump a flat dict of simple values."""
    lines = []
    for k, v in d.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            # array of tables — handled separately
            continue
        if isinstance(v, dict):
            continue
        if isinstance(v, list):
            items = ", ".join(_toml_escape(i) if isinstance(i, str) else str(i) for i in v)
            lines.append(f"{indent}{k} = [{items}]")
        else:
            lines.append(f"{indent}{k} = {_toml_value(v)}")
    return lines


def _dump_table(d: dict, prefix: str = "") -> list[str]:
    """Recursively dump a dict to TOML lines."""
    lines = []

    # Simple key=value pairs first
    simple_keys = []
    table_keys = []
    array_keys = []

    for k, v in d.items():
        if isinstance(v, dict):
            table_keys.append(k)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            array_keys.append(k)
        else:
            simple_keys.append(k)

    for k in simple_keys:
        v = d[k]
        if isinstance(v, list):
            items = ", ".join(_toml_escape(i) if isinstance(i, str) else str(i) for i in v)
            lines.append(f"{k} = [{items}]")
        else:
            lines.append(f"{k} = {_toml_value(v)}")

    # Sub-tables
    for k in table_keys:
        header = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        sub = _dump_table(d[k], header + ".")
        if sub:
            lines.append("")
            lines.append(f"[{header}]")
            lines.extend(sub)

    # Array of tables
    for k in array_keys:
        for item in d[k]:
            header = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            lines.append("")
            lines.append(f"[[{header}]]")
            # Flatten nested dicts
            for ik, iv in item.items():
                if isinstance(iv, list) and iv and isinstance(iv[0], str):
                    items = ", ".join(_toml_escape(s) for s in iv)
                    lines.append(f'{ik} = [{items}]')
                elif isinstance(iv, list) and iv and isinstance(iv[0], dict):
                    # nested array of tables
                    for sub_item in iv:
                        lines.append("")
                        lines.append(f"[[{header}.{ik}]]")
                        for sk, sv in sub_item.items():
                            if isinstance(sv, list) and sv and isinstance(sv[0], str):
                                items = ", ".join(_toml_escape(s) for s in sv)
                                lines.append(f'{sk} = [{items}]')
                            elif isinstance(sv, dict):
                                for dk, dv in sv.items():
                                    lines.append(f"{sk}.{dk} = {_toml_value(dv)}" if isinstance(dv, (int, float, bool, str)) else "")
                            else:
                                lines.append(f"{sk} = {_toml_value(sv)}")
                elif isinstance(iv, dict):
                    for dk, dv in iv.items():
                        if isinstance(dv, list):
                            items = ", ".join(_toml_escape(s) if isinstance(s, str) else str(s) for s in dv)
                            lines.append(f'{ik}.{dk} = [{items}]')
                        else:
                            lines.append(f"{ik}.{dk} = {_toml_value(dv)}")
                elif isinstance(iv, list):
                    items = ", ".join(_toml_escape(s) if isinstance(s, str) else str(s) for s in iv)
                    lines.append(f'{ik} = [{items}]')
                else:
                    lines.append(f"{ik} = {_toml_value(iv)}")

    return lines


def dump_toml(d: dict) -> str:
    """Serialize a dict to a TOML string."""
    lines = _dump_table(d)
    text = "\n".join(lines)
    # Clean up multiple blank lines
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip() + "\n"


# ---------------------------------------------------------------------------
# Data access helpers
# ---------------------------------------------------------------------------

def _characters_dir(root: Path) -> Path:
    return root / "data" / "base" / "characters"


def _registry_path(root: Path) -> Path:
    return root / "data" / "generated" / "tw_axis_registry.json"


def _stat_axes_path(root: Path) -> Path:
  return root / "data" / "base" / "stat_axes.toml"


def _port_map_path(root: Path) -> Path:
  return root / "data" / "base" / "port_map.toml"


def _commands_path(root: Path) -> Path:
  return root / "data" / "base" / "commands.toml"


def _relationship_stages_path(root: Path) -> Path:
  return root / "data" / "base" / "relationship_stages.toml"


def _marks_path(root: Path) -> Path:
  return root / "data" / "base" / "marks.toml"


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _load_registry(root: Path) -> dict:
    p = _registry_path(root)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_stat_axes(root: Path) -> dict[str, list[dict[str, object]]]:
  path = _stat_axes_path(root)
  if not path.exists():
    return {}
  catalog = load_stat_axis_catalog(path)
  payload: dict[str, list[dict[str, object]]] = {}
  for family in (AxisFamily.BASE, AxisFamily.PALAM):
    payload[family.value] = [
      {
        "key": axis.key,
        "era_index": axis.era_index,
        "label": axis.label,
        "group": axis.group,
      }
      for axis in catalog.family_axes(family)
    ]
  return payload


def _load_port_map(root: Path) -> list[dict]:
    """Load location list from port_map.toml."""
    path = _port_map_path(root)
    if not path.exists():
        return []
    port_map = load_port_map(path)
    return [
        {
            "key": location.key,
            "display_name": location.display_name,
            "zone": location.zone,
            "tags": list(location.tags),
            "start": location.start,
            "visibility": location.visibility,
        }
        for location in port_map.locations
    ]


def _load_command_keys(root: Path) -> list[str]:
    """Load command keys from commands.toml."""
    path = _commands_path(root)
    if not path.exists():
        return []
    return [command.key for command in load_command_definitions(path)]


def _load_commands(root: Path) -> list[dict[str, object]]:
    path = _commands_path(root)
    if not path.exists():
        return []
    return [
        {
            "key": command.key,
            "display_name": command.display_name,
            "category": command.category,
            "location_tags": list(command.location_tags),
            "time_slots": list(command.time_slots),
            "min_affection": command.min_affection,
            "min_trust": command.min_trust,
            "min_obedience": command.min_obedience,
            "required_stage": command.required_stage,
            "operation": command.operation,
            "requires_following": command.requires_following,
            "requires_date": command.requires_date,
            "required_marks": command.required_marks,
            "apply_marks": command.apply_marks,
            "remove_marks": list(command.remove_marks),
            "source": command.source,
            "downbase": command.downbase,
            "personal_income": command.personal_income,
            "success_tiers": list(command.success_tiers),
        }
        for command in load_command_definitions(path)
    ]


def _load_relationship_stages(root: Path) -> list[str]:
    """Load relationship stage keys."""
    path = _relationship_stages_path(root)
    if not path.exists():
        return []
    return [stage.key for stage in load_relationship_stages(path)]


def _load_relationship_stage_defs(root: Path) -> list[dict[str, object]]:
    path = _relationship_stages_path(root)
    if not path.exists():
        return []
    return [
        {
            "key": stage.key,
            "display_name": stage.display_name,
            "min_affection": stage.min_affection,
            "min_trust": stage.min_trust,
            "min_intimacy": stage.min_intimacy,
            "no_dislike_mark": stage.no_dislike_mark,
            "requires_item": stage.requires_item,
        }
        for stage in load_relationship_stages(path)
    ]


def _load_location_tags(root: Path) -> list[str]:
    """Collect all unique location tags from port_map."""
    path = _port_map_path(root)
    if not path.exists():
        return []
    port_map = load_port_map(path)
    tags = set()
    for loc in port_map.locations:
        for t in loc.tags:
            tags.add(t)
    return sorted(tags)


def _load_mark_defs(root: Path) -> list[dict[str, object]]:
    path = _marks_path(root)
    if not path.exists():
        return []
    return [
        {
            "key": mark.key,
            "display_name": mark.display_name,
            "group": mark.group,
            "max_level": mark.max_level,
        }
        for mark in load_mark_definitions(path)
    ]


def _load_meta(root: Path) -> dict[str, object]:
    port_map_path = _port_map_path(root)
    port_map = load_port_map(port_map_path) if port_map_path.exists() else None
    start_location = None
    if port_map is not None:
        start = port_map.starting_location()
        start_location = {
            "key": start.key,
            "display_name": start.display_name,
        }
    return {
        "locations": _load_port_map(root),
        "location_tags": _load_location_tags(root),
        "commands": _load_commands(root),
        "command_keys": _load_command_keys(root),
        "stages": _load_relationship_stage_defs(root),
        "stage_keys": _load_relationship_stages(root),
        "marks": _load_mark_defs(root),
        "stat_axes": _load_stat_axes(root),
        "registry": _load_registry(root),
        "time_slots": list(TIME_SLOTS),
        "starting_location": start_location,
    }


def list_characters(root: Path) -> list[dict]:
    """List all character packs with basic info."""
    chars_dir = _characters_dir(root)
    if not chars_dir.exists():
        return []
    result = []
    for d in sorted(chars_dir.iterdir()):
        if not d.is_dir():
            continue
        char_file = d / "character.toml"
        if not char_file.exists():
            continue
        info = _load_toml(char_file)
        result.append({
            "key": info.get("key", d.name),
            "display_name": info.get("display_name", d.name),
            "tags": info.get("tags", []),
        })
    return result


def load_character(root: Path, char_key: str) -> dict:
    """Load full character pack data."""
    char_dir = _characters_dir(root) / char_key
    if not char_dir.exists():
        return {}

    data = {
        "character": _load_toml(char_dir / "character.toml"),
        "base": _load_toml(char_dir / "base.toml"),
        "palam": _load_toml(char_dir / "palam.toml"),
        "abl": _load_toml(char_dir / "abl.toml"),
        "talent": _load_toml(char_dir / "talent.toml"),
        "cflag": _load_toml(char_dir / "cflag.toml"),
        "marks": _load_toml(char_dir / "marks.toml"),
        "dialogue": _load_toml(char_dir / "dialogue.toml"),
        "events": _load_toml(char_dir / "events.toml"),
    }
    return data


def save_character(root: Path, char_key: str, data: dict) -> dict:
    """Save character pack data to TOML files."""
    char_dir = _characters_dir(root) / char_key
    char_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for section in ("character", "base", "palam", "abl", "talent", "cflag", "marks"):
        if section in data and data[section]:
            path = char_dir / f"{section}.toml"
            path.write_text(dump_toml(data[section]), encoding="utf-8")
            saved_files.append(f"{section}.toml")

    # Dialogue
    if "dialogue" in data and data["dialogue"]:
        path = char_dir / "dialogue.toml"
        path.write_text(dump_toml(data["dialogue"]), encoding="utf-8")
        saved_files.append("dialogue.toml")

    # Events
    if "events" in data and data["events"]:
        path = char_dir / "events.toml"
        path.write_text(dump_toml(data["events"]), encoding="utf-8")
        saved_files.append("events.toml")

    return {"status": "ok", "files": saved_files}


def create_character(root: Path, char_key: str, display_name: str, tags: list[str], initial_location: str, schedule: dict) -> dict:
    """Create a new character pack."""
    char_dir = _characters_dir(root) / char_key
    if char_dir.exists():
        return {"status": "error", "message": f"角色 '{char_key}' 已存在"}

    char_data = {
        "key": char_key,
        "display_name": display_name,
        "tags": tags,
        "initial_location": initial_location,
        "schedule": schedule,
    }

    save_character(root, char_key, {
        "character": char_data,
        "base": {"stamina": 1000, "spirit": 800},
    })
    return {"status": "ok", "key": char_key}


def delete_character(root: Path, char_key: str) -> dict:
    """Delete a character pack directory."""
    import shutil
    char_dir = _characters_dir(root) / char_key
    if not char_dir.exists():
        return {"status": "error", "message": f"角色 '{char_key}' 不存在"}
    shutil.rmtree(char_dir)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class EditorHandler(BaseHTTPRequestHandler):
    root: Path = Path(".")

    def log_message(self, format, *args):
        pass  # Suppress request logs

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/api/characters":
            self._send_json(list_characters(self.root))
        elif path.startswith("/api/characters/"):
            key = path.split("/api/characters/")[1].rstrip("/")
            if key == "meta":
                # Return metadata for editor (locations, commands, stages, registry)
                meta = _load_meta(self.root)
                self._send_json({
                    "locations": meta["locations"],
                    "location_tags": meta["location_tags"],
                    "commands": meta["commands"],
                    "command_keys": meta["command_keys"],
                    "stages": meta["stages"],
                    "stage_keys": meta["stage_keys"],
                    "marks": meta["marks"],
                    "stat_axes": meta["stat_axes"],
                    "registry": meta["registry"],
                    "time_slots": meta["time_slots"],
                    "starting_location": meta["starting_location"],
                })
            else:
                data = load_character(self.root, key)
                if not data:
                    self._send_json({"error": "not found"}, 404)
                else:
                    self._send_json(data)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/characters":
            body = json.loads(self._read_body().decode("utf-8"))
            result = create_character(
                self.root,
                body["key"],
                body.get("display_name", body["key"]),
                body.get("tags", []),
                body.get("initial_location", "dock"),
                body.get("schedule", {}),
            )
            self._send_json(result)
        elif path.startswith("/api/characters/") and path.endswith("/delete"):
            key = path.split("/api/characters/")[1].replace("/delete", "")
            result = delete_character(self.root, key)
            self._send_json(result)
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/characters/"):
            key = path.split("/api/characters/")[1].rstrip("/")
            body = json.loads(self._read_body().decode("utf-8"))
            result = save_character(self.root, key, body)
            self._send_json(result)
        else:
            self.send_error(404)

    def _serve_html(self):
        html = _build_html()
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# HTML frontend
# ---------------------------------------------------------------------------

def _build_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>erAL 角色编辑器</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #1a1a2e; color: #e0e0e0; display: flex; height: 100vh; }
#sidebar { width: 240px; background: #16213e; padding: 16px; overflow-y: auto; border-right: 1px solid #0f3460; }
#sidebar h2 { font-size: 16px; margin-bottom: 12px; color: #e94560; }
#sidebar input { width: 100%; padding: 6px 8px; margin-bottom: 8px; background: #1a1a2e; border: 1px solid #0f3460; color: #e0e0e0; border-radius: 4px; }
.char-item { padding: 8px 10px; cursor: pointer; border-radius: 4px; margin-bottom: 2px; font-size: 14px; }
.char-item:hover { background: #0f3460; }
.char-item.active { background: #e94560; color: #fff; }
.btn { padding: 6px 14px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; margin: 2px; }
.btn-primary { background: #e94560; color: #fff; }
.btn-secondary { background: #0f3460; color: #e0e0e0; }
.btn-danger { background: #533a1b; color: #e0e0e0; }
.btn:hover { opacity: 0.85; }
#main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
#tabs { display: flex; background: #16213e; border-bottom: 2px solid #0f3460; }
.tab { padding: 10px 20px; cursor: pointer; border: none; background: none; color: #8a8a8a; font-size: 14px; }
.tab.active { color: #e94560; border-bottom: 2px solid #e94560; margin-bottom: -2px; }
#content { flex: 1; overflow-y: auto; padding: 20px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; color: #8a8a8a; margin-bottom: 4px; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 6px 8px; background: #1a1a2e; border: 1px solid #0f3460; color: #e0e0e0; border-radius: 4px; font-size: 13px; }
.form-group textarea { min-height: 60px; resize: vertical; }
.form-group select { cursor: pointer; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.grid-6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
.section-title { font-size: 15px; color: #e94560; margin: 20px 0 10px; padding-bottom: 4px; border-bottom: 1px solid #0f3460; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px; }
.stat-item { display: flex; align-items: center; gap: 8px; }
.stat-item label { min-width: 80px; font-size: 12px; color: #8a8a8a; }
.stat-item input { width: 80px; padding: 4px 6px; background: #1a1a2e; border: 1px solid #0f3460; color: #e0e0e0; border-radius: 3px; font-size: 13px; text-align: right; }
.entry-card { background: #16213e; border: 1px solid #0f3460; border-radius: 6px; padding: 12px; margin-bottom: 10px; }
.entry-card .entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.entry-card .entry-key { font-weight: bold; color: #e94560; font-size: 13px; }
.entry-card .lines-list { margin-top: 6px; }
.entry-card .line-item { display: flex; gap: 6px; margin-bottom: 4px; }
.entry-card .line-item textarea { flex: 1; min-height: 36px; padding: 4px 8px; background: #1a1a2e; border: 1px solid #0f3460; color: #e0e0e0; border-radius: 3px; font-size: 13px; resize: none; }
.field-help { margin-top: 4px; color: #8fa3c8; font-size: 11px; line-height: 1.4; }
.sub-section-title { margin: 10px 0 6px; color: #9fb3d9; font-size: 12px; font-weight: 600; }
.tag-chip { display: inline-block; background: #0f3460; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin: 2px; }
.empty-state { text-align: center; padding: 60px; color: #555; }
.save-bar { position: sticky; top: 0; background: #1a1a2e; padding: 10px 0; z-index: 10; border-bottom: 1px solid #0f3460; margin-bottom: 12px; display: flex; gap: 8px; align-items: center; }
.save-bar .status { font-size: 12px; color: #8a8a8a; margin-left: 8px; }
dialog { background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; border-radius: 8px; padding: 20px; }
dialog::backdrop { background: rgba(0,0,0,0.6); }
dialog h3 { color: #e94560; margin-bottom: 12px; }
</style>
</head>
<body>
<div id="sidebar">
  <h2>角色列表</h2>
  <input type="text" id="search" placeholder="搜索角色..." oninput="filterList()">
  <div id="char-list"></div>
  <div style="margin-top:12px">
    <button class="btn btn-primary" onclick="showCreateDialog()">+ 新建角色</button>
  </div>
</div>
<div id="main">
  <div id="tabs">
    <button class="tab active" data-tab="info" onclick="switchTab('info')">基本信息</button>
    <button class="tab" data-tab="stats" onclick="switchTab('stats')">数值属性</button>
    <button class="tab" data-tab="dialogue" onclick="switchTab('dialogue')">口上</button>
    <button class="tab" data-tab="events" onclick="switchTab('events')">事件</button>
  </div>
  <div id="content">
    <div class="empty-state">
      <p style="font-size:18px;margin-bottom:8px">erAL 角色编辑器</p>
      <p>从左侧选择角色，或点击"新建角色"开始</p>
    </div>
  </div>
</div>

<dialog id="create-dialog">
  <h3>新建角色</h3>
  <div class="form-group"><label>角色 key（英文，唯一标识）</label><input id="new-key" placeholder="如 belfast"></div>
  <div class="form-group"><label>显示名称</label><input id="new-name" placeholder="如 贝尔法斯特"></div>
  <div class="form-group"><label>标签（逗号分隔）</label><input id="new-tags" placeholder="如 belfast, cruiser, royal_navy"></div>
  <div class="form-group"><label>初始位置</label><select id="new-location"></select></div>
  <div class="section-title">日程表</div>
  <div class="grid-6" id="new-schedule"></div>
  <div style="margin-top:16px;text-align:right">
    <button class="btn btn-secondary" onclick="document.getElementById('create-dialog').close()">取消</button>
    <button class="btn btn-primary" onclick="doCreate()">创建</button>
  </div>
</dialog>

<dialog id="delete-dialog">
  <h3>确认删除</h3>
  <p id="delete-msg"></p>
  <div style="margin-top:16px;text-align:right">
    <button class="btn btn-secondary" onclick="document.getElementById('delete-dialog').close()">取消</button>
    <button class="btn btn-danger" onclick="doDelete()">删除</button>
  </div>
</dialog>

<script>
// ── State ──────────────────────────────────────────────
let meta = null;
let characters = [];
let currentKey = null;
let currentData = null;
let currentTab = 'info';

// ── Init ──────────────────────────────────────────────
async function init() {
  const res = await fetch('/api/characters/meta');
  meta = await res.json();
  await loadList();
}

async function loadList() {
  const res = await fetch('/api/characters');
  characters = await res.json();
  renderList();
}

function renderList(filter = '') {
  const el = document.getElementById('char-list');
  const filtered = characters.filter(c =>
    !filter || c.key.includes(filter) || c.display_name.includes(filter)
  );
  el.innerHTML = filtered.map(c =>
    '<div class="char-item' + (c.key === currentKey ? ' active' : '') +
    '" onclick="selectChar(\'' + c.key + '\')">' +
    c.display_name + ' <span style="color:#666;font-size:11px">(' + c.key + ')</span></div>'
  ).join('');
}

function filterList() {
  renderList(document.getElementById('search').value.trim());
}

// ── Select character ──────────────────────────────────
async function selectChar(key) {
  currentKey = key;
  renderList();
  const res = await fetch('/api/characters/' + key);
  currentData = await res.json();
  currentTab = 'info';
  renderTabs();
  renderContent();
}

// ── Tabs ──────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;
  renderTabs();
  renderContent();
}

function renderTabs() {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === currentTab);
  });
}

// ── Render content ────────────────────────────────────
function renderContent() {
  if (!currentData) return;
  const el = document.getElementById('content');
  switch (currentTab) {
    case 'info': el.innerHTML = renderInfo(); break;
    case 'stats': el.innerHTML = renderStats(); break;
    case 'dialogue': el.innerHTML = renderDialogue(); break;
    case 'events': el.innerHTML = renderEvents(); break;
  }
}

function locOpts(sel) {
  return '<option value="">--</option>' + (meta.locations || []).map(function(l) {
    return '<option value="' + esc(l.key) + '"' + (String(l.key) === String(sel || '') ? ' selected' : '') + '>' + esc(l.display_name) + ' (' + esc(l.key) + ')</option>';
  }).join('');
}

function cmdOpts(sel) {
  return '<option value="">--</option>' + (meta.commands || []).map(function(c) {
    var label = (c.display_name || c.key) + ' (' + c.key + ')';
    if (c.category) label += ' \u00b7 ' + c.category;
    return '<option value="' + esc(c.key) + '"' + (String(c.key) === String(sel || '') ? ' selected' : '') + '>' + esc(label) + '</option>';
  }).join('');
}

function stageOpts(sel) {
  return '<option value="">--</option>' + (meta.stages || []).map(function(s) {
    var label = (s.display_name || s.key) + ' (' + s.key + ')';
    return '<option value="' + esc(s.key) + '"' + (String(s.key) === String(sel || '') ? ' selected' : '') + '>' + esc(label) + '</option>';
  }).join('');
}

function boolOpts(val) {
  var v = val === true ? 'true' : val === false ? 'false' : '';
  return '<option value="">--</option><option value="true"' + (v === 'true' ? ' selected' : '') + '>是</option><option value="false"' + (v === 'false' ? ' selected' : '') + '>否</option>';
}

function help(text) { return '<div style="margin-top:2px;color:#8fa3c8;font-size:11px">' + esc(text) + '</div>'; }

// ── Info tab ──────────────────────────────────────────
function renderInfo() {
  var c = currentData.character || {};
  var schedule = c.schedule || {};
  var timeSlots = meta.time_slots || [];
  var startLoc = c.initial_location || '';

  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveInfo()">保存</button><span class="status" id="save-status"></span></div>';
  h += '<div class="grid-2">';
  h += '<div class="form-group"><label>角色 key（不可改）</label><input id="f-key" value="' + esc(c.key || '') + '" readonly style="opacity:0.6"></div>';
  h += '<div class="form-group"><label>显示名称</label><input id="f-display_name" value="' + esc(c.display_name || '') + '"></div>';
  h += '</div>';
  h += '<div class="form-group"><label>标签（逗号分隔）</label><input id="f-tags" value="' + esc((c.tags || []).join(', ')) + '">' + help('英文标签，如 enterprise, carrier, eagle_union') + '</div>';
  h += '<div class="form-group"><label>初始位置</label><select id="f-initial_location">' + locOpts(startLoc) + '</select>' + help('角色首次出现的位置。') + '</div>';
  h += '<div class="section-title">日程表</div>';
  h += '<div class="grid-6">';
  for (var t = 0; t < timeSlots.length; t++) {
    var ts = timeSlots[t];
    h += '<div class="form-group"><label>' + esc(ts) + '</label><select id="f-sched-' + esc(ts) + '">' + locOpts(schedule[ts] || startLoc) + '</select></div>';
  }
  h += '</div>';
  return h;
}

// ── Stats tab ─────────────────────────────────────────
function renderStats() {
  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveStats()">保存</button><span class="status" id="save-status"></span></div>';

  // BASE & PALAM from stat_axes
  var namedFamilies = [
    {key: 'base', title: 'BASE（即时资源）', help: '体力、气力等即时消耗/恢复的资源'},
    {key: 'palam', title: 'PALAM（累积参数）', help: '通过指令 SOURCE 结算后累积的参数'}
  ];
  for (var f = 0; f < namedFamilies.length; f++) {
    var fam = namedFamilies[f];
    var axes = (meta.stat_axes || {})[fam.key] || [];
    var current = currentData[fam.key] || {};
    h += '<div class="section-title">' + fam.title + '</div>';
    h += help(fam.help);
    if (axes.length === 0) {
      h += '<div style="color:#555;padding:8px">无注册表数据</div>';
      continue;
    }
    // Group by group field
    var groups = {};
    for (var i = 0; i < axes.length; i++) {
      var g = axes[i].group || '其他';
      if (!groups[g]) groups[g] = [];
      groups[g].push(axes[i]);
    }
    var gkeys = Object.keys(groups).sort();
    for (var gi = 0; gi < gkeys.length; gi++) {
      h += '<div style="margin:8px 0 4px;color:#9fb3d9;font-size:12px;font-weight:600">' + esc(gkeys[gi]) + '</div>';
      h += '<div class="stat-grid">';
      var items = groups[gkeys[gi]];
      for (var ii = 0; ii < items.length; ii++) {
        var ax = items[ii];
        var val = current[ax.key] != null ? current[ax.key] : 0;
        h += '<div class="stat-item"><label title="' + esc(ax.key) + '">' + esc(ax.label || ax.key) + '</label>';
        h += '<input type="number" data-section="' + fam.key + '" data-field="' + esc(ax.key) + '" value="' + val + '"></div>';
      }
      h += '</div>';
    }
  }

  // ABL, TALENT, CFLAG from registry
  var indexedFamilies = [
    {key: 'abl', title: 'ABL（能力等级）', help: '角色的各种能力等级。大部分初始为 0 即可。'},
    {key: 'talent', title: 'TALENT（素质）', help: '角色的先天素质。0=无，1=有，-1=相反素质。'},
    {key: 'cflag', title: 'CFLAG（角色标记）', help: '角色专属标记。大部分由系统运行时自动维护，初值一般设 0。'}
  ];
  for (var f = 0; f < indexedFamilies.length; f++) {
    var fam = indexedFamilies[f];
    var regs = (meta.registry || {})[fam.key] || [];
    var current = currentData[fam.key] || {};
    h += '<div class="section-title">' + fam.title + '</div>';
    h += help(fam.help);
    if (regs.length === 0) {
      h += '<div style="color:#555;padding:8px">无注册表数据</div>';
      continue;
    }
    // Group by section
    var groups = {};
    // First add current values not in registry
    for (var k in current) {
      var found = false;
      for (var r = 0; r < regs.length; r++) {
        if (String(regs[r].era_index) === k || regs[r].key === k) { found = true; break; }
      }
      if (!found) {
        var g = '自定义';
        if (!groups[g]) groups[g] = [];
        groups[g].push({era_index: parseInt(k) || 0, key: k, label: k, section: g, _val: current[k]});
      }
    }
    for (var i = 0; i < regs.length; i++) {
      var g = regs[i].section || '其他';
      if (!groups[g]) groups[g] = [];
      groups[g].push(regs[i]);
    }
    var gkeys = Object.keys(groups).sort();
    for (var gi = 0; gi < gkeys.length; gi++) {
      h += '<div style="margin:8px 0 4px;color:#9fb3d9;font-size:12px;font-weight:600">' + esc(gkeys[gi]) + '</div>';
      h += '<div class="stat-grid">';
      var items = groups[gkeys[gi]];
      for (var ii = 0; ii < items.length; ii++) {
        var reg = items[ii];
        var fieldKey = String(reg.era_index);
        var val = current[fieldKey] != null ? current[fieldKey] : (reg._val != null ? reg._val : 0);
        h += '<div class="stat-item"><label title="' + esc(reg.key) + ' [' + reg.era_index + ']">' + esc(reg.label || reg.key) + '</label>';
        h += '<input type="number" data-section="' + fam.key + '" data-field="' + esc(fieldKey) + '" value="' + val + '"></div>';
      }
      h += '</div>';
    }
  }

  // Marks
  var marks = currentData.marks || {};
  var markLines = [];
  for (var mk in marks) markLines.push(mk + '=' + marks[mk]);
  h += '<div class="section-title">MARK（印记）</div>';
  h += help('角色身上的印记。格式：每行一个 key=level，如 dislike_mark=1');
  h += '<div class="form-group"><textarea id="f-marks" rows="4">' + esc(markLines.join('\\n')) + '</textarea></div>';

  return h;
}

// ── Dialogue tab ──────────────────────────────────────
function renderDialogue() {
  var entries = (currentData.dialogue || {}).entries || [];
  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveDialogue()">保存</button>';
  h += '<button class="btn btn-secondary" onclick="addDialogueEntry()">+ 添加口上</button>';
  h += '<span class="status" id="save-status"></span></div>';
  h += help('口上是角色在玩家执行指令后说的台词。每条口上对应一个触发条件（指令、阶段、地点等），系统会自动匹配最合适的那条。');

  for (var i = 0; i < entries.length; i++) {
    var e = entries[i];
    h += '<div class="entry-card" data-idx="' + i + '">';
    h += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">';
    h += '<b style="color:#e94560">' + esc(e.key || '(新口上)') + '</b>';
    h += '<button class="btn btn-danger" onclick="removeDialogueEntry(' + i + ')">删除</button>';
    h += '</div>';

    // Key + actor
    h += '<div class="grid-2">';
    h += '<div class="form-group"><label>口上 key（唯一标识）</label><input data-dlg="key" data-idx="' + i + '" value="' + esc(e.key || '') + '">' + help('格式建议：角色_指令_地点，如 enterprise_chat_dock') + '</div>';
    h += '<div class="form-group"><label>角色 key</label><input data-dlg="actor_key" data-idx="' + i + '" value="' + esc(e.actor_key || currentKey) + '">' + help('默认当前角色 key。通用口上可填 _any。') + '</div>';
    h += '</div>';

    // Trigger conditions
    h += '<div style="margin-top:8px;color:#9fb3d9;font-size:12px;font-weight:600">触发条件（可选，留空表示不限制）</div>';
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>关联指令</label><select data-dlg="action_key" data-idx="' + i + '">' + cmdOpts(e.action_key) + '</select>' + help('玩家执行哪个指令时触发') + '</div>';
    h += '<div class="form-group"><label>需要关系阶段</label><select data-dlg="required_stage" data-idx="' + i + '">' + stageOpts(e.required_stage) + '</select>' + help('至少达到该阶段才触发') + '</div>';
    h += '<div class="form-group"><label>需要地点（逗号分隔）</label><input data-dlg="location_keys" data-idx="' + i + '" value="' + esc((e.location_keys || []).join(', ')) + '">' + help('如 dock, command_office') + '</div>';
    h += '</div>';
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>需要时段（逗号分隔）</label><input data-dlg="time_slots" data-idx="' + i + '" value="' + esc((e.time_slots || []).join(', ')) + '">' + help('如 morning, evening') + '</div>';
    h += '<div class="form-group"><label>需要私密</label><select data-dlg="requires_private" data-idx="' + i + '">' + boolOpts(e.requires_private) + '</select></div>';
    h += '<div class="form-group"><label>需要约会中</label><select data-dlg="requires_date" data-idx="' + i + '">' + boolOpts(e.requires_date) + '</select></div>';
    h += '</div>';

    // Lines
    h += '<div style="margin-top:8px;color:#9fb3d9;font-size:12px;font-weight:600">台词内容</div>';
    h += help('每条台词显示一行。可以写旁白（描述动作/神态）和对话（用「」包裹）。');
    var lines = e.lines || [];
    for (var j = 0; j < lines.length; j++) {
      h += '<div style="display:flex;gap:6px;margin-bottom:4px"><textarea data-dlg-line="' + i + '" data-line-idx="' + j + '" style="flex:1;min-height:36px;padding:4px 8px;background:#1a1a2e;border:1px solid #0f3460;color:#e0e0e0;border-radius:3px;font-size:13px;resize:vertical">' + esc(lines[j]) + '</textarea>';
      h += '<button class="btn btn-danger" style="height:36px" onclick="removeLine(' + i + ',' + j + ')">x</button></div>';
    }
    h += '<button class="btn btn-secondary" style="margin-top:4px" onclick="addLine(' + i + ')">+ 添加台词</button>';
    h += '</div>';
  }

  if (entries.length === 0) {
    h += '<div style="color:#555;text-align:center;padding:40px">暂无口上，点击"+ 添加口上"开始</div>';
  }
  return h;
}

// ── Events tab ────────────────────────────────────────
function renderEvents() {
  var events = (currentData.events || {}).events || [];
  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveEvents()">保存</button>';
  h += '<button class="btn btn-secondary" onclick="addEvent()">+ 添加事件</button>';
  h += '<span class="status" id="save-status"></span></div>';
  h += help('事件定义了"什么情况下触发特定口上"。事件不包含台词本身，只定义触发条件。口上通过 key 与事件关联。');

  for (var i = 0; i < events.length; i++) {
    var ev = events[i];
    h += '<div class="entry-card" data-idx="' + i + '">';
    h += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">';
    h += '<b style="color:#e94560">' + esc(ev.key || '(新事件)') + '</b>';
    h += '<button class="btn btn-danger" onclick="removeEvent(' + i + ')">删除</button>';
    h += '</div>';

    h += '<div class="grid-2">';
    h += '<div class="form-group"><label>事件 key（唯一标识）</label><input data-evt="key" data-idx="' + i + '" value="' + esc(ev.key || '') + '">' + help('格式建议：角色_指令_地点，如 enterprise_chat_dock') + '</div>';
    h += '<div class="form-group"><label>触发指令</label><select data-evt="action_key" data-idx="' + i + '">' + cmdOpts(ev.action_key) + '</select>' + help('玩家执行哪个指令时触发此事件') + '</div>';
    h += '</div>';

    h += '<div style="margin-top:6px;color:#9fb3d9;font-size:12px;font-weight:600">触发条件</div>';
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>角色标签（逗号分隔）</label><input data-evt="actor_tags" data-idx="' + i + '" value="' + esc((ev.actor_tags || []).join(', ')) + '">' + help('通常是角色 key，如 enterprise') + '</div>';
    h += '<div class="form-group"><label>地点（逗号分隔）</label><input data-evt="location_keys" data-idx="' + i + '" value="' + esc((ev.location_keys || []).join(', ')) + '">' + help('如 dock, command_office') + '</div>';
    h += '<div class="form-group"><label>时段（逗号分隔）</label><input data-evt="time_slots" data-idx="' + i + '" value="' + esc((ev.time_slots || []).join(', ')) + '">' + help('如 morning, afternoon, evening') + '</div>';
    h += '</div>';
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>需要关系阶段</label><select data-evt="required_stage" data-idx="' + i + '">' + stageOpts(ev.required_stage) + '</select></div>';
    h += '<div class="form-group"><label>需要约会中</label><select data-evt="requires_date" data-idx="' + i + '">' + boolOpts(ev.requires_date) + '</select></div>';
    h += '<div class="form-group"><label>需要私密</label><select data-evt="requires_private" data-idx="' + i + '">' + boolOpts(ev.requires_private) + '</select></div>';
    h += '</div>';

    h += '</div>';
  }

  if (events.length === 0) {
    h += '<div style="color:#555;text-align:center;padding:40px">暂无事件，点击"+ 添加事件"开始</div>';
  }
  return h;
}

// ── Save functions ────────────────────────────────────
async function saveAll(data) {
  const res = await fetch('/api/characters/' + currentKey, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data),
  });
  return await res.json();
}

function flash(msg) {
  const el = document.getElementById('save-status');
  if (el) { el.textContent = msg; setTimeout(() => el.textContent = '', 2000); }
}

async function saveInfo() {
  const c = currentData.character;
  c.display_name = document.getElementById('f-display_name').value;
  c.tags = document.getElementById('f-tags').value.split(',').map(s => s.trim()).filter(Boolean);
  c.initial_location = document.getElementById('f-initial_location').value;
  c.schedule = {};
  for (const ts of meta.time_slots) {
    c.schedule[ts] = document.getElementById('f-sched-' + ts).value;
  }
  currentData.character = c;
  await saveAll(currentData);
  await loadList();
  flash('已保存');
}

async function saveStats() {
  for (var si = 0; si < ['base','palam','abl','talent','cflag'].length; si++) {
    var sec = ['base','palam','abl','talent','cflag'][si];
    var inputs = document.querySelectorAll('input[data-section="' + sec + '"]');
    if (inputs.length === 0) continue;
    var obj = {};
    inputs.forEach(function(inp) {
      var val = parseInt(inp.value) || 0;
      if (val !== 0) obj[inp.dataset.field] = val;
    });
    currentData[sec] = obj;
  }
  // Marks
  var marksEl = document.getElementById('f-marks');
  if (marksEl) {
    var marksObj = {};
    marksEl.value.split('\n').map(function(s){return s.trim();}).filter(Boolean).forEach(function(line) {
      var parts = line.split('=');
      var mk = parts[0].trim();
      var mv = parts.length > 1 ? parseInt(parts[1].trim()) || 1 : 1;
      if (mk) marksObj[mk] = mv;
    });
    currentData.marks = marksObj;
  }
  await saveAll(currentData);
  flash('已保存');
}

async function saveDialogue() {
  collectDialogueFromDOM();
  await saveAll(currentData);
  flash('已保存');
}

async function saveEvents() {
  collectEventsFromDOM();
  await saveAll(currentData);
  flash('已保存');
}

function collectDialogueFromDOM() {
  var entries = [];
  var cards = document.querySelectorAll('#content .entry-card');
  for (var i = 0; i < cards.length; i++) {
    var card = cards[i];
    var idx = card.dataset.idx;
    if (idx === undefined) continue;
    var e = {};
    card.querySelectorAll('input[data-dlg]').forEach(function(inp) {
      if (inp.dataset.dlg === 'time_slots' || inp.dataset.dlg === 'location_keys') {
        e[inp.dataset.dlg] = inp.value.split(',').map(function(s){return s.trim();}).filter(Boolean);
      } else {
        e[inp.dataset.dlg] = inp.value;
      }
    });
    card.querySelectorAll('select[data-dlg]').forEach(function(sel) {
      if (sel.dataset.dlg === 'action_key') {
        e.action_key = sel.value || '';
      } else if (sel.dataset.dlg === 'required_stage') {
        e.required_stage = sel.value || null;
      } else if (sel.dataset.dlg === 'requires_private' || sel.dataset.dlg === 'requires_date') {
        e[sel.dataset.dlg] = sel.value === '' ? null : sel.value === 'true';
      }
    });
    var lines = [];
    card.querySelectorAll('textarea[data-dlg-line]').forEach(function(ta) {
      lines.push(ta.value);
    });
    e.lines = lines;
    entries.push(e);
  }
  currentData.dialogue = {entries: entries};
}

function collectEventsFromDOM() {
  var events = [];
  document.querySelectorAll('#content input[data-evt="key"]').forEach(function(inp) {
    var i = inp.dataset.idx;
    var ev = {key: inp.value};
    document.querySelectorAll('#content input[data-evt][data-idx="' + i + '"]').forEach(function(inp2) {
      if (inp2.dataset.evt === 'key') return;
      if (inp2.dataset.evt === 'actor_tags' || inp2.dataset.evt === 'location_keys' || inp2.dataset.evt === 'time_slots') {
        ev[inp2.dataset.evt] = inp2.value.split(',').map(function(s){return s.trim();}).filter(Boolean);
      } else {
        ev[inp2.dataset.evt] = inp2.value;
      }
    });
    document.querySelectorAll('#content select[data-evt][data-idx="' + i + '"]').forEach(function(sel) {
      if (sel.dataset.evt === 'action_key') {
        ev.action_key = sel.value || '';
      } else if (sel.dataset.evt === 'required_stage') {
        ev.required_stage = sel.value || null;
      } else if (sel.dataset.evt === 'requires_private' || sel.dataset.evt === 'requires_date') {
        ev[sel.dataset.evt] = sel.value === '' ? null : sel.value === 'true';
      }
    });
    events.push(ev);
  });
  currentData.events = {events: events};
}

// ── Dialogue helpers ─────────────────────────────────
function addDialogueEntry() {
  if (!currentData.dialogue) currentData.dialogue = {entries: []};
  if (!currentData.dialogue.entries) currentData.dialogue.entries = [];
  currentData.dialogue.entries.push({
    key: currentKey + '_' + Date.now(),
    actor_key: currentKey,
    action_key: '',
    required_stage: null,
    time_slots: [],
    location_keys: [],
    requires_private: null,
    requires_date: null,
    lines: [''],
  });
  renderContent();
}

function addLine(idx) {
  collectDialogueFromDOM();
  currentData.dialogue.entries[idx].lines.push('');
  renderContent();
}

function removeLine(idx, lineIdx) {
  collectDialogueFromDOM();
  currentData.dialogue.entries[idx].lines.splice(lineIdx, 1);
  renderContent();
}

function removeDialogueEntry(idx) {
  collectDialogueFromDOM();
  currentData.dialogue.entries.splice(idx, 1);
  renderContent();
}

// ── Event helpers ─────────────────────────────────────
function addEvent() {
  if (!currentData.events) currentData.events = { events: [] };
  if (!currentData.events.events) currentData.events.events = [];
  currentData.events.events.push({
    key: currentKey + '_evt_' + Date.now(),
    action_key: '',
    actor_tags: [currentKey],
    location_keys: [],
    time_slots: [],
    required_stage: null,
    min_affection: null,
    min_trust: null,
    min_obedience: null,
    requires_date: null,
    requires_private: null,
    required_marks: {},
  });
  renderContent();
}

function removeEvent(idx) {
  collectEventsFromDOM();
  currentData.events.events.splice(idx, 1);
  renderContent();
}

// ── Create / Delete ──────────────────────────────────
function showCreateDialog() {
  document.getElementById('new-location').innerHTML = locOpts('');
  var schedDiv = document.getElementById('new-schedule');
  schedDiv.innerHTML = (meta.time_slots || []).map(function(ts) {
    return '<div class="form-group"><label>' + esc(ts) + '</label><select id="new-sched-' + esc(ts) + '">' + locOpts('') + '</select></div>';
  }).join('');
  document.getElementById('new-key').value = '';
  document.getElementById('new-name').value = '';
  document.getElementById('new-tags').value = '';
  document.getElementById('create-dialog').showModal();
}

async function doCreate() {
  const key = document.getElementById('new-key').value.trim();
  if (!key) { alert('请输入角色 key'); return; }
  const schedule = {};
  for (const ts of meta.time_slots) {
    schedule[ts] = document.getElementById('new-sched-' + ts).value;
  }
  const res = await fetch('/api/characters', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      key: key,
      display_name: document.getElementById('new-name').value || key,
      tags: document.getElementById('new-tags').value.split(',').map(s => s.trim()).filter(Boolean),
      initial_location: document.getElementById('new-location').value,
      schedule: schedule,
    }),
  });
  const result = await res.json();
  document.getElementById('create-dialog').close();
  if (result.status === 'error') { alert(result.message); return; }
  await loadList();
  await selectChar(key);
}

function confirmDelete() {
  if (!currentKey) return;
  document.getElementById('delete-msg').textContent = '确定要删除角色 "' + currentKey + '" 吗？此操作不可恢复。';
  document.getElementById('delete-dialog').showModal();
}

async function doDelete() {
  const res = await fetch('/api/characters/' + currentKey + '/delete', { method: 'POST' });
  await res.json();
  document.getElementById('delete-dialog').close();
  currentKey = null;
  currentData = null;
  await loadList();
  document.getElementById('content').innerHTML = '<div class="empty-state"><p>角色已删除</p></div>';
}

// ── Utils ─────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Start ─────────────────────────────────────────────
init();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="erAL character editor")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on")
    parser.add_argument("--root", type=str, default=None, help="Project root directory")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parents[2]
    EditorHandler.root = root

    server = HTTPServer(("127.0.0.1", args.port), EditorHandler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"erAL 角色编辑器已启动: {url}")
    print(f"项目根目录: {root}")
    print("按 Ctrl+C 停止")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.server_close()


if __name__ == "__main__":
    main()

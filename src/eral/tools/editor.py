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


def _load_port_map(root: Path) -> list[dict]:
    """Load location list from port_map.toml."""
    path = root / "data" / "base" / "port_map.toml"
    if not path.exists():
        return []
    with path.open("rb") as f:
        raw = tomllib.load(f)
    locations = raw.get("locations", [])
    return [{"key": l["key"], "display_name": l.get("display_name", l["key"])} for l in locations]


def _load_command_keys(root: Path) -> list[str]:
    """Load command keys from commands.toml."""
    path = root / "data" / "base" / "commands.toml"
    if not path.exists():
        return []
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return [c["key"] for c in raw.get("commands", [])]


def _load_relationship_stages(root: Path) -> list[str]:
    """Load relationship stage keys."""
    path = root / "data" / "base" / "relationship_stages.toml"
    if not path.exists():
        return []
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return [s["key"] for s in raw.get("stages", [])]


def _load_location_tags(root: Path) -> list[str]:
    """Collect all unique location tags from port_map."""
    path = root / "data" / "base" / "port_map.toml"
    if not path.exists():
        return []
    with path.open("rb") as f:
        raw = tomllib.load(f)
    tags = set()
    for loc in raw.get("locations", []):
        for t in loc.get("tags", []):
            tags.add(t)
    return sorted(tags)


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
                registry = _load_registry(self.root)
                self._send_json({
                    "locations": _load_port_map(self.root),
                    "location_tags": _load_location_tags(self.root),
                    "commands": _load_command_keys(self.root),
                    "stages": _load_relationship_stages(self.root),
                    "registry": registry,
                    "time_slots": ["dawn", "morning", "afternoon", "evening", "night", "late_night"],
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

// ── Info tab ──────────────────────────────────────────
function renderInfo() {
  const c = currentData.character || {};
  const schedule = c.schedule || {};
  const timeSlots = meta.time_slots || [];
  const locations = meta.locations || [];
  const locOptions = '<option value="">--</option>' + locations.map(l =>
    '<option value="' + l.key + '"' + '>' + l.display_name + ' (' + l.key + ')</option>'
  ).join('');

  return '<div class="save-bar"><button class="btn btn-primary" onclick="saveInfo()">保存基本信息</button><span class="status" id="save-status"></span></div>' +
    '<div class="grid-2">' +
    '<div class="form-group"><label>角色 key</label><input id="f-key" value="' + esc(c.key || '') + '" readonly style="opacity:0.6"></div>' +
    '<div class="form-group"><label>显示名称</label><input id="f-display_name" value="' + esc(c.display_name || '') + '"></div>' +
    '</div>' +
    '<div class="form-group"><label>标签（逗号分隔）</label><input id="f-tags" value="' + esc((c.tags || []).join(', ')) + '"></div>' +
    '<div class="form-group"><label>初始位置</label><select id="f-initial_location">' + locOptions + '</select></div>' +
    '<div class="section-title">日程表</div>' +
    '<div class="grid-6">' +
    timeSlots.map(ts =>
      '<div class="form-group"><label>' + ts + '</label>' +
      '<select id="f-sched-' + ts + '">' + locOptions + '</select></div>'
    ).join('') +
    '</div>';
}

// ── Stats tab ─────────────────────────────────────────
function renderStats() {
  const sections = [
    { key: 'base', title: 'BASE（即时资源）', data: currentData.base || {}, reg: 'base' },
    { key: 'palam', title: 'PALAM（累积参数）', data: currentData.palam || {}, reg: 'palam' },
    { key: 'abl', title: 'ABL（能力）', data: currentData.abl || {}, reg: 'abl' },
    { key: 'talent', title: 'TALENT（素质）', data: currentData.talent || {}, reg: 'talent' },
    { key: 'cflag', title: 'CFLAG（角色标记）', data: currentData.cflag || {}, reg: 'cflag' },
  ];

  // Build label maps from registry
  const regMap = {};
  for (const reg of ['base', 'palam', 'abl', 'talent', 'cflag']) {
    regMap[reg] = {};
    const entries = (meta.registry || {})[reg] || [];
    for (const e of entries) {
      regMap[reg][String(e.era_index)] = e.label || e.key;
      regMap[reg][e.key] = e.label || e.key;
    }
  }

  // Named stats (base, palam) use string keys
  // Indexed stats (abl, talent, cflag) use era_index
  let html = '<div class="save-bar"><button class="btn btn-primary" onclick="saveStats()">保存数值</button><span class="status" id="save-status"></span></div>';

  for (const sec of sections) {
    html += '<div class="section-title">' + sec.title + '</div>';
    html += '<div class="stat-grid">';
    const entries = Object.entries(sec.data);
    if (entries.length === 0) {
      // Show registry entries with 0 default
      const regEntries = (meta.registry || {})[sec.reg] || [];
      if (regEntries.length > 0) {
        for (const re of regEntries.slice(0, 30)) {
          const label = re.label || re.key;
          const val = sec.data[re.key] ?? sec.data[String(re.era_index)] ?? 0;
          const fieldKey = sec.key === 'abl' || sec.key === 'talent' || sec.key === 'cflag'
            ? String(re.era_index) : re.key;
          html += '<div class="stat-item"><label title="' + esc(re.key) + '">' + esc(label) + '</label>' +
            '<input type="number" data-section="' + sec.key + '" data-field="' + esc(fieldKey) + '" value="' + val + '"></div>';
        }
      } else {
        html += '<div style="color:#555;font-size:13px;padding:8px">暂无数据</div>';
      }
    } else {
      for (const [k, v] of entries) {
        const label = regMap[sec.reg][k] || k;
        html += '<div class="stat-item"><label title="' + esc(k) + '">' + esc(label) + '</label>' +
          '<input type="number" data-section="' + sec.key + '" data-field="' + esc(k) + '" value="' + v + '"></div>';
      }
    }
    html += '</div>';
  }

  // Marks section
  const marks = currentData.marks || {};
  html += '<div class="section-title">MARK（印记）</div>';
  html += '<div class="form-group"><label>印记列表（每行一个 key）</label>' +
    '<textarea id="f-marks" rows="4">' + esc(Object.keys(marks).join('\n')) + '</textarea></div>';

  return html;
}

// ── Dialogue tab ──────────────────────────────────────
function renderDialogue() {
  const entries = (currentData.dialogue || {}).entries || [];
  let html = '<div class="save-bar"><button class="btn btn-primary" onclick="saveDialogue()">保存口上</button>' +
    '<button class="btn btn-secondary" onclick="addDialogueEntry()">+ 添加条目</button>' +
    '<span class="status" id="save-status"></span></div>';

  for (let i = 0; i < entries.length; i++) {
    const e = entries[i];
    html += '<div class="entry-card" data-idx="' + i + '">' +
      '<div class="entry-header">' +
      '<span class="entry-key">' + esc(e.key || '(未命名)') + '</span>' +
      '<div><button class="btn btn-danger" onclick="removeDialogueEntry(' + i + ')">删除</button></div>' +
      '</div>' +
      '<div class="grid-3">' +
      '<div class="form-group"><label>条目 key</label><input data-dlg="key" data-idx="' + i + '" value="' + esc(e.key || '') + '"></div>' +
      '<div class="form-group"><label>actor_key</label><input data-dlg="actor_key" data-idx="' + i + '" value="' + esc(e.actor_key || currentKey) + '"></div>' +
      '<div class="form-group"><label>优先级</label><input type="number" data-dlg="priority" data-idx="' + i + '" value="' + (e.priority ?? 10) + '"></div>' +
      '</div>' +
      renderDialogueConditions(e, i) +
      '<div class="lines-list">' +
      '<label style="font-size:12px;color:#8a8a8a">台词（每行一条）</label>';

    const lines = e.lines || [];
    for (let j = 0; j < lines.length; j++) {
      html += '<div class="line-item"><textarea data-dlg-line="' + i + '" data-line-idx="' + j + '">' + esc(lines[j]) + '</textarea></div>';
    }
    html += '<button class="btn btn-secondary" style="margin-top:4px" onclick="addLine(' + i + ')">+ 添加台词</button>';
    html += '</div></div>';
  }

  if (entries.length === 0) {
    html += '<div style="color:#555;text-align:center;padding:40px">暂无口上条目，点击"添加条目"开始</div>';
  }
  return html;
}

function renderDialogueConditions(e, idx) {
  const stageOpts = (meta.stages || []).map(s =>
    '<option value="' + s + '">' + s + '</option>'
  ).join('');
  return '<div class="grid-3">' +
    '<div class="form-group"><label>关联指令</label><input data-dlg="action_key" data-idx="' + idx + '" value="' + esc(e.action_key || '') + '" list="cmd-list"></div>' +
    '<div class="form-group"><label>关系阶段</label><input data-dlg="stage" data-idx="' + idx + '" value="' + esc(e.stage || '') + '" list="stage-list"></div>' +
    '<div class="form-group"><label>关联地点</label><input data-dlg="location_key" data-idx="' + idx + '" value="' + esc(e.location_key || '') + '" list="loc-list"></div>' +
    '</div>' +
    '<datalist id="cmd-list">' + (meta.commands || []).map(c => '<option value="' + c + '">').join('') + '</datalist>' +
    '<datalist id="stage-list">' + stageOpts + '</datalist>' +
    '<datalist id="loc-list">' + (meta.locations || []).map(l => '<option value="' + l.key + '">').join('') + '</datalist>';
}

// ── Events tab ────────────────────────────────────────
function renderEvents() {
  const events = (currentData.events || {}).events || [];
  let html = '<div class="save-bar"><button class="btn btn-primary" onclick="saveEvents()">保存事件</button>' +
    '<button class="btn btn-secondary" onclick="addEvent()">+ 添加事件</button>' +
    '<span class="status" id="save-status"></span></div>';

  for (let i = 0; i < events.length; i++) {
    const ev = events[i];
    html += '<div class="entry-card" data-idx="' + i + '">' +
      '<div class="entry-header">' +
      '<span class="entry-key">' + esc(ev.key || '(未命名)') + '</span>' +
      '<div><button class="btn btn-danger" onclick="removeEvent(' + i + ')">删除</button></div>' +
      '</div>' +
      '<div class="grid-2">' +
      '<div class="form-group"><label>事件 key</label><input data-evt="key" data-idx="' + i + '" value="' + esc(ev.key || '') + '"></div>' +
      '<div class="form-group"><label>关联指令 (action_key)</label><input data-evt="action_key" data-idx="' + i + '" value="' + esc(ev.action_key || '') + '" list="cmd-list2"></div>' +
      '</div>' +
      '<div class="grid-3">' +
      '<div class="form-group"><label>角色标签（逗号分隔）</label><input data-evt="actor_tags" data-idx="' + i + '" value="' + esc((ev.actor_tags || []).join(', ')) + '"></div>' +
      '<div class="form-group"><label>地点（逗号分隔）</label><input data-evt="location_keys" data-idx="' + i + '" value="' + esc((ev.location_keys || []).join(', ')) + '"></div>' +
      '<div class="form-group"><label>时段（逗号分隔）</label><input data-evt="time_slots" data-idx="' + i + '" value="' + esc((ev.time_slots || []).join(', ')) + '"></div>' +
      '</div>' +
      '<div class="grid-3">' +
      '<div class="form-group"><label>最低好感</label><input type="number" data-evt="min_affection" data-idx="' + i + '" value="' + (ev.min_affection ?? '') + '"></div>' +
      '<div class="form-group"><label>最低信赖</label><input type="number" data-evt="min_trust" data-idx="' + i + '" value="' + (ev.min_trust ?? '') + '"></div>' +
      '<div class="form-group"><label>需要私密</label><select data-evt="requires_private" data-idx="' + i + '">' +
        '<option value="false"' + (!ev.requires_private ? ' selected' : '') + '>否</option>' +
        '<option value="true"' + (ev.requires_private ? ' selected' : '') + '>是</option></select></div>' +
      '</div></div>';
  }

  if (events.length === 0) {
    html += '<div style="color:#555;text-align:center;padding:40px">暂无事件，点击"添加事件"开始</div>';
  }

  html += '<datalist id="cmd-list2">' + (meta.commands || []).map(c => '<option value="' + c + '">').join('') + '</datalist>';
  return html;
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
  // Collect stats from inputs
  for (const sec of ['base', 'palam', 'abl', 'talent', 'cflag']) {
    const inputs = document.querySelectorAll('input[data-section="' + sec + '"]');
    if (inputs.length === 0) continue;
    const obj = {};
    inputs.forEach(inp => {
      const val = parseInt(inp.value) || 0;
      if (val !== 0) obj[inp.dataset.field] = val;
    });
    currentData[sec] = obj;
  }
  // Marks
  const marksText = document.getElementById('f-marks').value;
  const marksObj = {};
  marksText.split('\n').map(s => s.trim()).filter(Boolean).forEach(k => { marksObj[k] = true; });
  currentData.marks = marksObj;

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
  const entries = [];
  const cards = document.querySelectorAll('.entry-card');
  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const idx = card.dataset.idx;
    if (idx === undefined) continue;
    const e = {};
    card.querySelectorAll('input[data-dlg]').forEach(inp => {
      if (inp.dataset.dlg === 'priority') e[inp.dataset.dlg] = parseInt(inp.value) || 10;
      else e[inp.dataset.dlg] = inp.value;
    });
    // Lines
    const lines = [];
    card.querySelectorAll('textarea[data-dlg-line]').forEach(ta => {
      lines.push(ta.value);
    });
    e.lines = lines;
    entries.push(e);
  }
  currentData.dialogue = { entries: entries };
}

function collectEventsFromDOM() {
  const events = [];
  document.querySelectorAll('input[data-evt="key"]').forEach(inp => {
    const i = inp.dataset.idx;
    const ev = { key: inp.value };
    document.querySelectorAll('input[data-evt][data-idx="' + i + '"]').forEach(inp2 => {
      if (inp2.dataset.evt === 'key') return;
      if (['actor_tags', 'location_keys', 'time_slots'].includes(inp2.dataset.evt)) {
        ev[inp2.dataset.evt] = inp2.value.split(',').map(s => s.trim()).filter(Boolean);
      } else if (inp2.dataset.evt === 'min_affection' || inp2.dataset.evt === 'min_trust') {
        if (inp2.value) ev[inp2.dataset.evt] = parseInt(inp2.value);
      } else {
        ev[inp2.dataset.evt] = inp2.value;
      }
    });
    const sel = document.querySelector('select[data-evt="requires_private"][data-idx="' + i + '"]');
    if (sel) ev.requires_private = sel.value === 'true';
    events.push(ev);
  });
  currentData.events = { events: events };
}

// ── Dialogue helpers ─────────────────────────────────
function addDialogueEntry() {
  if (!currentData.dialogue) currentData.dialogue = { entries: [] };
  if (!currentData.dialogue.entries) currentData.dialogue.entries = [];
  currentData.dialogue.entries.push({
    key: currentKey + '_new_' + Date.now(),
    actor_key: currentKey,
    priority: 10,
    lines: [''],
  });
  renderContent();
}

function addLine(idx) {
  collectDialogueFromDOM();
  currentData.dialogue.entries[idx].lines.push('');
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
  const locSel = document.getElementById('new-location');
  locSel.innerHTML = (meta.locations || []).map(l =>
    '<option value="' + l.key + '">' + l.display_name + '</option>'
  ).join('');
  const schedDiv = document.getElementById('new-schedule');
  schedDiv.innerHTML = (meta.time_slots || []).map(ts =>
    '<div class="form-group"><label>' + ts + '</label><select id="new-sched-' + ts + '">' +
    (meta.locations || []).map(l => '<option value="' + l.key + '">' + l.display_name + '</option>').join('') +
    '</select></div>'
  ).join('');
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

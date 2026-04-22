"""Minimal HTTP API server for erAL web playtesting.

Uses only Python stdlib (http.server + json).  Serves a single-page
HTML client and exposes REST-like JSON endpoints that wrap the
assembled Application.
"""

from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from eral.app.bootstrap import Application, create_application
from eral.content.stat_axes import AxisFamily
from eral.domain.actions import AppliedChange
from eral.domain.world import CharacterState, TimeSlot
from eral.ui import body_info, personal_info


# ── JSON helpers ───────────────────────────────────────────────

class _Encoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, AppliedChange):
            return {
                "family": obj.family,
                "target": obj.target,
                "before": obj.before,
                "after": obj.after,
                "delta": obj.delta,
            }
        if isinstance(obj, TimeSlot):
            return obj.value
        return super().default(obj)


def _dump(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, cls=_Encoder).encode("utf-8")


# ── State helpers ──────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # erAL/
_CHAR_RES_DIR = _REPO_ROOT / "resources" / "characters"

# BASE 轴显示配置：哪些轴作为状态条展示、默认上限、显示顺序
_DEFAULT_MAX_BASE = 1000
_NPC_BASE_KEYS: tuple[str, ...] = ("stamina", "spirit", "drunkenness", "reason")
_PLAYER_BASE_KEYS: tuple[str, ...] = (
    "stamina", "spirit", "drunkenness", "reason", "semen",
)
_BASE_LABELS: dict[str, str] = {
    "stamina": "体力",
    "spirit": "气力",
    "drunkenness": "酒意",
    "reason": "理性",
    "semen": "精液",
    "ejaculation": "射精",
    "erection": "勃起",
    "mood": "情绪",
}


def _build_base_entries(
    stats_base: Any,
    keys: tuple[str, ...],
    max_values: dict[str, int],
) -> list[dict[str, Any]]:
    """Assemble ordered BASE entries for UI rendering.

    Returns a list preserving `keys` order; each entry has key/label/value/max.
    """
    entries: list[dict[str, Any]] = []
    for key in keys:
        raw = None
        if stats_base is not None:
            try:
                raw = stats_base.get(key)
            except Exception:
                raw = None
        value = int(raw) if raw is not None else 0
        maximum = int(max_values.get(key, _DEFAULT_MAX_BASE))
        entries.append({
            "key": key,
            "label": _BASE_LABELS.get(key, key),
            "value": value,
            "max": maximum,
        })
    return entries
_PLACEHOLDER_AVATAR_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
    b'<rect width="64" height="64" fill="#1e3a5f"/>'
    b'<text x="32" y="36" text-anchor="middle" fill="#c8aa6e" font-size="14">?</text>'
    b"</svg>"
)
_PLACEHOLDER_PORTRAIT_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="500">'
    b'<rect width="300" height="500" fill="#0d1b2a"/>'
    b'<text x="150" y="250" text-anchor="middle" fill="#4a6a8a" font-size="16">'
    b"</text></svg>"
)


def _char_image_path(char_key: str, filename: str, skin_key: str | None = None) -> Path | None:
    if skin_key:
        p = _CHAR_RES_DIR / char_key / skin_key / filename
        if p.exists():
            return p
    p = _CHAR_RES_DIR / char_key / filename
    return p if p.exists() else None


def _actor_snapshot(actor: CharacterState, max_values: dict[str, int], *, gender: str = "female") -> dict[str, Any]:
    return {
        "key": actor.key,
        "display_name": actor.display_name,
        "location_key": actor.location_key,
        "affection": actor.affection,
        "trust": actor.trust,
        "obedience": actor.obedience,
        "tags": list(actor.tags),
        "is_following": actor.is_following,
        "follow_ready": actor.follow_ready,
        "is_on_date": actor.is_on_date,
        "relationship_stage": (
            actor.relationship_stage.display_name if actor.relationship_stage else None
        ),
        "relationship_stage_key": (
            actor.relationship_stage.key if actor.relationship_stage else None
        ),
        "fatigue": actor.fatigue,
        "stamina": actor.stats.base.get("stamina"),
        "spirit": actor.stats.base.get("spirit"),
        "reason": actor.stats.base.get("reason"),
        "mood": actor.stats.base.get("mood"),
        "drunkenness": actor.stats.base.get("drunkenness"),
        "base": _build_base_entries(actor.stats.base, _NPC_BASE_KEYS, max_values),
        "gender": gender,
        "is_male": gender == "male",
        "palam": dict(actor.stats.palam.values),
        "marks": dict(actor.marks),
        "conditions": dict(actor.conditions),
        "memories": dict(actor.memories),
        "active_persistent_states": list(actor.active_persistent_states),
        "equipped_skin_key": actor.equipped_skin_key,
        "owned_skins": sorted(actor.owned_skins),
        "removed_slots": list(actor.removed_slots),
        "is_same_room": actor.is_same_room,
        "is_on_commission": actor.is_on_commission,
        "avatar_url": f"/static/characters/{actor.key}/avatar.webp",
        "portrait_url": f"/static/characters/{actor.key}/portrait.webp",
    }


def _resolve_skin_path(char_key: str, filename: str, skin_key: str | None) -> str:
    if skin_key:
        return f"/static/characters/{char_key}/{skin_key}/{filename}"
    return f"/static/characters/{char_key}/{filename}"


def _world_snapshot(app: Application) -> dict[str, Any]:
    world = app.world
    return {
        "player_name": world.player_name,
        "day": world.current_day,
        "year": world.current_year,
        "month": world.current_month,
        "weekday": world.current_weekday,
        "hour": world.current_hour,
        "minute": world.current_minute,
        "time_slot": world.current_time_slot.value,
        "season": world.current_season,
        "location": {
            "key": world.active_location.key,
            "display_name": world.active_location.display_name,
        },
        "weather": world.weather_key,
        "personal_funds": world.personal_funds,
        "port_funds": world.port_funds,
        "training_active": world.training_active,
        "training_actor_key": world.training_actor_key,
        "training_position_key": world.training_position_key,
        "training_step_index": world.training_step_index,
        "training_flags": dict(world.training_flags),
        "is_busy": world.is_busy,
        "is_date_traveling": world.is_date_traveling,
        "date_partner_key": world.date_partner_key,
        "inventory": dict(world.inventory),
        "facility_levels": dict(world.facility_levels),
        "conditions": dict(world.conditions),
    }


def _commands_for_actor(app: Application, actor_key: str) -> list[dict[str, Any]]:
    cmds = app.command_service.available_commands_for_actor(app.world, actor_key)
    return [
        {
            "key": c.key,
            "display_name": c.display_name,
            "category": c.category,
            "shopfront_key": c.shopfront_key,
        }
        for c in cmds
    ]


# ── Request handler ────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    app: Application
    _client_html: bytes = b""

    def log_message(self, fmt: str, *args: Any) -> None:
        # Suppress default request logging to reduce noise.
        pass

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = _dump(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message: str, status: int = 400) -> None:
        self._send_json({"error": message}, status=status)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: C901
        path = self.path.split("?", 1)[0]
        app = self.app
        world = app.world

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(self._client_html)))
            self.end_headers()
            self.wfile.write(self._client_html)
            return

        if path.startswith("/static/characters/"):
            self._serve_character_static(path)
            return

        if path.startswith("/static/"):
            self._serve_static_file(path)
            return

        if path == "/api/state":
            max_values = app.vital_service.max_values
            gender_by_key = {d.key: d.gender for d in app.roster}
            visible = [
                _actor_snapshot(a, max_values, gender=gender_by_key.get(a.key, "female"))
                for a in world.visible_characters()
            ]
            self._send_json({"world": _world_snapshot(app), "visible_actors": visible})
            return

        if path == "/api/actors":
            max_values = app.vital_service.max_values
            gender_by_key = {d.key: d.gender for d in app.roster}
            visible = [
                _actor_snapshot(a, max_values, gender=gender_by_key.get(a.key, "female"))
                for a in world.visible_characters()
            ]
            self._send_json(visible)
            return

        if path.startswith("/api/actor/") and path.endswith("/commands"):
            actor_key = path[len("/api/actor/") : -len("/commands")]
            try:
                cmds = _commands_for_actor(app, actor_key)
            except KeyError:
                self._send_error("Actor not found", 404)
                return
            self._send_json(cmds)
            return

        if path.startswith("/api/actor/") and path.endswith("/status"):
            actor_key = path[len("/api/actor/") : -len("/status")]
            actor = next((a for a in world.characters if a.key == actor_key), None)
            if actor is None:
                self._send_error("Actor not found", 404)
                return
            self._send_json(_build_status_data(app, actor))
            return

        if path == "/api/destinations":
            dests = app.navigation_service.available_destinations(world)
            self._send_json(
                [
                    {
                        "key": d.destination_key,
                        "display_name": d.destination_name,
                        "area_key": d.destination_area_key,
                        "area_name": d.destination_area_name,
                        "cost_minutes": d.total_cost_minutes,
                        "is_adjacent": d.is_adjacent,
                    }
                    for d in dests
                ]
            )
            return

        if path == "/api/shop":
            query = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            shopfront_key = params.get("shopfront")
            if not shopfront_key:
                self._send_error("Missing shopfront parameter")
                return
            items = app.shop_service.list_items(shopfront_key)
            self._send_json(
                [
                    {
                        "key": item.key,
                        "display_name": item.display_name,
                        "price": item.price,
                        "description": item.description,
                        "category": item.category,
                    }
                    for item in items
                ]
            )
            return

        if path == "/api/scene":
            query = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            actor_key = params.get("actor_key")
            if not actor_key:
                self._send_error("Missing actor_key parameter")
                return
            actor = next((a for a in world.characters if a.key == actor_key), None)
            if actor is None:
                self._send_error("Actor not found", 404)
                return
            loc = app.port_map.location_by_key(world.active_location.key)
            scene = app.scene_service.build_for_actor(
                world, actor, action_key="", location_tags=loc.tags,
            )
            self._send_json({
                "actor_key": scene.actor_key,
                "actor_tags": list(scene.actor_tags),
                "time_slot": scene.time_slot,
                "season": scene.season,
                "weather": scene.weather_key,
                "location_key": scene.location_key,
                "location_tags": list(scene.location_tags),
                "is_private": scene.is_private,
                "visible_count": scene.visible_count,
                "affection": scene.affection,
                "trust": scene.trust,
                "obedience": scene.obedience,
                "relationship_stage": scene.relationship_stage,
                "relationship_rank": scene.relationship_rank,
                "is_following": scene.is_following,
                "is_on_date": scene.is_on_date,
                "is_same_room": scene.is_same_room,
                "equipped_skin_key": scene.equipped_skin_key,
                "equipped_skin_tags": list(scene.equipped_skin_tags),
                "removed_slots": list(scene.removed_slots),
                "marks": dict(scene.marks),
                "memories": dict(scene.memories),
                "is_training": scene.is_training,
                "training_position_key": scene.training_position_key,
                "training_step_index": scene.training_step_index,
                "training_results": list(scene.training_results),
            })
            return

        if path == "/api/runtime_log":
            query = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            try:
                limit = max(1, min(500, int(params.get("limit", "50"))))
            except ValueError:
                limit = 50
            log_path = app.runtime_logger.log_path()
            entries: list[dict[str, Any]] = []
            if log_path.exists():
                with log_path.open("r", encoding="utf-8") as handle:
                    lines = handle.readlines()
                for raw in lines[-limit:]:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        entries.append(json.loads(raw))
                    except json.JSONDecodeError:
                        continue
            self._send_json(entries)
            return

        if path == "/api/inventory":
            items_by_key = {item.key: item for item in app.items}
            rows: list[dict[str, Any]] = []
            for key, count in world.inventory.items():
                if count <= 0:
                    continue
                item = items_by_key.get(key)
                rows.append({
                    "key": key,
                    "display_name": item.display_name if item else key,
                    "count": count,
                    "description": item.description if item else "",
                    "category": getattr(item, "category", "") if item else "",
                    "tags": list(getattr(item, "tags", ()) or ()) if item else [],
                })
            rows.sort(key=lambda r: (r["category"], r["key"]))
            self._send_json(rows)
            return

        if path == "/api/calendar":
            cal = app.calendar_definition
            month = world.current_month
            season = world.current_season
            festivals = []
            for event in getattr(cal, "festivals", ()) or ():
                festivals.append({
                    "key": event.key,
                    "display_name": event.display_name,
                    "month": event.month,
                    "day": event.day,
                })
            self._send_json({
                "year": world.current_year,
                "month": month,
                "day": world.current_day,
                "weekday": world.current_weekday,
                "season": season,
                "festivals": festivals,
            })
            return

        if path == "/api/world_meta":
            roster = [
                {
                    "key": d.key,
                    "display_name": d.display_name,
                    "tags": list(d.tags),
                    "home_location_key": d.home_location_key,
                }
                for d in app.roster
            ]
            areas = []
            for area_key in app.port_map.area_keys():
                area = app.port_map.area_by_key(area_key)
                if area is not None:
                    areas.append({"key": area.key, "display_name": area.display_name})
            cur_loc = app.port_map.location_by_key(world.active_location.key)
            self._send_json({
                "roster": roster,
                "areas": areas,
                "current_location": {
                    "key": cur_loc.key,
                    "display_name": cur_loc.display_name,
                    "tags": list(cur_loc.tags),
                    "area_key": cur_loc.area_key,
                    "visibility": cur_loc.visibility,
                },
            })
            return

        if path == "/api/player":
            max_values = app.vital_service.max_values
            gender = world.player_gender or "male"
            keys = _PLAYER_BASE_KEYS if gender == "male" else _NPC_BASE_KEYS
            stats_base = world.player_stats.base if world.player_stats is not None else None
            base = _build_base_entries(stats_base, keys, max_values)
            self._send_json({
                "name": world.player_name,
                "gender": gender,
                "is_male": gender == "male",
                "base": base,
                # 保留旧字段以兼容前端
                "stamina": stats_base.get("stamina") if stats_base is not None else 2000,
                "max_stamina": max_values.get("stamina", 2000),
                "spirit": stats_base.get("spirit") if stats_base is not None else 1500,
                "max_spirit": max_values.get("spirit", 1500),
                "reason": stats_base.get("reason") if stats_base is not None else 1000,
                "max_reason": max_values.get("reason", 1000),
            })
            return

        if path == "/api/game_status":
            # 用于前端判断是否需要走"新游戏捏人"流程
            save_path = app.save_service.quicksave_path()
            has_save = save_path.exists()
            # 使用 conditions["game_started"] 作为当前世界是否已完成建档的标记
            started = world.get_condition("game_started") > 0
            self._send_json({
                "has_save": has_save,
                "started": started,
                "current_player_name": world.player_name,
                "current_player_gender": world.player_gender,
            })
            return
            return

        self._send_error("Not found", 404)

    def _serve_static_file(self, path: str) -> None:
        static_dir = Path(__file__).resolve().parent / "static"
        rel = path[len("/static/"):]
        file_path = static_dir / rel
        if not file_path.exists() or not file_path.is_file():
            self._send_error("Not found", 404)
            return
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_character_static(self, path: str) -> None:
        tail = path[len("/static/characters/"):]
        parts = tail.split("/")
        # patterns: <key>/<filename>  or  <key>/<skin>/<filename>
        if len(parts) == 2:
            char_key, filename = parts
            skin_key = None
        elif len(parts) == 3:
            char_key, skin_key, filename = parts
        else:
            self._send_error("Not found", 404)
            return
        img_path = _char_image_path(char_key, filename, skin_key)
        if filename == "avatar.webp" and img_path is None:
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(_PLACEHOLDER_AVATAR_SVG)))
            self.end_headers()
            self.wfile.write(_PLACEHOLDER_AVATAR_SVG)
            return
        elif filename == "portrait.webp" and img_path is None:
            svg = _PLACEHOLDER_PORTRAIT_SVG.replace(
                b"</text>", f"{char_key}</text>".encode()
            )
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(svg)))
            self.end_headers()
            self.wfile.write(svg)
            return
        if img_path is None:
            self._send_error("Not found", 404)
            return
        mime = mimetypes.guess_type(str(img_path))[0] or "application/octet-stream"
        data = img_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: C901
        path = self.path
        app = self.app
        world = app.world
        body = self._read_json()

        if path == "/api/execute":
            actor_key = body.get("actor_key")
            command_key = body.get("command_key")
            if not actor_key or not command_key:
                self._send_error("Missing actor_key or command_key")
                return
            try:
                result = app.command_service.execute(world, actor_key, command_key)
            except ValueError as exc:
                self._send_json(
                    {
                        "success": False,
                        "messages": [str(exc)],
                        "actor_key": actor_key,
                        "action_key": command_key,
                    }
                )
                return
            response: dict[str, Any] = {
                "success": result.success,
                "action_key": result.action_key,
                "actor_key": result.actor_key,
                "messages": result.messages,
                "changes": result.changes,
                "fainted": result.fainted,
                "shopfront_key": result.shopfront_key,
            }
            if result.funds_delta:
                response["funds_delta"] = result.funds_delta
            self._send_json(response)
            return

        if path == "/api/move":
            location_key = body.get("location_key")
            if not location_key:
                self._send_error("Missing location_key")
                return
            move_result = app.navigation_service.execute_move(world, location_key)
            self._send_json(
                {
                    "success": move_result.success,
                    "messages": move_result.messages,
                    "location": {
                        "key": world.active_location.key,
                        "display_name": world.active_location.display_name,
                    },
                }
            )
            return

        if path == "/api/shop/buy":
            shopfront_key = body.get("shopfront_key")
            item_key = body.get("item_key")
            if not shopfront_key or not item_key:
                self._send_error("Missing shopfront_key or item_key")
                return
            purchase = app.shop_service.purchase(world, shopfront_key, item_key)
            self._send_json(
                {
                    "success": purchase.success,
                    "item_key": purchase.item_key,
                    "count": purchase.count,
                    "total_price": purchase.total_price,
                    "reason": purchase.reason,
                }
            )
            return

        if path == "/api/wait":
            if app.game_loop is not None:
                app.game_loop.advance_time(world)
            if app.companion_service is not None:
                app.companion_service.refresh_world(world)
            encountered = [
                {"key": a.key, "display_name": a.display_name}
                for a in world.encounter_characters()
            ]
            for actor in world.characters:
                if actor.location_key == world.active_location.key:
                    actor.encounter_location_key = world.active_location.key
            self._send_json(
                {
                    "time_slot": world.current_time_slot.value,
                    "hour": world.current_hour,
                    "minute": world.current_minute,
                    "encountered": encountered,
                }
            )
            return

        if path == "/api/save":
            app.save_service.save_world(world)
            self._send_json({"saved": True})
            return

        if path == "/api/new_game":
            # 新游戏建档：接收玩家选项并覆盖当前世界状态
            name = str(body.get("name") or "").strip() or "指挥官"
            gender = str(body.get("gender") or "male").strip()
            if gender not in ("male", "female"):
                gender = "male"
            # 属性加成（可选；对应 base axis key → 加成值）
            stat_bonuses = body.get("stat_bonuses") or {}
            # 初始 TALENT 选择（era_index 列表；每个 talent 置 1）
            talent_picks = body.get("talent_picks") or []
            # 开局资金加成（可选）
            bonus_funds = int(body.get("bonus_funds") or 0)

            world.player_name = name
            world.player_gender = gender

            if world.player_stats is not None:
                for key, delta in stat_bonuses.items():
                    try:
                        world.player_stats.base.add(str(key), int(delta))
                    except Exception:
                        continue
                for era_idx in talent_picks:
                    try:
                        world.player_stats.compat.talent.set(int(era_idx), 1)
                    except Exception:
                        continue

            if bonus_funds > 0:
                world.personal_funds += bonus_funds

            # 标记建档完成
            world.set_condition("game_started", 1)
            # 立即落存档，避免下次启动再次弹出建档
            app.save_service.save_world(world)
            self._send_json({
                "ok": True,
                "player_name": world.player_name,
                "player_gender": world.player_gender,
                "personal_funds": world.personal_funds,
            })
            return

        if path == "/api/load":
            loaded = app.save_service.load_world()
            if loaded is not None:
                app.world = loaded
                app.distribution_service.refresh_world(app.world)
                app.relationship_service.refresh_world(app.world)
                app.companion_service.refresh_world(app.world)
                app.date_service.refresh_world(app.world)
            self._send_json({"loaded": loaded is not None})
            return

        self._send_error("Not found", 404)


# ── Status panel data builder ──────────────────────────────────

def _build_status_data(app: Application, actor: CharacterState) -> dict[str, Any]:
    """Build serialisable six-tab status data for the web client."""
    definition = next((d for d in app.roster if d.key == actor.key), None)
    abl_entries = app.stat_axes.family_axes(AxisFamily.ABL)
    talent_entries = app.stat_axes.family_axes(AxisFamily.TALENT)

    abilities: list[dict[str, Any]] = []
    experience: list[dict[str, Any]] = []
    for entry in abl_entries:
        val = actor.stats.compat.abl.get(entry.era_index)
        exp_val = actor.stats.abl_exp.get(entry.era_index, 0)
        if val > 0 or exp_val > 0:
            abilities.append({
                "era_index": entry.era_index,
                "label": entry.label,
                "level": val,
                "exp": exp_val,
            })
            experience.append({
                "era_index": entry.era_index,
                "label": entry.label,
                "level": val,
                "exp": exp_val,
            })

    talents: list[dict[str, Any]] = []
    for entry in talent_entries:
        val = actor.stats.compat.talent.get(entry.era_index)
        if val > 0:
            talents.append({
                "era_index": entry.era_index,
                "label": entry.label,
                "value": val,
            })

    intimacy_abl = actor.stats.compat.abl.get(9)
    counters = {
        "train_total_steps": actor.conditions.get("train_total_steps", 0),
        "total_orgasm_count": actor.conditions.get("total_orgasm_count", 0),
        "train_touch_count": actor.conditions.get("train_touch_count", 0),
        "train_kiss_count": actor.conditions.get("train_kiss_count", 0),
    }

    fallen_progress = []
    for stage_def in app.relationship_stages:
        fallen_progress.append({
            "key": stage_def.key,
            "display_name": stage_def.display_name,
            "min_affection": stage_def.min_affection,
            "min_trust": stage_def.min_trust,
            "min_intimacy": stage_def.min_intimacy,
            "no_dislike_mark": stage_def.no_dislike_mark,
            "requires_item": stage_def.requires_item,
            "current_affection": actor.affection,
            "current_trust": actor.trust,
            "current_intimacy": intimacy_abl,
        })

    data: dict[str, Any] = {
        "clothing_ability": {
            "equipped_skin": actor.equipped_skin_key,
            "removed_slots": list(actor.removed_slots),
            "abilities": abilities,
            "talents": talents,
        },
        "experience": experience,
        "counters": counters,
    }

    activity = personal_info.activity_hours(definition) if definition else "—"
    areas = personal_info.frequent_areas(definition, app.port_map) if definition else "—"
    home = personal_info.home_location_display(definition, app.port_map) if definition else "—"
    milestones = [
        {"label": m.label, "day": m.day}
        for m in personal_info.milestones(actor)
    ]
    data["personal"] = {
        "personality": personal_info.personality_from_tags(actor.tags),
        "activity_hours": [activity] if activity and activity != "—" else [],
        "frequent_areas": [areas] if areas and areas != "—" else [],
        "home": home,
        "milestones": milestones,
    }

    gift_prefs = getattr(definition, "gift_preferences", None) if definition else None
    food_prefs = getattr(definition, "food_preferences", None) if definition else None
    data["likes"] = {
        "gift_preferences": {
            "liked": list(gift_prefs.liked_tags) if gift_prefs else [],
            "disliked": list(gift_prefs.disliked_tags) if gift_prefs else [],
        },
        "food_preferences": {
            "liked": list(food_prefs.liked_tags) if food_prefs else [],
            "disliked": list(food_prefs.disliked_tags) if food_prefs else [],
        },
    }

    outer = body_info.outer_parts(actor)
    inner = body_info.inner_parts(actor)
    data["body"] = {
        "outer": [
            {"label": p.label, "tags": list(p.tags), "description": p.description, "history": p.history}
            for p in outer
        ],
        "inner": [
            {"label": p.label, "tags": list(p.tags), "description": p.description, "history": p.history}
            for p in inner
        ],
    }

    stage = actor.relationship_stage
    data["fallen"] = {
        "stage": stage.key if stage else None,
        "stage_name": stage.display_name if stage else "—",
        "has_pledge_ring": app.world.item_count("pledge_ring") > 0,
        "progress": fallen_progress,
    }

    return data


# ── Server bootstrap ───────────────────────────────────────────

def _find_client_html() -> bytes:
    """Load the bundled single-page client."""
    here = Path(__file__).resolve().parent
    client_path = here / "web_client.html"
    if client_path.exists():
        return client_path.read_bytes()
    return b"<h1>web_client.html not found</h1>"


def run_web_server(app: Application | None = None, port: int = 8080) -> None:
    """Start the development HTTP server."""
    if app is None:
        app = create_application()

    _Handler.app = app
    _Handler._client_html = _find_client_html()

    server = HTTPServer(("", port), _Handler)
    print(f"erAL web server running at http://localhost:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()

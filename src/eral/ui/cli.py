"""Interactive CLI game loop for erAL."""

from __future__ import annotations

from eral.app.bootstrap import Application
from eral.domain.world import WorldState


# ── display helpers ────────────────────────────────────────────────

def _print_header(world: WorldState, app: Application) -> None:
    location = world.active_location
    print()
    print(f"═══ 第{world.current_day}天 · {_slot_label(world.current_time_slot.value)} ═══")
    print(f"地点：{location.display_name}")
    if world.date_partner_key:
        print(f"约会中：{world.date_partner_key}")


def _slot_label(slot: str) -> str:
    labels = {
        "dawn": "清晨",
        "morning": "上午",
        "afternoon": "午后",
        "evening": "傍晚",
        "night": "夜晚",
        "late_night": "深夜",
    }
    return labels.get(slot, slot)


def _print_visible_characters(world: WorldState) -> None:
    visible = world.visible_characters()
    if not visible:
        print("  （周围没有人）")
        return
    for actor in visible:
        tags: list[str] = []
        if actor.is_following:
            tags.append("同行")
        if actor.is_on_date:
            tags.append("约会中")
        active_marks = [f"{k}:{v}" for k, v in actor.marks.items() if v > 0]
        if active_marks:
            tags.extend(active_marks)
        stage_text = actor.relationship_stage.display_name if actor.relationship_stage else ""
        suffix = ""
        if tags:
            suffix = f" [{', '.join(tags)}]"
        print(
            f"  {actor.display_name}  "
            f"好感:{actor.affection} 信赖:{actor.trust} 服从:{actor.obedience} "
            f"关系:{stage_text}{suffix}"
        )


def _print_action_result(messages: list[str]) -> None:
    print()
    for line in messages:
        print(f"  {line}")


# ── command builders ───────────────────────────────────────────────

def _build_menu(app: Application, world: WorldState) -> list[tuple[str, str, str | None]]:
    """Return (label, action_type, param) tuples for the menu.

    action_type is one of: 'command', 'move', 'wait', 'status', 'save', 'quit'.
    """
    menu: list[tuple[str, str, str | None]] = []
    visible = world.visible_characters()

    # actor commands — only show against visible characters
    for actor in visible:
        actor_commands = app.command_service.available_commands_for_actor(world, actor.key)
        for cmd in actor_commands:
            menu.append((f"{cmd.display_name} → {actor.display_name}", "command", f"{actor.key}:{cmd.key}"))

    # navigation
    visible_destinations = app.navigation_service.visible_destinations(world)
    for key in visible_destinations:
        loc = app.port_map.location_by_key(key)
        menu.append((f"前往 {loc.display_name}", "move", key))

    # time
    menu.append(("等待（推进时段）", "wait", None))
    menu.append(("查看状态", "status", None))
    menu.append(("保存", "save", None))
    if app.save_service.has_quicksave():
        menu.append(("读取快速存档", "load", None))
    menu.append(("退出", "quit", None))
    return menu


def _print_menu(menu: list[tuple[str, str, str | None]]) -> None:
    print()
    print("── 可用操作 ──")
    for i, (label, _, _) in enumerate(menu, 1):
        print(f"  [{i}] {label}")


def _print_status(world: WorldState, app: Application) -> None:
    print()
    print(f"── 玩家：{world.player_name} ──")
    print(f"日期：第{world.current_day}天  时段：{_slot_label(world.current_time_slot.value)}")
    print(f"地点：{world.active_location.display_name}")
    print()
    print("── 角色 ──")
    for actor in world.characters:
        loc = app.port_map.location_by_key(actor.location_key)
        stage_text = actor.relationship_stage.display_name if actor.relationship_stage else "—"
        tags: list[str] = []
        if actor.is_following:
            tags.append("同行")
        if actor.is_on_date:
            tags.append("约会中")
        suffix = f" [{', '.join(tags)}]" if tags else ""
        print(
            f"  {actor.display_name} @ {loc.display_name}  "
            f"好感:{actor.affection} 信赖:{actor.trust} "
            f"关系:{stage_text}{suffix}"
        )


# ── main loop ──────────────────────────────────────────────────────

def run_cli(app: Application) -> None:
    world = app.world
    print(f"\n{app.config.game_title} — 交互模式")

    while True:
        _print_header(world, app)
        _print_visible_characters(world)
        menu = _build_menu(app, world)
        _print_menu(menu)

        try:
            raw = input("\n请选择 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break

        if not raw:
            continue

        try:
            choice = int(raw)
        except ValueError:
            print("请输入数字。")
            continue

        if choice < 1 or choice > len(menu):
            print("无效选项。")
            continue

        label, action_type, param = menu[choice - 1]

        if action_type == "quit":
            print("再见。")
            break

        if action_type == "status":
            _print_status(world, app)
            continue

        if action_type == "save":
            save_path = app.save_service.save_world(world)
            print(f"\n  已保存到 {save_path.name}。")
            continue

        if action_type == "load":
            world = app.save_service.load_world()
            app.world = world
            app.relationship_service.refresh_world(world)
            app.companion_service.refresh_world(world)
            app.date_service.refresh_world(world)
            print("\n  已读取快速存档。")
            continue

        if action_type == "wait":
            app.game_loop.advance_time(world)
            app.companion_service.refresh_world(world)
            print(f"\n  时间推进到 {_slot_label(world.current_time_slot.value)}。")
            # Check for new encounters after schedule refresh
            encountered = world.encounter_characters()
            for actor in encountered:
                print(f"  遇到了{actor.display_name}。")
                actor.encounter_location_key = world.active_location.key
            continue

        if action_type == "move":
            result = app.navigation_service.move_player(world, param)
            _print_action_result(result.messages)
            continue

        if action_type == "command":
            actor_key, cmd_key = param.split(":", 1)
            result = app.command_service.execute(world, actor_key, cmd_key)
            _print_action_result(result.messages)
            if result.changes:
                for change in result.changes:
                    direction = "↑" if change.delta > 0 else "↓"
                    print(f"    {change.family}.{change.target} {direction}{abs(change.delta)} ({change.before}→{change.after})")
            continue

"""Interactive CLI game loop for erAL — eraTW-style terminal UI.

Renders a structured, color-coded terminal interface that mirrors the
classic eraTW layout:

  ① Header status line (day / time / location / funds)
  ② Target character info (name / affection / trust)
  ③ Vital bars (stamina / spirit / reason)
  ④ PALAM parameter grid
  ⑤ Message / dialogue log
  ⑥ Categorized command menu
  ⑦ Input prompt with last-command hint
"""

from __future__ import annotations

from collections.abc import Callable

from eral.app.bootstrap import Application
from eral.domain.world import CharacterState, WorldState
from eral.systems.calendar import weekday_label
from eral.ui.ansi import (
    BOLD,
    RESET,
    FG_BLUE,
    FG_CYAN,
    FG_DARK_GRAY,
    FG_GRAY,
    FG_GREEN,
    FG_MAGENTA,
    FG_ORANGE,
    FG_RED,
    FG_WHITE,
    FG_YELLOW,
    bar,
    clear_screen,
    cjk_center,
    cjk_ljust,
    cjk_width,
    colorize,
    fg,
    header_separator,
    separator,
    terminal_width,
)


# ── helpers ────────────────────────────────────────────────────────

_SLOT_LABELS: dict[str, str] = {
    "dawn": "清晨",
    "morning": "上午",
    "afternoon": "午后",
    "evening": "傍晚",
    "night": "夜晚",
    "late_night": "深夜",
}


def _slot_label(slot: str) -> str:
    return _SLOT_LABELS.get(slot, slot)


def _reason_stars(value: int, max_val: int = 1000) -> str:
    """Map reason value to a 5-star rating string."""
    if max_val <= 0:
        ratio = 0.0
    else:
        ratio = max(0.0, min(1.0, value / max_val))
    filled = round(ratio * 5)
    return colorize("★" * filled, FG_YELLOW) + colorize("☆" * (5 - filled), FG_DARK_GRAY)


# ── PALAM level thresholds (eraTW standard) ───────────────────────

_PALAM_LV = (0, 100, 500, 1500, 3000, 6000, 10000, 15000, 25000)


def _palam_level(value: int) -> tuple[int, int, int]:
    """Return (level, progress_in_level, threshold_for_next)."""
    lv = 0
    for i in range(len(_PALAM_LV) - 1, -1, -1):
        if value >= _PALAM_LV[i]:
            lv = i
            break
    if lv >= len(_PALAM_LV) - 1:
        return lv, 0, 0
    return lv, value - _PALAM_LV[lv], _PALAM_LV[lv + 1] - _PALAM_LV[lv]


def _palam_cell(label: str, value: int, col_width: int) -> str:
    """Render a single PALAM cell: label + Lv + mini bar."""
    lv, cur, need = _palam_level(value)
    lv_text = f"{label}Lv{lv}"
    if need > 0 and cur > 0:
        ratio = cur / need
        filled = int(ratio * 4)
        mini = "■" * filled + "□" * (4 - filled)
        lv_text += f" {mini}"
    color = FG_YELLOW if lv > 0 else FG_DARK_GRAY
    return colorize(cjk_ljust(lv_text, col_width), color)


# ── ABL section display names ──────────────────────────────────────

_ABL_SECTION_NAMES: dict[str, str] = {
    "感覚": "感覚系",
    "基本": "基本能力",
    "中毒": "中毒系",
    "技能": "技能系",
    "性技": "性技巧",
}

_ABL_SECTION_ORDER = ("感覚", "基本", "中毒", "技能", "性技")

# ── Clothing slot placeholders ─────────────────────────────────────

_CLOTHING_SLOTS = (
    ("头饰", "headwear"),
    ("饰品", "accessory"),
    ("上衣", "top"),
    ("裙子", "skirt"),
    ("内衣(上)", "underwear_top"),
    ("内衣(下)", "underwear_bottom"),
    ("袜子", "socks"),
    ("鞋", "shoes"),
    ("附属", "attachment"),
)

# ── Talent group by index range ────────────────────────────────────

_TALENT_GROUPS: tuple[tuple[int, int, str], ...] = (
    (0, 2, "性别"),
    (3, 9, "陷落素质"),
    (10, 19, "性格"),
    (20, 27, "性关注"),
    (30, 34, "少女心"),
    (40, 41, "体质"),
    (46, 57, "技术"),
    (60, 62, "洁癖度"),
    (70, 78, "快感反应"),
    (80, 86, "性癖"),
    (90, 94, "魅力"),
    (100, 122, "身体特征"),
    (130, 299, "特殊"),
)


def _talent_group_name(index: int) -> str:
    """Return the Chinese group name for a talent index."""
    for lo, hi, name in _TALENT_GROUPS:
        if lo <= index <= hi:
            return name
    return "其他"


# ── Zone ① : Header ───────────────────────────────────────────────

def _render_header(world: WorldState, app: Application) -> None:
    tw = terminal_width()
    print(header_separator("═", tw))

    day_str = colorize(f"第{world.current_day}天", FG_BLUE, bold=True)
    slot_str = colorize(f"({_slot_label(world.current_time_slot.value)})", FG_CYAN)
    loc_str = colorize(world.active_location.display_name, FG_WHITE, bold=True)
    funds_str = colorize(f"资金:{world.personal_funds}", FG_YELLOW)

    parts = [day_str, slot_str, f"地点:{loc_str}", funds_str]

    if world.date_partner_key:
        partner = next(
            (c for c in world.characters if c.key == world.date_partner_key),
            None,
        )
        name = partner.display_name if partner else world.date_partner_key
        parts.append(colorize(f"[约会中:{name}]", FG_MAGENTA, bold=True))

    player_str = colorize(f"玩家:{world.player_name}", FG_GRAY)
    parts.append(player_str)

    print("  " + "  ".join(parts))

    # Player vitals line
    # TODO: WorldState currently has no player stats (stamina/spirit).
    #       When player ActorNumericState is added, read from world.player_stats.
    #       For now show placeholder values matching eraTW's header.
    p_sta_label = colorize("体", FG_GRAY)
    p_sta_bar = bar(2000, 2000, 15, FG_GREEN)
    p_spi_label = colorize("気", FG_GRAY)
    p_spi_bar = bar(1500, 1500, 15, FG_CYAN)
    print(f"  {colorize('▼[主人公]', FG_GRAY)}  {p_sta_label} {p_sta_bar}  {p_spi_label} {p_spi_bar}")
    print(header_separator("═", tw))


# ── Zone ② : Target actor status ──────────────────────────────────

def _render_target_status(actor: CharacterState) -> None:
    """Render detailed status for the selected/visible character."""
    # Name & relationship
    name = colorize(f"【{actor.display_name}】", FG_WHITE, bold=True)
    stage_text = actor.relationship_stage.display_name if actor.relationship_stage else "陌生"
    rel = colorize(f"关系:{stage_text}", FG_MAGENTA)
    aff = colorize(f"好感:{actor.affection}", FG_CYAN)
    trust = colorize(f"信赖:{actor.trust}", FG_GREEN)
    obed = colorize(f"服从:{actor.obedience}", FG_YELLOW)

    print(f"  {name}  {rel}  {aff}  {trust}  {obed}")

    # Tags (only show status tags, not detailed marks)
    tags: list[str] = []
    if actor.is_following:
        tags.append(colorize("👣同行", FG_CYAN))
    if actor.is_on_date:
        tags.append(colorize("💖约会", FG_MAGENTA))
    if tags:
        print("  " + "  ".join(tags))

    print()


# ── Zone ③ : Vital bars + PALAM grid ─────────────────────────────

def _render_vitals(actor: CharacterState) -> None:
    """Render stamina/spirit bars and PALAM parameter grid."""
    # ── Vital bars ──
    stamina = actor.stats.base.get("stamina")
    spirit = actor.stats.base.get("spirit")
    reason = actor.stats.base.get("reason")

    max_sta = 2000  # from maxbase.toml defaults
    max_spi = 1500
    max_reason = 1000

    sta_label = cjk_ljust("体力", 6)
    spi_label = cjk_ljust("気力", 6)
    rsn_label = cjk_ljust("理性", 6)

    print(f"  {colorize(sta_label, FG_GRAY)}  {bar(stamina, max_sta, 20, FG_GREEN)}")
    print(f"  {colorize(spi_label, FG_GRAY)}  {bar(spirit, max_spi, 20, FG_CYAN)}")
    print(f"  {colorize(rsn_label, FG_GRAY)}  {_reason_stars(reason, max_reason)}")
    print()

    # ── PALAM grid (4 columns, with level + mini bar) ──
    palam_axes = [
        ("快C", "pleasure_c"),
        ("快V", "pleasure_v"),
        ("快A", "pleasure_a"),
        ("快B", "pleasure_b"),
        ("快M", "pleasure_m"),
        ("润滑", "lubrication"),
        ("恭顺", "obedience"),
        ("情欲", "lust"),
        ("屈服", "submission"),
        ("习得", "mastery"),
        ("恥情", "shame"),
        ("苦痛", "pain"),
        ("恐怖", "fear"),
        ("好意", "favor"),
        ("优越", "superiority"),
        ("反感", "disgust"),
    ]

    cols = 4
    col_width = 18
    row_items: list[str] = []
    for label, key in palam_axes:
        val = actor.stats.palam.get(key)
        cell = _palam_cell(label, val, col_width)
        row_items.append(cell)

    for i in range(0, len(row_items), cols):
        chunk = row_items[i:i + cols]
        print("  " + "".join(chunk))
    print()


# ── Zone ④ : Look + Portrait placeholder ──────────────────────────

def _render_look(actor: CharacterState) -> None:
    """Render look / clothing display and portrait placeholder."""
    print(colorize("▼[-] [Look]──────────[显示设定]", FG_GRAY))
    # Clothing info can be expanded later when clothing system is added
    print()

    # ── Portrait placeholder ──
    # Reserve visual space for the character sprite / portrait.
    # When image assets are added, this area will display them.
    portrait_height = 8
    tw = terminal_width()
    portrait_width = min(30, tw // 3)
    left_pad = (tw - portrait_width) // 2

    border_top = " " * left_pad + colorize("┌" + "─" * (portrait_width - 2) + "┐", FG_DARK_GRAY)
    border_bot = " " * left_pad + colorize("└" + "─" * (portrait_width - 2) + "┘", FG_DARK_GRAY)
    print(border_top)
    for i in range(portrait_height):
        if i == portrait_height // 2:
            label = f"[{actor.display_name}]"
            inner = cjk_center(label, portrait_width - 2)
            print(" " * left_pad + colorize("│", FG_DARK_GRAY) + colorize(inner, FG_DARK_GRAY) + colorize("│", FG_DARK_GRAY))
        elif i == portrait_height // 2 + 1:
            label2 = "(立绘位置)"
            inner2 = cjk_center(label2, portrait_width - 2)
            print(" " * left_pad + colorize("│", FG_DARK_GRAY) + colorize(inner2, FG_DARK_GRAY) + colorize("│", FG_DARK_GRAY))
        else:
            print(" " * left_pad + colorize("│" + " " * (portrait_width - 2) + "│", FG_DARK_GRAY))
    print(border_bot)
    print()


# ── Zone ⑤ : Message log ──────────────────────────────────────────

def _render_messages(messages: list[str]) -> None:
    """Render the dialogue / action result log."""
    if not messages:
        return
    print(separator("─"))
    for line in messages:
        print(f"  {colorize(line, FG_WHITE)}")
    print()


# ── Zone ⑥ : Command menu ─────────────────────────────────────────

# Map game categories to display groups
_ACT_CATEGORIES = ("daily", "work", "follow", "date", "intimacy", "recovery")
_ACT_LABELS = {
    "daily": "日常",
    "work": "工作",
    "follow": "同行",
    "date": "约会",
    "intimacy": "亲密",
    "recovery": "恢复",
}

_EX_CATEGORIES = ("move", "system")
_EX_LABELS = {
    "move": "移动",
    "system": "系统",
}


def _append_destination_menu(
    menu: dict[str, list[tuple[str, str, str | None]]],
    destinations: list[object],
) -> None:
    """Populate the move menu with reachable destinations grouped by area.

    Structured rendering: label contains area/cost metadata but the
    action remains ``("move", dest_key)`` so the execution layer is
    unchanged.  Future UI renderers can parse the MovePlan directly
    instead of the label string.
    """
    from eral.systems.navigation import MovePlan  # avoid circular at module level

    # Group by area
    by_area: dict[str, list[MovePlan]] = {}
    for plan in destinations:
        area_label = plan.destination_area_name or "其他区域"
        by_area.setdefault(area_label, []).append(plan)

    for area_name, plans in by_area.items():
        # Area header (selectable but does nothing — acts as visual separator)
        menu["move"].append((f"── {area_name} ──", "move_header", area_name))
        for plan in plans:
            cost_label = f"{plan.total_cost_minutes}分钟"
            label = f"  {plan.destination_name}（{cost_label}）"
            menu["move"].append((label, "move", plan.destination_key))


def _build_menu(
    app: Application,
    world: WorldState,
    selected_actor_key: str | None = None,
    roster_page_index: int = 0,
    page_size: int = 10,
) -> dict[str, list[tuple[str, str, str | None]]]:
    """Return categorized actions.

    Returns a dict from internal category key to list of
    (display_label, action_type, param) tuples.
    """
    menu: dict[str, list[tuple[str, str, str | None]]] = {
        "daily": [],
        "work": [],
        "follow": [],
        "date": [],
        "intimacy": [],
        "recovery": [],
        "move": [],
        "system": [],
    }

    location_key = world.active_location.key
    selected_actor_key = _coerce_selected_actor_key(app, location_key, selected_actor_key)
    selected_actor = _selected_present_actor(app, location_key, selected_actor_key)
    if selected_actor is not None:
        roster_page_index = _page_index_for_actor(
            app,
            location_key,
            selected_actor.key,
            page_size=page_size,
        )
    else:
        roster_page_index = _normalize_roster_page_index(
            app,
            location_key,
            roster_page_index,
            page_size=page_size,
        )

    # Actor commands — only expose commands for the selected actor.
    if selected_actor is not None:
        actor_commands = app.command_service.available_commands_for_actor(
            world,
            selected_actor.key,
        )
        for cmd in actor_commands:
            cat = cmd.category if cmd.category in menu else "daily"
            label = f"{cmd.display_name}→{selected_actor.display_name}"
            menu[cat].append((label, "command", f"{selected_actor.key}:{cmd.key}"))

    # Navigation — show all reachable destinations grouped by area
    destinations = app.navigation_service.available_destinations(world)
    _append_destination_menu(menu, destinations)

    page_actors = _paginate_present_characters(
        app,
        location_key,
        page_index=roster_page_index,
        page_size=page_size,
    )
    for actor in page_actors:
        if actor.key == selected_actor_key:
            continue
        menu["system"].append((f"选中 {actor.display_name}", "select_actor", actor.key))

    page_count = _roster_page_count(app, location_key, page_size=page_size)
    if page_count > 1 and roster_page_index > 0:
        menu["system"].append(("上一页舰娘", "page_roster", "prev"))
    if page_count > 1 and roster_page_index + 1 < page_count:
        menu["system"].append(("下一页舰娘", "page_roster", "next"))

    # Time & generic
    present_actor_keys = {a.key for a in page_actors}
    if "akashi" in present_actor_keys:
        menu["system"].append(("进入明石的杂货店", "shop", "general_shop"))
    if "shiranui" in present_actor_keys:
        menu["system"].append(("进入不知火的时装屋", "shop", "skin_shop"))
    menu["system"].append(("切换企业皮肤", "skin_wardrobe", "enterprise"))
    menu["system"].append(("查看日历", "calendar", None))
    menu["system"].append(("等待(推进时段)", "wait", None))
    menu["system"].append(("能力显示", "status", None))
    menu["system"].append(("保存当前进度", "save", None))
    if app.save_service.has_quicksave():
        menu["system"].append(("读取快速存档", "load", None))
    menu["system"].append(("退出游戏", "quit", None))

    return menu


def _render_command_menu(
    menu: dict[str, list[tuple[str, str, str | None]]],
    active_act_tab: int = 0,
) -> list[tuple[str, str, str | None]]:
    """Render the command menu and return the flat indexed list.

    *active_act_tab* selects which Act_COM category is expanded
    (index into ``_ACT_CATEGORIES``). Only that tab's commands are
    rendered; the rest are hidden to reduce screen clutter.
    """
    tw = terminal_width()
    flat: list[tuple[str, str, str | None]] = []
    current_idx = 1

    # ── Act_COM row ──
    act_has_items = any(menu.get(c) for c in _ACT_CATEGORIES)
    if act_has_items:
        tabs = []
        for i, cat in enumerate(_ACT_CATEGORIES):
            label = _ACT_LABELS.get(cat, cat)
            if i == active_act_tab and menu.get(cat):
                tabs.append(colorize(f"【{label}】", FG_CYAN, bold=True))
            elif menu.get(cat):
                tabs.append(colorize(f"[{label}]", FG_GRAY))
            else:
                tabs.append(colorize(f"[{label}]", FG_DARK_GRAY))
        tab_line = colorize("Act_COM", FG_BLUE, bold=True) + " ═ " + "─".join(tabs)
        print(tab_line)

        # Render commands for the active tab only
        active_cat = _ACT_CATEGORIES[active_act_tab]
        items = menu.get(active_cat, [])
        if items:
            col_width = 22
            cols = max(1, tw // col_width)
            row_buf: list[str] = []
            for label, action_type, param in items:
                cell_text = f"{label}[{current_idx}]"
                cell = cjk_ljust(cell_text, col_width)
                cell = colorize(cell, FG_WHITE)
                row_buf.append(cell)
                flat.append((label, action_type, param))
                current_idx += 1

                if len(row_buf) == cols:
                    print("  " + "".join(row_buf))
                    row_buf = []
            if row_buf:
                print("  " + "".join(row_buf))
        else:
            print(colorize("  （当前分类无可用指令）", FG_DARK_GRAY))

        print(colorize("  [<] 上一个分类  [>] 下一个分类", FG_DARK_GRAY))
        print()

    # ── Ex_COM row ──
    ex_has_items = any(menu.get(c) for c in _EX_CATEGORIES)
    if ex_has_items:
        tabs = []
        for cat in _EX_CATEGORIES:
            label = _EX_LABELS.get(cat, cat)
            if menu.get(cat):
                tabs.append(colorize(f"[{label}]", FG_CYAN))
            else:
                tabs.append(colorize(f"[{label}]", FG_DARK_GRAY))
        tab_line = colorize("Ex_COM", FG_BLUE, bold=True) + "  ═ " + "─".join(tabs)
        print(tab_line)

        col_width = 22
        cols = max(1, tw // col_width)
        row_buf = []

        for cat in _EX_CATEGORIES:
            items = menu.get(cat, [])
            for label, action_type, param in items:
                if action_type == "move_header":
                    # Area separator — not selectable
                    if row_buf:
                        print("  " + "".join(row_buf))
                        row_buf = []
                    print(colorize(f"  {label}", FG_CYAN))
                    continue
                cell_text = f"{label}[{current_idx}]"
                cell = cjk_ljust(cell_text, col_width)
                cell = colorize(cell, FG_WHITE)
                row_buf.append(cell)
                flat.append((label, action_type, param))
                current_idx += 1

                if len(row_buf) == cols:
                    print("  " + "".join(row_buf))
                    row_buf = []

        if row_buf:
            print("  " + "".join(row_buf))

    return flat


def _open_shopfront(
    app: Application,
    world: WorldState,
    shopfront_key: str,
    *,
    input_fn: Callable[[str], str] = input,
) -> list[str]:
    """Run a purchase prompt, dispatching to skin or item logic by shopfront type."""

    if shopfront_key == "skin_shop":
        return _open_skin_shop_by_type(app, world, input_fn=input_fn)

    shopfront = app.shop_service.shopfront_definitions.get(shopfront_key)
    if shopfront is None:
        return [colorize("商店不存在。", FG_RED)]

    goods = app.shop_service.list_items(shopfront_key)
    if not goods:
        return [colorize(f"{shopfront.display_name}当前暂无可购买商品。", FG_YELLOW)]

    clear_screen()
    print(header_separator("═", terminal_width()))
    print(colorize(f"  {shopfront.display_name}", FG_CYAN, bold=True))
    print(colorize(f"  当前资金: {world.personal_funds}", FG_YELLOW))
    print(header_separator("═", terminal_width()))
    for index, item in enumerate(goods, start=1):
        print(colorize(f"  [{index}] {item.display_name}  ￥{item.price}", FG_WHITE))
        print(colorize(f"      {item.description}", FG_DARK_GRAY))
    print(colorize("  [0] 返回", FG_GRAY))

    raw = input_fn(colorize("  请选择商品 > ", FG_WHITE)).strip()
    if not raw or raw == "0":
        return [colorize(f"离开了{shopfront.display_name}。", FG_GRAY)]

    try:
        choice = int(raw)
    except ValueError:
        return [colorize("商店选项无效。", FG_RED)]

    if choice < 1 or choice > len(goods):
        return [colorize("商店选项无效。", FG_RED)]

    item = goods[choice - 1]
    result = app.shop_service.purchase(world, shopfront_key, item.key)
    if not result.success:
        return [colorize(f"{shopfront.display_name}购买失败：{result.reason}", FG_RED)]
    return [
        colorize(
            f"在{shopfront.display_name}购买了 {item.display_name} x{result.count}。",
            FG_GREEN,
        )
    ]


def _open_skin_shop_by_type(
    app: Application,
    world: WorldState,
    *,
    input_fn: Callable[[str], str] = input,
) -> list[str]:
    """Run a purchase prompt for skins via the unified shop entry point."""

    # Use the first available actor as the skin target (enterprise default)
    actor_key = "enterprise"
    actor = next((character for character in world.characters if character.key == actor_key), None)
    if actor is None:
        return [colorize("目标角色不存在。", FG_RED)]

    goods = app.skin_service.visible_shop_skins(actor_key)
    if not goods:
        return [colorize(f"{actor.display_name}当前没有可购买皮肤。", FG_YELLOW)]

    clear_screen()
    print(header_separator("═", terminal_width()))
    print(colorize(f"  {actor.display_name}皮肤商店", FG_CYAN, bold=True))
    print(colorize(f"  当前资金: {world.personal_funds}", FG_YELLOW))
    print(header_separator("═", terminal_width()))
    preview_lines = [colorize("可购买皮肤：", FG_WHITE)]
    for index, skin in enumerate(goods, start=1):
        line = f"  [{index}] {skin.display_name}  ￥{skin.price}"
        print(colorize(line, FG_WHITE))
        preview_lines.append(line)
    print(colorize("  [0] 返回", FG_GRAY))

    raw = input_fn(colorize("  请选择皮肤 > ", FG_WHITE)).strip()
    if not raw or raw == "0":
        return preview_lines + [colorize(f"离开了{actor.display_name}皮肤商店。", FG_GRAY)]

    try:
        choice = int(raw)
    except ValueError:
        return [colorize("皮肤商店选项无效。", FG_RED)]
    if choice < 1 or choice > len(goods):
        return [colorize("皮肤商店选项无效。", FG_RED)]

    skin = goods[choice - 1]
    success, reason = app.skin_service.purchase_skin(world, actor, skin.key)
    if not success:
        return [colorize(f"{actor.display_name}皮肤购买失败：{reason}", FG_RED)]
    return [colorize(f"为{actor.display_name}购买了 {skin.display_name}。", FG_GREEN)]


def _open_skin_wardrobe(
    app: Application,
    world: WorldState,
    actor_key: str,
    *,
    input_fn: Callable[[str], str] = input,
) -> list[str]:
    """Run a minimal owned-skin equip prompt for one actor."""

    actor = next((character for character in world.characters if character.key == actor_key), None)
    if actor is None:
        return [colorize("目标角色不存在。", FG_RED)]

    owned = [
        app.skin_service.skin_definitions[skin_key]
        for skin_key in sorted(actor.owned_skins)
        if skin_key in app.skin_service.skin_definitions
    ]
    if not owned:
        return [colorize(f"{actor.display_name}当前没有可切换皮肤。", FG_YELLOW)]

    clear_screen()
    print(header_separator("═", terminal_width()))
    print(colorize(f"  {actor.display_name}衣柜", FG_CYAN, bold=True))
    print(header_separator("═", terminal_width()))
    for index, skin in enumerate(owned, start=1):
        current = "（当前）" if actor.equipped_skin_key == skin.key else ""
        print(colorize(f"  [{index}] {skin.display_name} {current}", FG_WHITE))
    print(colorize("  [0] 返回", FG_GRAY))

    raw = input_fn(colorize("  请选择皮肤 > ", FG_WHITE)).strip()
    if not raw or raw == "0":
        return [colorize(f"离开了{actor.display_name}衣柜。", FG_GRAY)]

    try:
        choice = int(raw)
    except ValueError:
        return [colorize("衣柜选项无效。", FG_RED)]
    if choice < 1 or choice > len(owned):
        return [colorize("衣柜选项无效。", FG_RED)]

    skin = owned[choice - 1]
    actor.equip_skin(skin.key)
    actor.clear_removed_slots()
    return [colorize(f"{actor.display_name}换上了 {skin.display_name}。", FG_GREEN)]


def _appearance_summary(app: Application, actor: CharacterState) -> str:
    """Build a compact summary of the equipped skin and its slot values."""

    skin_key = actor.equipped_skin_key
    if skin_key is None:
        return "当前皮肤: 未知"
    skin = app.skin_service.skin_definitions.get(skin_key)
    appearance = app.skin_service.appearance_for_actor(actor)
    if skin is None or appearance is None:
        return "当前皮肤: 未知"

    slot_parts: list[str] = []
    for slot_label, slot_key in _CLOTHING_SLOTS:
        value = appearance.slots.get(slot_key, "----")
        if slot_key in actor.removed_slots:
            value = "(已脱除)"
        slot_parts.append(f"{slot_label}:{value}")
    return f"当前皮肤: {skin.display_name} | " + " ".join(slot_parts)


def _present_characters(app: Application, location_key: str) -> tuple[CharacterState, ...]:
    """Return present characters for one location using distribution rules."""

    return app.distribution_service.present_characters(app.world, location_key)


def _auto_select_actor_key(app: Application, location_key: str) -> str | None:
    """Return the highest-priority actor key for one location."""

    present = _present_characters(app, location_key)
    return present[0].key if present else None


def _paginate_present_characters(
    app: Application,
    location_key: str,
    page_index: int = 0,
    page_size: int = 10,
) -> tuple[CharacterState, ...]:
    """Return one page of present characters for a location."""

    present = _present_characters(app, location_key)
    start = page_index * page_size
    end = start + page_size
    return present[start:end]


def _coerce_selected_actor_key(
    app: Application,
    location_key: str,
    selected_actor_key: str | None,
) -> str | None:
    """Keep the current selection if it still exists, else auto-select."""

    present = _present_characters(app, location_key)
    if not present:
        return None
    if selected_actor_key and any(actor.key == selected_actor_key for actor in present):
        return selected_actor_key
    return present[0].key


def _roster_page_count(
    app: Application,
    location_key: str,
    page_size: int = 10,
) -> int:
    """Return the total number of pages for one location roster."""

    if page_size <= 0:
        raise ValueError("page_size must be positive")
    present_count = len(_present_characters(app, location_key))
    if present_count == 0:
        return 0
    return (present_count - 1) // page_size + 1


def _page_index_for_actor(
    app: Application,
    location_key: str,
    actor_key: str,
    page_size: int = 10,
) -> int:
    """Return the page index containing one actor in the present roster."""

    if page_size <= 0:
        raise ValueError("page_size must be positive")
    present = _present_characters(app, location_key)
    for index, actor in enumerate(present):
        if actor.key == actor_key:
            return index // page_size
    return 0


def _normalize_roster_page_index(
    app: Application,
    location_key: str,
    page_index: int,
    page_size: int = 10,
) -> int:
    """Clamp a page index into the valid roster range."""

    page_count = _roster_page_count(app, location_key, page_size=page_size)
    if page_count <= 0:
        return 0
    return max(0, min(page_index, page_count - 1))


def _selected_present_actor(
    app: Application,
    location_key: str,
    selected_actor_key: str | None,
) -> CharacterState | None:
    """Return the currently selected actor when one is present."""

    selected_actor_key = _coerce_selected_actor_key(app, location_key, selected_actor_key)
    if selected_actor_key is None:
        return None
    return next(
        actor
        for actor in _present_characters(app, location_key)
        if actor.key == selected_actor_key
    )


def _render_calendar_preview(app: Application, world: WorldState) -> list[str]:
    """Return a compact preview of nearby calendar days and work schedules."""

    lines = ["日历预览（前后2天）"]
    for view in app.calendar_view_service.day_views(world, span_before=2, span_after=2):
        header = f"{view.month}月{view.day}日 {weekday_label(view.weekday)} {view.season}"
        if view.festival_labels:
            header += " | 节日:" + "、".join(view.festival_labels)
        lines.append(header)
        if view.schedule_entries:
            for entry in view.schedule_entries:
                lines.append(
                    f"  {entry.time_range} {entry.actor_name} / {entry.location_name} / {entry.work_label}"
                )
        else:
            lines.append("  （无工作安排）")
    return lines


def _show_calendar(app: Application, world: WorldState) -> list[str]:
    """Render the read-only calendar preview and return its lines."""

    lines = _render_calendar_preview(app, world)
    clear_screen()
    print(header_separator("═", terminal_width()))
    for line in lines:
        print(colorize(f"  {line}", FG_WHITE if not line.startswith("  ") else FG_GRAY))
    print(header_separator("═", terminal_width()))
    return lines


# ── Zone ② bis : Scene context (multiple characters) ──────────────

def _render_scene_context(
    app: Application,
    world: WorldState,
    selected_actor_key: str | None,
    roster_page_index: int = 0,
    page_size: int = 10,
) -> None:
    """Render the current location roster plus the selected target's detail."""

    location_key = world.active_location.key
    present = _present_characters(app, location_key)
    if not present:
        print(colorize("  （周围没有人）", FG_DARK_GRAY))
        print()
        return

    selected_actor_key = _coerce_selected_actor_key(app, location_key, selected_actor_key)
    if selected_actor_key is None:
        print(colorize("  （周围没有人）", FG_DARK_GRAY))
        print()
        return

    roster_page_index = _page_index_for_actor(
        app,
        location_key,
        selected_actor_key,
        page_size=page_size,
    )
    page_actors = _paginate_present_characters(
        app,
        location_key,
        page_index=roster_page_index,
        page_size=page_size,
    )
    page_count = _roster_page_count(app, location_key, page_size=page_size)
    selected_actor = next(actor for actor in present if actor.key == selected_actor_key)

    print(
        colorize(
            (
                f"▼[在场舰娘 {len(present)} 人 / "
                f"第 {roster_page_index + 1} 页 / 共 {page_count} 页 / "
                f"当前目标: {selected_actor.display_name}]"
            ),
            FG_GRAY,
        ),
    )

    for actor in page_actors:
        tags: list[str] = []
        if actor.is_following:
            tags.append("同行")
        if actor.is_on_date:
            tags.append("约会")
        tag_str = " ".join(tags)
        stage_text = (
            actor.relationship_stage.display_name
            if actor.relationship_stage
            else "陌生"
        )
        is_selected = actor.key == selected_actor_key
        marker = ">" if is_selected else " "
        name_part = colorize(
            f"{marker}[{actor.display_name}]",
            FG_CYAN if is_selected else FG_WHITE,
            bold=is_selected,
        )
        stats_part = (
            f"{colorize(f'好感:{actor.affection}', FG_CYAN)}  "
            f"{colorize(f'信赖:{actor.trust}', FG_GREEN)}  "
            f"{colorize(f'关系:{stage_text}', FG_MAGENTA)}"
        )
        suffix = f"  {colorize(tag_str, FG_ORANGE)}" if tag_str else ""
        print(f"  {cjk_ljust(name_part, 16)} {stats_part}{suffix}")
    print()

    if page_count > 1:
        print(colorize("  可在系统区切换舰娘或翻页。", FG_DARK_GRAY))
        print()

    # Show detailed view for the selected visible character.
    print(separator("─"))
    _render_target_status(selected_actor)
    _render_vitals(selected_actor)
    _render_look(selected_actor)


# ── Zone ⑦ : Ability display (tabbed status screen) ───────────────

_ABILITY_TABS = (
    ("服装&能力", "clothing_ability"),
    ("经验", "exp_jewel"),
    ("个人情报", "personal"),
    ("个人好恶", "likes"),
    ("身体情报", "body"),
    ("陷落状态", "fallen"),
)


def _render_ability_header(actor: CharacterState) -> None:
    """Render the character header block for the ability display."""
    tw = terminal_width()
    print(header_separator("═", tw))

    # Name line
    name = colorize(f"■ {actor.display_name}", FG_WHITE, bold=True)
    stage_text = actor.relationship_stage.display_name if actor.relationship_stage else "陌生"
    aff = colorize(f"好感度: {actor.affection}", FG_CYAN)
    trust = colorize(f"信赖度: {actor.trust}", FG_GREEN)
    obed = colorize(f"服从: {actor.obedience}", FG_YELLOW)
    id_str = colorize(f"#ID:{actor.key}", FG_DARK_GRAY)
    print(f"  {name}  ({aff}  {trust}  {obed})  {id_str}")

    # Vital bars
    stamina = actor.stats.base.get("stamina")
    spirit = actor.stats.base.get("spirit")
    max_sta = 2000
    max_spi = 1500
    sta_label = colorize("体力", FG_GRAY)
    spi_label = colorize("气力", FG_GRAY)
    print(f"  {sta_label} {bar(stamina, max_sta, 20, FG_GREEN)}    {spi_label} {bar(spirit, max_spi, 20, FG_CYAN)}")
    print(header_separator("═", tw))


def _render_tab_bar(active_index: int) -> None:
    """Render the bottom tab bar with the active tab highlighted."""
    parts: list[str] = []
    for i, (label, _) in enumerate(_ABILITY_TABS):
        if i == active_index:
            parts.append(colorize(f"【{label}】", FG_CYAN, bold=True))
        else:
            parts.append(colorize(f"[{label}]", FG_GRAY))
    print("  " + "  ".join(parts))


def _render_tab_clothing_ability(actor: CharacterState, app: Application) -> None:
    """Tab 1: 服装 & 能力."""
    from eral.content.tw_axis_registry import AxisFamily

    tw = terminal_width()

    # ── Clothing section ──
    print(colorize("□ 服装 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))
    print(colorize(f"  {_appearance_summary(app, actor)}", FG_GRAY))
    skin_tags = _active_skin_tags(app, actor)
    if skin_tags:
        print("  " + colorize("标签: ", FG_DARK_GRAY) + colorize(" ".join(f"#{t}" for t in skin_tags), FG_CYAN))
    print()
    col_width = 20
    cols = max(1, tw // col_width)
    row_buf: list[str] = []
    appearance = app.skin_service.appearance_for_actor(actor)
    slot_values = appearance.slots if appearance is not None else {}
    removed_slots = set(actor.removed_slots)
    for slot_name, slot_key in _CLOTHING_SLOTS:
        value = slot_values.get(slot_key, "----")
        if slot_key in removed_slots:
            value = "(已脱除)"
        color = FG_DARK_GRAY if value == "----" else FG_WHITE
        cell = colorize(cjk_ljust(f"  {slot_name}: {value}", col_width), color)
        row_buf.append(cell)
        if len(row_buf) == cols:
            print("".join(row_buf))
            row_buf = []
    if row_buf:
        print("".join(row_buf))
    print()

    # ── Ability section ──
    print(colorize("□ 能力 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))

    # Read ABL entries from registry, group by section
    abl_entries = app.tw_axes.family_entries(AxisFamily.ABL)
    sections: dict[str, list[tuple[str, int, int]]] = {}
    for entry in abl_entries:
        sec = entry.section or "其他"
        if sec not in sections:
            sections[sec] = []
        sections[sec].append((entry.label, entry.era_index, actor.stats.compat.abl.get(entry.era_index)))

    col_width = 18
    cols = max(1, tw // col_width)
    for sec_key in _ABL_SECTION_ORDER:
        items = sections.get(sec_key)
        if not items:
            continue
        sec_name = _ABL_SECTION_NAMES.get(sec_key, sec_key)
        print(colorize(f"  ── {sec_name} ──", FG_GRAY))
        row_buf = []
        for label, _idx, val in items:
            cell_text = f"{label}: {val}"
            color = FG_YELLOW if val > 0 else FG_DARK_GRAY
            row_buf.append(colorize(cjk_ljust(cell_text, col_width), color))
            if len(row_buf) == cols:
                print("  " + "".join(row_buf))
                row_buf = []
        if row_buf:
            print("  " + "".join(row_buf))
    print()

    # ── Talent section ──
    talent_entries = app.tw_axes.family_entries(AxisFamily.TALENT)
    active: dict[str, list[str]] = {}
    for entry in talent_entries:
        if actor.stats.compat.talent.get(entry.era_index) > 0:
            group = _talent_group_name(entry.era_index)
            active.setdefault(group, []).append(entry.label)

    if active:
        print(colorize("□ 素质 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))
        col_width = 16
        cols = max(1, (tw - 4) // col_width)
        for _lo, _hi, group_name in _TALENT_GROUPS:
            items = active.get(group_name)
            if not items:
                continue
            print(f"  {colorize(f'[{group_name}]', FG_DARK_GRAY)}")
            row_buf = []
            for label in items:
                row_buf.append(colorize(cjk_ljust(label, col_width), FG_CYAN))
                if len(row_buf) == cols:
                    print("    " + "".join(row_buf))
                    row_buf = []
            if row_buf:
                print("    " + "".join(row_buf))
        print()


def _active_skin_tags(app: Application, actor: CharacterState) -> tuple[str, ...]:
    """Return tags of the currently equipped skin, if any."""
    equipped_key = actor.equipped_skin_key
    if not equipped_key:
        return ()
    for skin in app.skin_definitions:
        if skin.key == equipped_key:
            return tuple(skin.tags)
    return ()


def _render_tab_exp_jewel(actor: CharacterState, app: Application) -> None:
    """Tab 2: 经验 & 特殊经验."""
    from eral.content.tw_axis_registry import AxisFamily

    tw = terminal_width()

    # ── Experience section ──
    print(colorize("□ 经验 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))

    # Build label map: ABL index → label from registry
    abl_entries = app.tw_axes.family_entries(AxisFamily.ABL)
    abl_labels: dict[int, str] = {e.era_index: e.label for e in abl_entries}

    if actor.stats.abl_exp:
        # Group exp by ABL section
        abl_sections: dict[str, str] = {e.era_index: (e.section or "其他") for e in abl_entries}
        grouped: dict[str, list[tuple[str, int]]] = {}
        for idx, exp_val in sorted(actor.stats.abl_exp.items()):
            label = abl_labels.get(idx, f"ABL[{idx}]")
            sec = abl_sections.get(idx, "其他")
            grouped.setdefault(sec, []).append((f"{label}经验", exp_val))

        col_width = 20
        cols = max(1, tw // col_width)
        for sec_key in _ABL_SECTION_ORDER:
            items = grouped.get(sec_key)
            if not items:
                continue
            sec_name = _ABL_SECTION_NAMES.get(sec_key, sec_key)
            print(colorize(f"  ── {sec_name} ──", FG_GRAY))
            row_buf: list[str] = []
            for label, exp_val in items:
                cell_text = f"{label}: {exp_val}"
                color = FG_YELLOW if exp_val > 0 else FG_DARK_GRAY
                row_buf.append(colorize(cjk_ljust(cell_text, col_width), color))
                if len(row_buf) == cols:
                    print("  " + "".join(row_buf))
                    row_buf = []
            if row_buf:
                print("  " + "".join(row_buf))
    else:
        print(colorize("  （暂无经验数据）", FG_DARK_GRAY))
    print()

    # ── Special counters (debug/progress stats) ──
    print(colorize("□ 特殊经验 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))

    date_count = actor.memories.get("evt:start_date", 0) + actor.memories.get("cmd:start_date", 0)
    training_step = actor.get_condition("train_total_steps")
    orgasm_count = actor.get_condition("total_orgasm_count")
    counter_kiss = actor.memories.get("evt:counter_kiss", 0)
    counter_request = actor.memories.get("evt:counter_request", 0)
    ejaculate_inside = actor.memories.get("evt:player_ejaculation_inside", 0)
    ejaculate_outside = actor.memories.get("evt:player_ejaculation_outside", 0)
    gift_given = sum(v for k, v in actor.memories.items() if k.startswith("gift:"))

    rows = [
        ("总调教次数", training_step),
        ("总高潮次数", orgasm_count),
        ("主动亲吻次数", counter_kiss),
        ("主动请求次数", counter_request),
        ("总约会次数", date_count),
        ("内射次数", ejaculate_inside),
        ("外射次数", ejaculate_outside),
        ("收礼次数", gift_given),
    ]

    col_width = 20
    cols = max(1, tw // col_width)
    row_buf: list[str] = []
    for label, val in rows:
        color = FG_YELLOW if val > 0 else FG_DARK_GRAY
        row_buf.append(colorize(cjk_ljust(f"  {label}: {val}", col_width), color))
        if len(row_buf) == cols:
            print("".join(row_buf))
            row_buf = []
    if row_buf:
        print("".join(row_buf))
    print()

    # ── Development axes ──
    dev_keys = [
        ("身体开发", "train_body"),
        ("口部开发", "train_mouth"),
        ("胸部开发", "train_chest"),
        ("阴蒂开发", "train_clit"),
        ("膣开发", "train_v"),
        ("肛开发", "train_a"),
    ]
    has_dev = any(actor.get_condition(k) > 0 for _, k in dev_keys)
    if has_dev:
        print(colorize("□ 开发度 □", FG_WHITE, bold=True) + colorize("─" * (tw - 12), FG_DARK_GRAY))
        row_buf = []
        for label, key in dev_keys:
            val = actor.get_condition(key)
            color = FG_YELLOW if val > 0 else FG_DARK_GRAY
            row_buf.append(colorize(cjk_ljust(f"  {label}: {val}", col_width), color))
            if len(row_buf) == cols:
                print("".join(row_buf))
                row_buf = []
        if row_buf:
            print("".join(row_buf))
        print()


def _render_tab_personal(actor: CharacterState, app: Application) -> None:
    """Tab 3: 个人情报."""
    from eral.ui import personal_info as pi

    tw = terminal_width()
    print(colorize("□ 个人情报 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))

    stage_text = actor.relationship_stage.display_name if actor.relationship_stage else "陌生"
    print(f"  {colorize('关系阶段:', FG_GRAY)} {colorize(stage_text, FG_MAGENTA, bold=True)}")
    print(f"  {colorize('好感度:', FG_GRAY)}   {colorize(str(actor.affection), FG_CYAN)}")
    print(f"  {colorize('信赖度:', FG_GRAY)}   {colorize(str(actor.trust), FG_GREEN)}")
    print(f"  {colorize('服从度:', FG_GRAY)}   {colorize(str(actor.obedience), FG_YELLOW)}")
    print()

    definition = next(
        (d for d in app.roster if d.key == actor.key), None
    )
    if definition is not None:
        personality = pi.personality_from_tags(definition.tags)
        hours = pi.activity_hours(definition)
        freq_areas = pi.frequent_areas(definition, app.port_map)
        home_disp = pi.home_location_display(definition, app.port_map)
        faction = definition.faction_key or "—"

        print(f"  {colorize('性格:', FG_GRAY)}       {colorize(personality, FG_WHITE)}")
        print(f"  {colorize('活动时间带:', FG_GRAY)} {colorize(hours, FG_WHITE)}")
        print(f"  {colorize('常去区域:', FG_GRAY)}   {colorize(freq_areas, FG_WHITE)}")
        print(f"  {colorize('自宅位置:', FG_GRAY)}   {colorize(home_disp, FG_WHITE)}")
        print(f"  {colorize('所属阵营:', FG_GRAY)}   {colorize(faction, FG_WHITE)}")

        entries = pi.work_entries(actor.key, app.work_schedules, app.port_map)
        if entries:
            print()
            print(colorize("  ── 工作情报 ──", FG_GRAY))
            for entry in entries:
                print(
                    f"    {colorize(entry.work_label, FG_CYAN)}  "
                    f"{entry.days}  {entry.time_range}  "
                    f"@ {colorize(entry.location_display, FG_WHITE)}"
                )
        print()

    # State tags
    tags: list[str] = []
    if actor.is_following:
        tags.append(colorize("同行", FG_CYAN))
    if actor.is_on_date:
        tags.append(colorize("约会", FG_MAGENTA))
    if actor.is_on_commission:
        tags.append(colorize("委托中", FG_ORANGE))
    if tags:
        print(f"  {colorize('状态标签:', FG_GRAY)} {' '.join(tags)}")
        print()

    # Marks
    active_marks = [(k, v) for k, v in actor.marks.items() if v > 0]
    if active_marks:
        print(colorize("  ── 印记 ──", FG_GRAY))
        for mark_key, mark_val in active_marks:
            print(f"    {colorize(mark_key, FG_ORANGE)}: Lv.{mark_val}")
        print()

    # Milestones (first-occurrence history)
    milestones = pi.milestones(actor)
    if milestones:
        print(colorize("  ── 里程碑 ──", FG_GRAY))
        for m in milestones:
            print(f"    {colorize(m.label, FG_MAGENTA)}: 第 {m.day} 日")
        print()

    # Inter-character relationships — placeholder for now
    print(colorize("  ── 人际关系 ──", FG_GRAY))
    print(colorize("    （角色间亲密度系统尚未实装）", FG_DARK_GRAY))
    print()


def _render_tab_body(actor: CharacterState, app: Application) -> None:
    """Tab 4: 身体情报 — TW-style two-column body part panel."""
    from eral.content.tw_axis_registry import AxisFamily
    from eral.ui import body_info as bi

    tw = terminal_width()
    print(colorize("□ 身体情报 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))
    print()

    outer = bi.outer_parts(actor)
    inner = bi.inner_parts(actor)

    # Two-column rendering
    col_width = max(30, (tw - 4) // 2)

    def format_part(part: bi.BodyPartInfo, width: int) -> list[str]:
        lines: list[str] = []
        header = colorize(f"——【{part.label}】——", FG_CYAN)
        lines.append(cjk_ljust(header, width))
        if part.tags:
            tag_line = " ".join(f"【{t}】" for t in part.tags)
            lines.append(cjk_ljust(colorize(f"  {tag_line}", FG_YELLOW), width))
        lines.append(cjk_ljust(colorize(f"  {part.description}", FG_WHITE), width))
        if part.history:
            lines.append(cjk_ljust(colorize(f"  {part.history}", FG_MAGENTA), width))
        return lines

    print(colorize("  肉体情报（表）" + " " * (col_width - 14) + "肉体情报（里）", FG_WHITE, bold=True))
    print(colorize("  " + "─" * (col_width - 2) + "  " + "─" * (col_width - 2), FG_DARK_GRAY))

    for left_part, right_part in zip(outer, inner):
        left_lines = format_part(left_part, col_width)
        right_lines = format_part(right_part, col_width)
        max_len = max(len(left_lines), len(right_lines))
        for i in range(max_len):
            left = left_lines[i] if i < len(left_lines) else cjk_ljust("", col_width)
            right = right_lines[i] if i < len(right_lines) else cjk_ljust("", col_width)
            print(f"  {left}  {right}")
        print()

    # Body features from TALENT 身体特征
    talent_entries = app.tw_axes.family_entries(AxisFamily.TALENT)
    body_features: list[str] = []
    for entry in talent_entries:
        if actor.stats.compat.talent.get(entry.era_index) > 0:
            group = _talent_group_name(entry.era_index)
            if group == "身体特征":
                body_features.append(entry.label)
    print(colorize("□ 身体特征 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))
    if body_features:
        line_col = 14
        cols = max(1, tw // line_col)
        row_buf: list[str] = []
        for label in body_features:
            row_buf.append(colorize(cjk_ljust(f"  {label}", line_col), FG_CYAN))
            if len(row_buf) == cols:
                print("".join(row_buf))
                row_buf = []
        if row_buf:
            print("".join(row_buf))
    else:
        print(colorize("  （尚无显著身体特征）", FG_DARK_GRAY))
    print()

    # PALAM grid (moved from Tab 3)
    palam_axes = [
        ("快C", "pleasure_c"), ("快V", "pleasure_v"),
        ("快A", "pleasure_a"), ("快B", "pleasure_b"),
        ("快M", "pleasure_m"), ("润滑", "lubrication"),
        ("恭顺", "obedience"), ("情欲", "lust"),
        ("屈服", "submission"), ("习得", "mastery"),
        ("恥情", "shame"), ("苦痛", "pain"),
        ("恐怖", "fear"), ("好意", "favor"),
        ("优越", "superiority"), ("反感", "disgust"),
    ]
    print(colorize("□ PALAM □", FG_WHITE, bold=True) + colorize("─" * (tw - 11), FG_DARK_GRAY))
    col_width = 18
    cols = max(1, tw // col_width)
    row_buf = []
    for label, key in palam_axes:
        val = actor.stats.palam.get(key)
        cell = _palam_cell(label, val, col_width)
        row_buf.append(cell)
        if len(row_buf) == cols:
            print("  " + "".join(row_buf))
            row_buf = []
    if row_buf:
        print("  " + "".join(row_buf))
    print()


def _render_tab_likes(actor: CharacterState, app: Application) -> None:
    """Tab 6: 个人好恶 — gift and food preferences."""
    tw = terminal_width()
    print(colorize("□ 个人好恶 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))
    print()

    definition = next(
        (d for d in app.roster if d.key == actor.key), None
    )
    if definition is None:
        print(colorize("  （找不到角色定义）", FG_DARK_GRAY))
        return

    # ── Gifts ──
    print(colorize("□ 礼物 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))
    gift_prefs = definition.gift_preferences
    _render_preference_block(
        liked=gift_prefs.liked_tags,
        disliked=gift_prefs.disliked_tags,
        catalog_pairs=_gift_samples(app, gift_prefs.liked_tags, gift_prefs.disliked_tags),
    )
    print()

    # ── Food ──
    print(colorize("□ 食物 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))
    food_prefs = definition.food_preferences
    _render_preference_block(
        liked=food_prefs.liked_tags,
        disliked=food_prefs.disliked_tags,
        catalog_pairs=(),
    )
    print()


def _render_preference_block(
    liked: tuple[str, ...],
    disliked: tuple[str, ...],
    catalog_pairs: tuple[tuple[str, str], ...],
) -> None:
    """Render liked/disliked tags with optional sample entries."""
    if liked:
        print(f"  {colorize('喜欢:', FG_GREEN)} {' '.join(f'#{t}' for t in liked)}")
    else:
        print(colorize("  喜欢: （未定义）", FG_DARK_GRAY))
    if disliked:
        print(f"  {colorize('讨厌:', FG_RED)} {' '.join(f'#{t}' for t in disliked)}")
    else:
        print(colorize("  讨厌: （未定义）", FG_DARK_GRAY))

    if catalog_pairs:
        print()
        print(colorize("  — 示例 —", FG_GRAY))
        for name, pref in catalog_pairs:
            color = FG_GREEN if pref == "liked" else FG_RED
            print(f"    {colorize(name, color)}  ({pref})")


def _gift_samples(
    app: Application,
    liked: tuple[str, ...],
    disliked: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    """Pick up to 3 liked and 3 disliked gifts from the catalog for display."""
    gift_service = getattr(app.command_service, "gift_service", None)
    if gift_service is None:
        return ()
    liked_gifts: list[tuple[str, str]] = []
    disliked_gifts: list[tuple[str, str]] = []
    for gift in gift_service.gift_definitions.values():
        if any(tag in liked for tag in gift.tags) and len(liked_gifts) < 3:
            liked_gifts.append((gift.display_name, "liked"))
        elif any(tag in disliked for tag in gift.tags) and len(disliked_gifts) < 3:
            disliked_gifts.append((gift.display_name, "disliked"))
    return tuple(liked_gifts + disliked_gifts)


def _render_tab_fallen(
    actor: CharacterState,
    stages: tuple,
    app: Application,
) -> None:
    """Tab 5: 陷落状态 — show progress toward each relationship stage."""
    tw = terminal_width()
    print(colorize("□ 陷落状态 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))
    print()

    intimacy = actor.stats.compat.abl.get(9)  # ABL_INTIMACY_INDEX
    has_dislike = actor.has_mark("dislike_mark")

    # Skip the 'stranger' stage (index 0), show only the 4 target stages
    for stage_def in stages:
        if stage_def.key == "stranger":
            continue

        # Determine if this stage is achieved
        aff_ok = actor.affection >= stage_def.min_affection
        trust_ok = actor.trust >= stage_def.min_trust
        intim_ok = intimacy >= stage_def.min_intimacy
        dislike_ok = not (stage_def.no_dislike_mark and has_dislike)
        item_ok = True
        if stage_def.requires_item:
            item_ok = app.world.item_count(stage_def.requires_item) > 0
        achieved = aff_ok and trust_ok and intim_ok and dislike_ok and item_ok

        title_color = FG_GREEN if achieved else FG_YELLOW
        marker = "■" if achieved else "□"
        print(colorize(f"  {marker}{stage_def.display_name}达成条件", title_color, bold=True))
        print()

        # Affection
        aff_color = FG_GREEN if aff_ok else FG_RED
        print(colorize(
            f"    好感度{stage_def.min_affection}以上  "
            f"（现在: {actor.affection}）",
            aff_color,
        ))

        # Trust
        trust_color = FG_GREEN if trust_ok else FG_RED
        print(colorize(
            f"    信赖度{stage_def.min_trust}以上  "
            f"（现在: {actor.trust}）",
            trust_color,
        ))

        # Intimacy
        if stage_def.min_intimacy > 0:
            intim_color = FG_GREEN if intim_ok else FG_RED
            print(colorize(
                f"    亲密度{stage_def.min_intimacy}以上  "
                f"（现在: {intimacy}）",
                intim_color,
            ))

        # No dislike mark
        if stage_def.no_dislike_mark:
            dislike_color = FG_GREEN if dislike_ok else FG_RED
            dislike_val = 1 if has_dislike else 0
            print(colorize(
                f"    没有反感刻印  "
                f"（现在: {dislike_val}）",
                dislike_color,
            ))

        # Required item
        if stage_def.requires_item:
            have = app.world.item_count(stage_def.requires_item)
            item_color = FG_GREEN if have > 0 else FG_RED
            print(colorize(
                f"    需要道具: {stage_def.requires_item}  "
                f"（持有: {have}）",
                item_color,
            ))

        print()


def _ability_display(
    world: WorldState,
    app: Application,
    initial_actor_key: str | None = None,
) -> None:
    """Interactive tabbed ability display screen."""
    visible = list(_present_characters(app, world.active_location.key))
    if not visible:
        clear_screen()
        print(colorize("  当前位置没有角色。", FG_RED))
        input(colorize("  按 Enter 返回...", FG_GRAY))
        return

    current_char_idx = 0
    if initial_actor_key is not None:
        for index, actor in enumerate(visible):
            if actor.key == initial_actor_key:
                current_char_idx = index
                break
    current_tab = 0
    tab_count = len(_ABILITY_TABS)

    while True:
        actor = visible[current_char_idx]
        clear_screen()

        # ── Header ──
        _render_ability_header(actor)
        print()

        # ── Tab content ──
        tab_key = _ABILITY_TABS[current_tab][1]
        if tab_key == "clothing_ability":
            _render_tab_clothing_ability(actor, app)
        elif tab_key == "exp_jewel":
            _render_tab_exp_jewel(actor, app)
        elif tab_key == "personal":
            _render_tab_personal(actor, app)
        elif tab_key == "likes":
            _render_tab_likes(actor, app)
        elif tab_key == "body":
            _render_tab_body(actor, app)
        elif tab_key == "fallen":
            _render_tab_fallen(actor, app.relationship_stages, app)

        # ── Footer ──
        print(separator("─"))
        _render_tab_bar(current_tab)

        nav_parts: list[str] = []
        for i, (label, _) in enumerate(_ABILITY_TABS):
            nav_parts.append(colorize(f"[{i + 1}]{label}", FG_DARK_GRAY))
        print("  " + "  ".join(nav_parts))

        char_info = colorize(
            f"  角色 {current_char_idx + 1}/{len(visible)}: {actor.display_name}",
            FG_GRAY,
        )
        print(char_info)
        print(
            f"  {colorize('[77] 前一位角色', FG_GRAY)}  "
            f"{colorize('[88] 下一位角色', FG_GRAY)}"
        )
        print(colorize("  [0] 返回", FG_GRAY))

        try:
            raw = input(colorize("  请选择 > ", FG_WHITE)).strip()
        except (EOFError, KeyboardInterrupt):
            return

        if not raw:
            continue

        try:
            choice = int(raw)
        except ValueError:
            continue

        if choice == 0:
            return
        elif 1 <= choice <= tab_count:
            current_tab = choice - 1
        elif choice == 77:
            current_char_idx = (current_char_idx - 1) % len(visible)
        elif choice == 88:
            current_char_idx = (current_char_idx + 1) % len(visible)


# ── Action result rendering ────────────────────────────────────────

def _format_action_result_messages(
    result_messages: list[str],
    result_changes: list | None = None,
    fainted: bool = False,
) -> list[str]:
    """Format action result into display lines."""
    lines: list[str] = []
    for msg in result_messages:
        lines.append(msg)
    if result_changes:
        lines.append(colorize("[状态变化]", FG_YELLOW))
        for change in result_changes:
            direction = "↑" if change.delta > 0 else "↓"
            color = FG_GREEN if change.delta > 0 else FG_RED
            lines.append(
                colorize(
                    f"  {change.family}.{change.target} {direction}{abs(change.delta)} "
                    f"({change.before}→{change.after})",
                    color,
                ),
            )
    if fainted:
        lines.append(colorize("  ※ 体力耗尽，强制就寝。", FG_RED, bold=True))
    return lines


# ── Main loop ──────────────────────────────────────────────────────

def run_cli(app: Application) -> None:
    """eraTW-style main game loop."""
    world = app.world
    last_command: str | None = None
    pending_messages: list[str] = []
    active_act_tab = 0
    selected_actor_key = _auto_select_actor_key(app, world.active_location.key)
    roster_page_index = 0
    roster_page_size = 10
    num_act_cats = len(_ACT_CATEGORIES)

    print(f"\n{colorize(app.config.game_title, FG_BLUE, bold=True)} — 交互模式")
    print(colorize("(终端宽度建议 ≥ 80 列)", FG_DARK_GRAY))

    while True:
        selected_actor_key = _coerce_selected_actor_key(
            app,
            world.active_location.key,
            selected_actor_key,
        )
        if selected_actor_key is None:
            roster_page_index = 0
        else:
            roster_page_index = _page_index_for_actor(
                app,
                world.active_location.key,
                selected_actor_key,
                page_size=roster_page_size,
            )

        # ── Render ────────────────────────────────────────────────
        clear_screen()

        # Zone ①
        _render_header(world, app)

        # Zone ② ③ ④
        _render_scene_context(
            app,
            world,
            selected_actor_key,
            roster_page_index=roster_page_index,
            page_size=roster_page_size,
        )

        # Zone ⑤
        if pending_messages:
            _render_messages(pending_messages)

        # Zone ⑥
        print(separator("─"))
        menu_dict = _build_menu(
            app,
            world,
            selected_actor_key=selected_actor_key,
            roster_page_index=roster_page_index,
            page_size=roster_page_size,
        )
        flat_menu = _render_command_menu(menu_dict, active_act_tab)
        print(separator("─"))

        # Zone ⑦
        prompt_parts = []
        if last_command:
            prompt_parts.append(
                colorize(f"<上回指令: {last_command}>", FG_DARK_GRAY),
            )
        prompt_parts.append(colorize("请选择 > ", FG_WHITE))
        prompt_str = "  ".join(prompt_parts)

        try:
            raw = input(prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            print(colorize("\n再见。", FG_GRAY))
            break

        if not raw:
            pending_messages = []
            continue

        # Tab switching for Act_COM categories
        if raw in ("<", "["):
            active_act_tab = (active_act_tab - 1) % num_act_cats
            pending_messages = []
            continue
        if raw in (">", "]"):
            active_act_tab = (active_act_tab + 1) % num_act_cats
            pending_messages = []
            continue

        try:
            choice = int(raw)
        except ValueError:
            pending_messages = [colorize("请输入数字。", FG_RED)]
            continue

        if choice < 1 or choice > len(flat_menu):
            pending_messages = [colorize("无效选项。", FG_RED)]
            continue

        label, action_type, param = flat_menu[choice - 1]
        last_command = label
        pending_messages = []

        # ── Dispatch ──────────────────────────────────────────────

        if action_type == "quit":
            print(colorize("再见。", FG_GRAY))
            break

        if action_type == "status":
            _ability_display(world, app, initial_actor_key=selected_actor_key)
            continue

        if action_type == "save":
            save_path = app.save_service.save_world(world)
            pending_messages = [
                colorize(f"已保存到 {save_path.name}。", FG_GREEN),
            ]
            continue

        if action_type == "load":
            world = app.save_service.load_world()
            app.world = world
            app.distribution_service.refresh_world(world)
            app.relationship_service.refresh_world(world)
            app.companion_service.refresh_world(world)
            app.date_service.refresh_world(world)
            selected_actor_key = _auto_select_actor_key(app, world.active_location.key)
            roster_page_index = 0
            pending_messages = [
                colorize("已读取快速存档。", FG_GREEN),
            ]
            continue

        if action_type == "wait":
            app.game_loop.advance_time(world)
            app.companion_service.refresh_world(world)
            msg_lines = [
                colorize(
                    f"时间推进到 {_slot_label(world.current_time_slot.value)}。",
                    FG_CYAN,
                ),
            ]
            encountered = world.encounter_characters()
            for actor in encountered:
                msg_lines.append(
                    colorize(f"遇到了{actor.display_name}。", FG_WHITE),
                )
                actor.encounter_location_key = world.active_location.key
            pending_messages = msg_lines
            continue

        if action_type == "move_header":
            continue

        if action_type == "move":
            result = app.navigation_service.execute_move(world, param)
            selected_actor_key = _coerce_selected_actor_key(
                app,
                world.active_location.key,
                selected_actor_key,
            )
            pending_messages = _format_action_result_messages(result.messages)
            continue

        if action_type == "shop":
            pending_messages = _open_shopfront(app, world, param)
            continue

        if action_type == "skin_wardrobe":
            pending_messages = _open_skin_wardrobe(app, world, param)
            continue

        if action_type == "calendar":
            pending_messages = _show_calendar(app, world)
            continue

        if action_type == "select_actor":
            selected_actor_key = _coerce_selected_actor_key(
                app,
                world.active_location.key,
                param,
            )
            if selected_actor_key is None:
                pending_messages = [colorize("当前位置没有可选舰娘。", FG_RED)]
            else:
                roster_page_index = _page_index_for_actor(
                    app,
                    world.active_location.key,
                    selected_actor_key,
                    page_size=roster_page_size,
                )
                actor = _selected_present_actor(
                    app,
                    world.active_location.key,
                    selected_actor_key,
                )
                pending_messages = [
                    colorize(f"当前目标已切换为 {actor.display_name}。", FG_CYAN),
                ]
            continue

        if action_type == "page_roster":
            delta = -1 if param == "prev" else 1
            roster_page_index = _normalize_roster_page_index(
                app,
                world.active_location.key,
                roster_page_index + delta,
                page_size=roster_page_size,
            )
            page_actors = _paginate_present_characters(
                app,
                world.active_location.key,
                page_index=roster_page_index,
                page_size=roster_page_size,
            )
            selected_actor_key = page_actors[0].key if page_actors else None
            page_count = _roster_page_count(
                app,
                world.active_location.key,
                page_size=roster_page_size,
            )
            pending_messages = [
                colorize(
                    f"切换到舰娘列表第 {roster_page_index + 1}/{page_count} 页。",
                    FG_CYAN,
                ),
            ]
            continue

        if action_type == "command":
            actor_key, cmd_key = param.split(":", 1)
            result = app.command_service.execute(world, actor_key, cmd_key)
            if result.shopfront_key is not None:
                pending_messages = _open_shopfront(app, world, result.shopfront_key)
                continue
            pending_messages = _format_action_result_messages(
                result.messages,
                result.changes,
                result.fainted,
            )
            continue

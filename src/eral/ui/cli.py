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

from eral.app.bootstrap import Application
from eral.domain.world import CharacterState, WorldState
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
    ("上衣", "top"),
    ("下衣", "bottom"),
    ("内衣(上)", "underwear_top"),
    ("内衣(下)", "underwear_bottom"),
    ("袜子", "socks"),
    ("鞋", "shoes"),
    ("饰品", "accessory"),
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


def _build_menu(
    app: Application,
    world: WorldState,
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

    visible = world.visible_characters()

    # Actor commands — map to game category
    for actor in visible:
        actor_commands = app.command_service.available_commands_for_actor(
            world, actor.key,
        )
        for cmd in actor_commands:
            cat = cmd.category if cmd.category in menu else "daily"
            label = f"{cmd.display_name}→{actor.display_name}"
            menu[cat].append((label, "command", f"{actor.key}:{cmd.key}"))

    # Navigation
    visible_destinations = app.navigation_service.visible_destinations(world)
    for key in visible_destinations:
        loc = app.port_map.location_by_key(key)
        menu["move"].append((f"前往 {loc.display_name}", "move", key))

    # Time & generic
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


# ── Zone ② bis : Scene context (multiple characters) ──────────────

def _render_scene_context(world: WorldState) -> None:
    """Render a compact list of all visible characters at current location."""
    visible = world.visible_characters()
    if not visible:
        print(colorize("  （周围没有人）", FG_DARK_GRAY))
        print()
        return

    if len(visible) == 1:
        # Single target — render full detail
        _render_target_status(visible[0])
        _render_vitals(visible[0])
        _render_look(visible[0])
        return

    # Multiple characters — compact list, then detail for first
    for actor in visible:
        tags: list[str] = []
        if actor.is_following:
            tags.append("👣同行")
        if actor.is_on_date:
            tags.append("💖约会")
        tag_str = " ".join(tags)
        stage_text = (
            actor.relationship_stage.display_name
            if actor.relationship_stage
            else "陌生"
        )
        name_part = colorize(f"[{actor.display_name}]", FG_WHITE, bold=True)
        stats_part = (
            f"{colorize(f'好感:{actor.affection}', FG_CYAN)}  "
            f"{colorize(f'信赖:{actor.trust}', FG_GREEN)}  "
            f"{colorize(f'关系:{stage_text}', FG_MAGENTA)}"
        )
        suffix = f"  {colorize(tag_str, FG_ORANGE)}" if tag_str else ""
        print(f"  {cjk_ljust(name_part, 16)} {stats_part}{suffix}")
    print()

    # Show detailed view for the first visible character
    first = visible[0]
    print(separator("─"))
    _render_target_status(first)
    _render_vitals(first)
    _render_look(first)


# ── Zone ⑦ : Ability display (tabbed status screen) ───────────────

_ABILITY_TABS = (
    ("服装&能力", "clothing_ability"),
    ("经验&宝珠", "exp_jewel"),
    ("个人情报", "personal"),
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
    col_width = 20
    cols = max(1, tw // col_width)
    row_buf: list[str] = []
    for slot_name, _slot_key in _CLOTHING_SLOTS:
        cell = colorize(cjk_ljust(f"  {slot_name}: ----", col_width), FG_DARK_GRAY)
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


def _render_tab_exp_jewel(actor: CharacterState, app: Application) -> None:
    """Tab 2: 经验 & 宝珠."""
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
            if sec not in grouped:
                grouped[sec] = []
            grouped[sec].append((f"{label}经验", exp_val))

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

    # ── Jewel section (placeholder) ──
    print(colorize("□ 宝珠 □", FG_WHITE, bold=True) + colorize("─" * (tw - 10), FG_DARK_GRAY))
    print(colorize("  （宝珠系统尚未实装）", FG_DARK_GRAY))
    print()


def _render_tab_personal(actor: CharacterState, app: Application) -> None:
    """Tab 3: 个人情报."""
    from eral.content.tw_axis_registry import AxisFamily

    tw = terminal_width()
    print(colorize("□ 个人情报 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))

    stage_text = actor.relationship_stage.display_name if actor.relationship_stage else "陌生"
    print(f"  {colorize('关系阶段:', FG_GRAY)} {colorize(stage_text, FG_MAGENTA, bold=True)}")
    print(f"  {colorize('好感度:', FG_GRAY)}   {colorize(str(actor.affection), FG_CYAN)}")
    print(f"  {colorize('信赖度:', FG_GRAY)}   {colorize(str(actor.trust), FG_GREEN)}")
    print(f"  {colorize('服从度:', FG_GRAY)}   {colorize(str(actor.obedience), FG_YELLOW)}")
    print()

    # Tags
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
    if actor.marks:
        print(colorize("  ── 印记 ──", FG_GRAY))
        for mark_key, mark_val in actor.marks.items():
            if mark_val > 0:
                print(f"    {colorize(mark_key, FG_ORANGE)}: Lv.{mark_val}")
        print()

    # TALENT display
    talent_entries = app.tw_axes.family_entries(AxisFamily.TALENT)
    active: dict[str, list[str]] = {}
    for entry in talent_entries:
        if actor.stats.compat.talent.get(entry.era_index) > 0:
            group = _talent_group_name(entry.era_index)
            if group not in active:
                active[group] = []
            active[group].append(entry.label)

    if active:
        print(colorize("  ── 素质 ──", FG_GRAY))
        col_width = 16
        cols = max(1, (tw - 4) // col_width)
        for _lo, _hi, group_name in _TALENT_GROUPS:
            items = active.get(group_name)
            if not items:
                continue
            print(f"    {colorize(f'[{group_name}]', FG_DARK_GRAY)}", end="")
            row_buf: list[str] = []
            for i, label in enumerate(items):
                row_buf.append(colorize(cjk_ljust(label, col_width), FG_CYAN))
                if len(row_buf) == cols:
                    if i < cols:
                        print("  " + "".join(row_buf))
                    else:
                        print()
                        print("    " + "".join(row_buf))
                    row_buf = []
            if row_buf:
                print("  " + "".join(row_buf))
        print()

    # PALAM grid
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
    has_palam = any(actor.stats.palam.get(k) > 0 for _, k in palam_axes)
    if has_palam:
        print(colorize("  ── PALAM ──", FG_GRAY))
        col_width = 18
        cols = max(1, tw // col_width)
        row_buf: list[str] = []
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


def _render_tab_body(actor: CharacterState, app: Application) -> None:
    """Tab 4: 身体情报."""
    tw = terminal_width()
    print(colorize("□ 身体情报 □", FG_WHITE, bold=True) + colorize("─" * (tw - 14), FG_DARK_GRAY))

    # ── Body measurements (from BASE body_shape group, placeholder) ──
    print(colorize("  ── 身体数据 ──", FG_GRAY))
    body_params = [
        ("身高", "height"), ("体重", "weight"),
        ("胸围", "bust"), ("腰围", "waist"), ("臀围", "hips"),
    ]
    col_width = 18
    cols = max(1, tw // col_width)
    row_buf: list[str] = []
    for label, _key in body_params:
        row_buf.append(colorize(cjk_ljust(f"  {label}: ----", col_width), FG_DARK_GRAY))
        if len(row_buf) == cols:
            print("".join(row_buf))
            row_buf = []
    if row_buf:
        print("".join(row_buf))
    print()

    # ── Sensitivity (from BASE/TALENT sensitivity entries, placeholder) ──
    print(colorize("  ── 敏感度 ──", FG_GRAY))
    sensitivity = [
        ("C敏感度", "pleasure_c"), ("V敏感度", "pleasure_v"),
        ("A敏感度", "pleasure_a"), ("B敏感度", "pleasure_b"),
        ("M敏感度", "pleasure_m"),
    ]
    row_buf = []
    for label, _key in sensitivity:
        row_buf.append(colorize(cjk_ljust(f"  {label}: ----", col_width), FG_DARK_GRAY))
        if len(row_buf) == cols:
            print("".join(row_buf))
            row_buf = []
    if row_buf:
        print("".join(row_buf))
    print()

    # ── Body features (from TALENT 身体特徴 section, placeholder) ──
    print(colorize("  ── 身体特征 ──", FG_GRAY))
    print(colorize("  （身体特征系统尚未实装）", FG_DARK_GRAY))
    print()


def _render_tab_fallen(
    actor: CharacterState,
    stages: tuple,
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
        item_ok = True  # item system not implemented yet
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
            print(colorize(
                f"    需要道具: {stage_def.requires_item}  "
                f"（道具系统未实装）",
                FG_DARK_GRAY,
            ))

        print()


def _ability_display(world: WorldState, app: Application) -> None:
    """Interactive tabbed ability display screen."""
    visible = list(world.visible_characters())
    if not visible:
        clear_screen()
        print(colorize("  当前位置没有角色。", FG_RED))
        input(colorize("  按 Enter 返回...", FG_GRAY))
        return

    current_char_idx = 0
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
        elif tab_key == "body":
            _render_tab_body(actor, app)
        elif tab_key == "fallen":
            _render_tab_fallen(actor, app.relationship_stages)

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
    num_act_cats = len(_ACT_CATEGORIES)

    print(f"\n{colorize(app.config.game_title, FG_BLUE, bold=True)} — 交互模式")
    print(colorize("(终端宽度建议 ≥ 80 列)", FG_DARK_GRAY))

    while True:
        # ── Render ────────────────────────────────────────────────
        clear_screen()

        # Zone ①
        _render_header(world, app)

        # Zone ② ③ ④
        _render_scene_context(world)

        # Zone ⑤
        if pending_messages:
            _render_messages(pending_messages)

        # Zone ⑥
        print(separator("─"))
        menu_dict = _build_menu(app, world)
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
            _ability_display(world, app)
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
            app.relationship_service.refresh_world(world)
            app.companion_service.refresh_world(world)
            app.date_service.refresh_world(world)
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

        if action_type == "move":
            result = app.navigation_service.move_player(world, param)
            pending_messages = _format_action_result_messages(result.messages)
            continue

        if action_type == "command":
            actor_key, cmd_key = param.split(":", 1)
            result = app.command_service.execute(world, actor_key, cmd_key)
            pending_messages = _format_action_result_messages(
                result.messages,
                result.changes,
                result.fainted,
            )
            continue

"""Web-based character and dialogue editor for erAL.

Launch with: python -m eral.tools.editor [--port PORT] [--root ROOT]

Opens a browser-based editor for creating and editing character packs,
including basic info, stats (BASE/PALAM/ABL/TALENT/CFLAG), dialogue, and events.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from eral.content.character_relations import load_character_relations
from eral.content.commands import load_command_definitions
from eral.content.gifts import load_gift_definitions
from eral.content.marks import load_mark_definitions
from eral.content.port_map import load_port_map
from eral.content.relationships import load_relationship_stages
from eral.content.skins import load_appearance_definitions, load_skin_definitions
from eral.content.stat_axes import AxisFamily, load_stat_axis_catalog
from eral.content.work_schedules import load_work_schedule_definitions

TIME_SLOTS: tuple[str, ...] = ("dawn", "morning", "afternoon", "evening", "night", "late_night")
KANA_RE = re.compile(r"[ぁ-んァ-ンｧ-ﾝﾞﾟー]")
INTERNAL_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
INDEX_KEY_RE = re.compile(r"^(abl|talent|cflag|flag|tflag|base|palam)_\d+$", re.IGNORECASE)

JP_ZH_REPLACEMENTS: tuple[tuple[str, str], ...] = (
  # —— 必须最先替换的多字短语（被后续单字短语拆散前处理）——
  ("キス未経験", "无接吻经验"),
  ("一線越えない", "难以越过的底线"),
  ("目立ちたがり", "喜欢引人注目"),
  ("幼児／幼児退行", "幼儿/幼儿退行"),
  ("濡れやすさ", "弄湿难易"),
  ("自慰しやすい", "容易自慰"),
  ("快感応答", "快感应答"),
  ("性別嗜好", "性别嗜好"),
  ("ヒップサイズ", "臀围"),
  ("酒耐性", "酒耐性"),
  # —— 核心词组（原有）——
  ("ムード", "情绪"),
  ("怒り", "愤怒"),
  ("酒気", "醉意"),
  ("抑鬱", "抑郁"),
  ("バスト", "胸围"),
  ("ウェスト", "腰围"),
  ("ヒップサイズ", "臀围尺寸"),
  ("ヒップ", "臀围"),
  ("気力", "气力"),
  ("身長", "身高"),
  ("体重", "体重"),
  ("絶頂", "高潮"),
  ("余韻", "余韵"),
  ("経験", "经验"),
  ("感覚", "感官"),
  ("親密", "亲密"),
  ("従順", "顺从"),
  ("戦闘", "战斗"),
  ("話術", "话术"),
  ("清掃", "清扫"),
  ("音楽", "音乐"),
  ("教養", "教养"),
  ("肛門", "肛门"),
  ("膣", "阴道"),
  ("歓楽", "欢愉"),
  ("屈従", "屈从"),
  ("鬱屈", "郁屈"),
  # —— SOURCE / PALAM 补齐 ——
  ("与快", "快"),
  ("潤滑", "润滑"),
  ("恭順", "恭顺"),
  ("屈服", "屈服"),
  ("習得", "习得"),
  ("恥情", "羞情"),
  ("好意", "好意"),
  ("優越", "优越"),
  ("反感", "反感"),
  ("不快", "不适"),
  ("眠姦", "眠奸"),
  ("情愛", "情爱"),
  ("性行動", "性行为"),
  ("達成", "达成"),
  ("苦痛", "苦痛"),
  ("恐怖", "恐惧"),
  ("欲情", "欲情"),
  ("露出", "露出"),
  ("征服", "征服"),
  ("受動", "受动"),
  ("不潔", "不洁"),
  ("逸脱", "逸脱"),
  ("誘惑", "诱惑"),
  ("挑発", "挑衅"),
  ("奉仕", "奉献"),
  ("強要", "强求"),
  ("加虐", "加虐"),
  # —— TALENT 常用（对齐 参考图/素质编辑.png 的中文）——
  ("処女", "处女"),
  ("非童貞", "非处男"),
  ("性別", "性别"),
  ("キス未経験", "无接吻经验"),
  ("態度", "态度"),
  ("応答", "回应"),
  ("傲嬌", "娇俏"),
  ("年齢", "年龄"),
  ("自制心", "自制心"),
  ("無知", "无知"),
  ("一線越えない", "难以越过的底线"),
  ("目立ちたがり", "喜欢引人注目"),
  ("貞操", "贞操"),
  ("自己愛", "自己爱"),
  ("羞恥心", "羞耻心"),
  ("痛覚", "痛觉"),
  ("濡れやすさ", "弄湿难易"),
  ("猫舌", "猫舌"),
  ("漏尿癖", "漏尿癖"),
  ("自慰しやすい", "容易自慰"),
  ("汚臭耐性", "污臭耐性"),
  ("献身的", "献身的"),
  ("快感応答", "快感应答"),
  ("倒錯的", "倒错的"),
  ("性別嗜好", "性别嗜好"),
  ("施虐狂", "施虐狂"),
  ("受虐狂", "受虐狂"),
  ("体型", "体型"),
  ("Ｃ感度", "C感度"),
  ("Ｖ感度", "V感度"),
  ("Ａ感度", "A感度"),
  ("Ｂ感度", "B感度"),
  ("Ｍ感度", "M感度"),
  ("胸围", "胸围"),
  ("ヒップサイズ", "臀围"),
  ("ヒップ", "臀围"),
  ("酒耐性", "酒耐性"),
  ("風騷", "风骚"),
  ("動物耳", "兽耳"),
  ("具現", "其它"),
  ("幼児／幼児退行", "幼儿/幼儿退行"),
  ("幼児退行", "幼儿退行"),
  ("幼児", "幼儿"),
  ("幼稚", "幼稚"),
  ("初潮", "初潮"),
  ("容易中毒", "容易中毒"),
  ("胆量", "胆量"),
  ("懒散", "懒散"),
  ("性情不定", "性情不定"),
  ("冷漠", "冷漠"),
  ("感情缺乏", "感情缺乏"),
  ("性的兴趣", "性的兴趣"),
  ("抵抗", "抵抗"),
  ("自尊心", "自尊心"),
  # —— CFLAG / FLAG / TFLAG 常用 ——
  ("既成事実", "既成事实"),
  ("信頼度", "信赖度"),
  ("基本服装セット", "基本服装组合"),
  ("服装オプション", "服装选项"),
  ("弱み握られ", "把柄被握"),
  ("弱み握り", "把柄握有"),
  ("デート後イベントフラグ", "约会后事件标志"),
  ("デート中", "约会中"),
  ("合意判定", "合意判定"),
  ("異常経験", "异常经验"),
  ("オナバレ", "自慰被撞见"),
  ("夜這い", "夜袭"),
  ("面識", "面识"),
  ("固有指令", "固有指令"),
  ("口上実装状況", "口上实装状况"),
  ("前回の口上実装状況", "前回口上实装状况"),
  ("現在位置", "现在位置"),
  ("同行準備", "同行准备"),
  ("同行", "同行"),
  ("同室", "同室"),
  ("陪睡中", "陪睡中"),
  ("風呂", "浴室"),
  ("情事目撃", "情事目击"),
  ("行動時間", "行动时间"),
  ("行動", "行动"),
  ("職場", "职场"),
  ("徹夜", "通宵"),
  ("隠密中", "隐密中"),
  ("招待", "邀请"),
  ("遭遇位置", "遭遇位置"),
  ("清い交際", "纯洁交际"),
  ("体目当て", "只图肉体"),
  ("膣内射精", "阴内射精"),
  ("肛門射精", "肛门射精"),
  ("口内精液", "口内精液"),
  ("勃起度", "勃起度"),
  ("初期位置", "初始位置"),
  ("衰弱", "衰弱"),
  ("睡眠", "睡眠"),
  ("味覚嗜好", "味觉嗜好"),
  ("延迟", "延迟"),
  ("大掃除", "大扫除"),
  ("片付け工作量", "整理工作量"),
  ("片付け場所", "整理地点"),
  ("職種", "职种"),
  ("睡衣", "睡衣"),
  ("忙得抽不出手", "忙得抽不出手"),
  ("自慰过了", "自慰过了"),
  ("宴会開催", "宴会开办"),
  ("宴会規模", "宴会规模"),
  ("宴会会場", "宴会会场"),
  ("開始時間", "开始时间"),
  ("開始日", "开始日"),
  ("参加人数", "参加人数"),
  ("悪天候中止", "恶劣天气中止"),
  ("宴会差し入れ", "宴会慰劳品"),
  ("每日变更事件", "每日变更事件"),
  ("陥落人数", "陷落人数"),
  ("周回数", "周目数"),
  ("累計好感度上昇量", "累计好感度上升量"),
  ("住宿人物", "住宿人物"),
  ("偷情人数", "偷情人数"),
  ("警告牌使用", "警告牌使用"),
  ("享用処女", "享用处女"),
  ("好感度上昇率", "好感度上升率"),
  ("信頼度上昇率", "信赖度上升率"),
  ("委托接口", "委托接口"),
  ("追加恋人枠", "恋人槽位扩充"),
  ("寻找委托", "寻找委托"),
  ("時間停止", "时间停止"),
  ("禁自慰", "禁自慰"),
  ("抱負", "抱负"),
  ("约会的对象", "约会对象"),
  ("道具購入済み", "道具已购入"),
  ("新聞購読", "报纸订阅"),
  ("射精部位", "射精部位"),
  ("破瓜", "破瓜"),
  ("挿入継続", "插入继续"),
  ("挿入不可", "插入不可"),
  ("刻印取得", "刻印获取"),
  ("刻印従順変化", "刻印顺从变化"),
  ("特殊COM", "特殊指令"),
  ("使用中", "使用中"),
  ("不让推倒", "不让推倒"),
  ("授乳コマンド", "授乳指令"),
  ("キス合意取得", "接吻合意获取"),
  ("信頼度変化なし", "信赖度无变化"),
  ("理性削り", "理性削减"),
  ("情緒上昇抑制", "情绪上升抑制"),
  ("情緒BONUS", "情绪加成"),
  ("口上特殊補正", "口上特殊修正"),
  ("好感度BONUS", "好感度加成"),
  ("好感度减少", "好感度减少"),
  ("好感度管理", "好感度管理"),
  ("信赖度管理之２", "信赖度管理二"),
  ("信赖度管理", "信赖度管理"),
  ("調教中COMABLE管理", "调教中指令可用管理"),
  ("調教自動実行管理", "调教自动执行管理"),
  ("COMABLE管理", "指令可用管理"),
)

FAMILY_ZH_NAME: dict[str, str] = {
  "base": "基础",
  "palam": "参数",
  "abl": "能力",
  "talent": "素质",
  "cflag": "角色标记",
  "flag": "全局标记",
  "tflag": "临时标记",
}


def _localize_display_text(value: object, fallback: str = "") -> str:
  text = str(value or "").strip()
  if not text:
    return fallback
  for source, target in JP_ZH_REPLACEMENTS:
    text = text.replace(source, target)
  if KANA_RE.search(text):
    return fallback or "未命名"
  return text


def _family_fallback_label(family: str, era_index: object, key: object, idx: int) -> str:
  """Retained for potential reuse; currently only the axis-label localize path is wired in."""
  family_name = FAMILY_ZH_NAME.get(str(family), str(family).upper())
  if isinstance(era_index, int):
    return f"{family_name}[{era_index}]"
  key_text = str(key or "").strip()
  if key_text:
    return f"{family_name}[{key_text}]"
  return f"{family_name}[{idx}]"

# _looks_internal_label / _normalize_section_text 已在重构中移除。
# 之前用于 registry.json 的 section 字段清洗；axes/*.toml 已是干净 label + group，不需要再清洗。

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


def _stat_axes_path(root: Path) -> Path:
  return root / "data" / "base" / "axes"


def _port_map_path(root: Path) -> Path:
  return root / "data" / "base" / "port_map.toml"


def _commands_path(root: Path) -> Path:
  return root / "data" / "base" / "commands.toml"


def _relationship_stages_path(root: Path) -> Path:
  return root / "data" / "base" / "relationship_stages.toml"


def _marks_path(root: Path) -> Path:
  return root / "data" / "base" / "marks.toml"


def _checklist_path(root: Path) -> Path:
  """Retained for historical reference; no longer read by the editor."""
  return root / "docs" / "tw_axis_registry_checklist.md"


def _skins_path(root: Path) -> Path:
  return root / "data" / "base" / "skins.toml"


def _appearances_path(root: Path) -> Path:
  return root / "data" / "base" / "appearances.toml"


def _work_schedules_path(root: Path) -> Path:
  return root / "data" / "base" / "work_schedules.toml"


def _character_relations_path(root: Path) -> Path:
  return root / "data" / "base" / "character_relations.toml"


def _gifts_path(root: Path) -> Path:
  return root / "data" / "base" / "gifts.toml"


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


# _load_registry / _load_registry_allowlist 已在重构中移除。
# 编辑器所有 axis 定义现在直接读取 data/base/axes/*.toml。


def _load_stat_axes(root: Path) -> dict[str, list[dict[str, object]]]:
  path = _stat_axes_path(root)
  if not path.exists():
    return {}
  catalog = load_stat_axis_catalog(path)
  payload: dict[str, list[dict[str, object]]] = {}
  # 所有家族都从 axes/*.toml 加载；editor 各 tab 根据需要挑选。
  for family in (AxisFamily.BASE, AxisFamily.PALAM, AxisFamily.SOURCE,
                 AxisFamily.ABL, AxisFamily.TALENT):
    payload[family.value] = [
      {
        "key": axis.key,
        "era_index": axis.era_index,
        "label": _localize_display_text(axis.label, axis.key),
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


def _load_areas(root: Path) -> list[dict[str, object]]:
    path = _port_map_path(root)
    if not path.exists():
        return []
    port_map = load_port_map(path)
    return [
        {
            "key": area.key,
            "display_name": area.display_name,
            "kind": area.kind,
            "faction_key": area.faction_key or "",
        }
        for area in port_map.areas
    ]


def _load_all_skins(root: Path) -> list[dict[str, object]]:
    path = _skins_path(root)
    if not path.exists():
        return []
    return [
        {
            "key": skin.key,
            "actor_key": skin.actor_key,
            "display_name": skin.display_name,
            "price": skin.price,
            "grant_mode": skin.grant_mode,
            "shop_visibility": skin.shop_visibility,
            "tags": list(skin.tags),
            "appearance_key": skin.appearance_key,
        }
        for skin in load_skin_definitions(path)
    ]


def _load_all_appearances(root: Path) -> dict[str, dict[str, object]]:
    path = _appearances_path(root)
    if not path.exists():
        return {}
    return {
        appearance.key: {
            "key": appearance.key,
            "portrait_key": appearance.portrait_key,
            "slots": dict(appearance.slots),
        }
        for appearance in load_appearance_definitions(path)
    }


def _load_all_work_schedules(root: Path) -> list[dict[str, object]]:
    path = _work_schedules_path(root)
    if not path.exists():
        return []
    result: list[dict[str, object]] = []
    for sch in load_work_schedule_definitions(path):
        result.append({
            "key": sch.key,
            "actor_key": sch.actor_key,
            "location_key": sch.location_key,
            "work_key": sch.work_key,
            "work_label": sch.work_label,
            "start_time": sch.start_time,
            "end_time": sch.end_time,
            "date_rules": {k: list(v) for k, v in sch.date_rules.items()},
        })
    return result


def _load_all_relations(root: Path) -> list[dict[str, object]]:
    path = _character_relations_path(root)
    if not path.exists():
        return []
    index = load_character_relations(path)
    return [
        {
            "from": r.from_key,
            "to": r.to_key,
            "affinity": r.affinity,
            "tags": list(r.tags),
        }
        for r in index.relations
    ]


def _load_gift_tags(root: Path) -> list[str]:
    path = _gifts_path(root)
    if not path.exists():
        return []
    tags: set[str] = set()
    for gift in load_gift_definitions(path):
        for t in gift.tags:
            tags.add(t)
    return sorted(tags)


def _save_work_schedules(root: Path, schedules: list[dict]) -> dict:
    """Rewrite work_schedules.toml with the full schedule list."""
    path = _work_schedules_path(root)
    lines: list[str] = []
    for sch in schedules:
        lines.append("[[work_schedules]]")
        lines.append(f'key = {_toml_escape(str(sch.get("key", "")))}')
        lines.append(f'actor_key = {_toml_escape(str(sch.get("actor_key", "")))}')
        lines.append(f'location_key = {_toml_escape(str(sch.get("location_key", "")))}')
        lines.append(f'work_key = {_toml_escape(str(sch.get("work_key", "")))}')
        lines.append(f'work_label = {_toml_escape(str(sch.get("work_label", "")))}')
        lines.append(f'start_time = {_toml_escape(str(sch.get("start_time", "")))}')
        lines.append(f'end_time = {_toml_escape(str(sch.get("end_time", "")))}')
        date_rules = sch.get("date_rules") or {}
        if date_rules:
            lines.append("")
            lines.append("[work_schedules.date_rules]")
            for rk, rv in date_rules.items():
                if isinstance(rv, list):
                    items = ", ".join(
                        _toml_escape(x) if isinstance(x, str) else str(x) for x in rv
                    )
                    lines.append(f"{rk} = [{items}]")
                elif isinstance(rv, (int, float)):
                    lines.append(f"{rk} = {rv}")
                else:
                    lines.append(f"{rk} = {_toml_escape(str(rv))}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {"status": "ok"}


def _save_character_relations(root: Path, relations: list[dict]) -> dict:
    """Rewrite character_relations.toml with the full relations list."""
    path = _character_relations_path(root)
    header_lines: list[str] = []
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in existing:
            stripped = line.lstrip()
            if stripped.startswith("[[relations]]"):
                break
            header_lines.append(line)

    lines: list[str] = list(header_lines)
    if lines and lines[-1].strip() != "":
        lines.append("")

    for r in relations:
        lines.append("[[relations]]")
        lines.append(f'from = {_toml_escape(str(r.get("from", "")))}')
        lines.append(f'to = {_toml_escape(str(r.get("to", "")))}')
        try:
            affinity = int(r.get("affinity", 0))
        except (TypeError, ValueError):
            affinity = 0
        lines.append(f"affinity = {affinity}")
        tags = r.get("tags") or []
        if tags:
            items = ", ".join(_toml_escape(str(t)) for t in tags)
            lines.append(f"tags = [{items}]")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {"status": "ok"}


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
        "areas": _load_areas(root),
        "commands": _load_commands(root),
        "command_keys": _load_command_keys(root),
        "stages": _load_relationship_stage_defs(root),
        "stage_keys": _load_relationship_stages(root),
        "marks": _load_mark_defs(root),
        "stat_axes": _load_stat_axes(root),
        "time_slots": list(TIME_SLOTS),
        "starting_location": start_location,
        "skins": _load_all_skins(root),
        "appearances": _load_all_appearances(root),
        "gift_tags": _load_gift_tags(root),
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
        query = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/api/characters":
            self._send_json(list_characters(self.root))
        elif path == "/api/work_schedules":
            actor = (query.get("actor", [""])[0] or "").strip()
            all_schedules = _load_all_work_schedules(self.root)
            if actor:
                self._send_json([s for s in all_schedules if s["actor_key"] == actor])
            else:
                self._send_json(all_schedules)
        elif path == "/api/relations":
            actor = (query.get("actor", [""])[0] or "").strip()
            all_relations = _load_all_relations(self.root)
            if actor:
                self._send_json([r for r in all_relations if r["from"] == actor or r["to"] == actor])
            else:
                self._send_json(all_relations)
        elif path.startswith("/api/characters/"):
            key = path.split("/api/characters/")[1].rstrip("/")
            if key == "meta":
                # Return metadata for editor (locations, commands, stages, registry)
                meta = _load_meta(self.root)
                self._send_json({
                    "locations": meta["locations"],
                    "location_tags": meta["location_tags"],
                    "areas": meta["areas"],
                    "commands": meta["commands"],
                    "command_keys": meta["command_keys"],
                    "stages": meta["stages"],
                    "stage_keys": meta["stage_keys"],
                    "marks": meta["marks"],
                    "stat_axes": meta["stat_axes"],
                    "time_slots": meta["time_slots"],
                    "starting_location": meta["starting_location"],
                    "skins": meta["skins"],
                    "appearances": meta["appearances"],
                    "gift_tags": meta["gift_tags"],
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

        if path == "/api/work_schedules":
            body = json.loads(self._read_body().decode("utf-8"))
            schedules = body if isinstance(body, list) else body.get("schedules", [])
            result = _save_work_schedules(self.root, schedules)
            self._send_json(result)
        elif path == "/api/relations":
            body = json.loads(self._read_body().decode("utf-8"))
            relations = body if isinstance(body, list) else body.get("relations", [])
            result = _save_character_relations(self.root, relations)
            self._send_json(result)
        elif path.startswith("/api/characters/"):
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
.info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; margin: 10px 0; }
.info-grid > div { background: #16213e; border: 1px solid #0f3460; border-radius: 4px; padding: 8px 10px; font-size: 13px; }
.info-label { color: #8fa3c8; margin-right: 4px; }
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
    <button class="tab" data-tab="personal" onclick="switchTab('personal')">个人情报</button>
    <button class="tab" data-tab="stats" onclick="switchTab('stats')">数值属性</button>
    <button class="tab" data-tab="relations" onclick="switchTab('relations')">人际关系</button>
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
  if (tab === 'personal') {
    ensurePersonalData();
    return;
  }
  if (tab === 'relations') {
    ensureRelationsData();
    return;
  }
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
    case 'personal': el.innerHTML = renderPersonal(); break;
    case 'stats': el.innerHTML = renderStats(); break;
    case 'relations': el.innerHTML = renderRelations(); break;
    case 'dialogue': el.innerHTML = renderDialogue(); break;
    case 'events': el.innerHTML = renderEvents(); break;
  }
}

function locOpts(sel) {
  return '<option value="">--</option>' + (meta.locations || []).map(function(l) {
    return '<option value="' + esc(l.key) + '"' + (String(l.key) === String(sel || '') ? ' selected' : '') + '>' + esc(l.display_name) + ' (' + esc(l.key) + ')</option>';
  }).join('');
}

function areaOpts(sel, areas) {
  var list = areas || (meta.areas || []);
  return '<option value="">--</option>' + list.map(function(a) {
    return '<option value="' + esc(a.key) + '"' + (String(a.key) === String(sel || '') ? ' selected' : '') + '>' + esc(a.display_name) + ' (' + esc(a.key) + ')</option>';
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
  var areas = meta.areas || [];

  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveInfo()">保存</button>';
  h += '<button class="btn btn-danger" style="margin-left:auto" onclick="confirmDelete()">删除角色</button>';
  h += '<span class="status" id="save-status"></span></div>';

  h += '<div class="section-title">身份</div>';
  h += '<div class="grid-3">';
  h += '<div class="form-group"><label>角色 key（不可改）</label><input id="f-key" value="' + esc(c.key || '') + '" readonly style="opacity:0.6"></div>';
  h += '<div class="form-group"><label>显示名称</label><input id="f-display_name" value="' + esc(c.display_name || '') + '"></div>';
  h += '<div class="form-group"><label>称呼（玩家对角色的昵称）</label><input id="f-nickname" value="' + esc(c.nickname || '') + '">' + help('如"企业"、"企姐"。留空则用显示名称。') + '</div>';
  h += '</div>';
  h += '<div class="grid-3">';
  h += '<div class="form-group"><label>性别</label><select id="f-gender"><option value="female"' + (c.gender === 'female' ? ' selected' : '') + '>女</option><option value="male"' + (c.gender === 'male' ? ' selected' : '') + '>男</option><option value="other"' + (c.gender === 'other' ? ' selected' : '') + '>其他</option></select></div>';
  h += '<div class="form-group"><label>船级</label><input id="f-ship_class" value="' + esc(c.ship_class || '') + '">' + help('如 航母 / 驱逐 / 重巡') + '</div>';
  h += '<div class="form-group"><label>稀有度</label><input id="f-rarity" value="' + esc(c.rarity || '') + '">' + help('如 普通/稀有/精锐/超稀有/海上传奇') + '</div>';
  h += '</div>';
  h += '<div class="form-group"><label>标签（逗号分隔）</label><input id="f-tags" value="' + esc((c.tags || []).join(', ')) + '">' + help('英文标签，如 enterprise, carrier, eagle_union, serious；同时承担性格标记（era 体系下性格由 TALENT + tags 共同体现，无独立字段）') + '</div>';
  h += '<div class="form-group"><label>角色介绍</label><textarea id="f-intro" rows="4">' + esc(c.intro || '') + '</textarea>' + help('一段角色背景描述，用于角色面板展示。') + '</div>';

  h += '<div class="section-title">归属</div>';
  h += '<div class="grid-3">';
  h += '<div class="form-group"><label>阵营 faction_key</label><input id="f-faction_key" value="' + esc(c.faction_key || '') + '">' + help('如 eagle_union, royal_navy, sakura, iron_blood, iris') + '</div>';
  h += '<div class="form-group"><label>住居区域 residence_area_key</label><select id="f-residence_area_key">' + areaOpts(c.residence_area_key, areas) + '</select>' + help('宿舍归属的区域。') + '</div>';
  h += '<div class="form-group"><label>宿舍分组 dorm_group_key</label><input id="f-dorm_group_key" value="' + esc(c.dorm_group_key || '') + '">' + help('同阵营角色共享的宿舍分组标识。') + '</div>';
  h += '</div>';
  h += '<div class="grid-2">';
  h += '<div class="form-group"><label>自宅位置 home_location_key</label><select id="f-home_location_key">' + locOpts(c.home_location_key) + '</select>' + help('角色的起居位置，派生"常去区域"和"活动时间带"。') + '</div>';
  h += '<div class="form-group"><label>默认活动标签（逗号分隔）</label><input id="f-default_activity_tags" value="' + esc((c.default_activity_tags || []).join(', ')) + '">' + help('如 work, harbor, serious；用于日程/事件匹配。') + '</div>';
  h += '</div>';

  h += '<div class="section-title">初始位置 & 日程表</div>';
  h += '<div class="form-group"><label>初始位置</label><select id="f-initial_location">' + locOpts(startLoc) + '</select>' + help('角色首次出现的位置。') + '</div>';
  h += '<div class="grid-6">';
  for (var t = 0; t < timeSlots.length; t++) {
    var ts = timeSlots[t];
    h += '<div class="form-group"><label>' + esc(ts) + '</label><select id="f-sched-' + esc(ts) + '">' + locOpts(schedule[ts] || startLoc) + '</select></div>';
  }
  h += '</div>';

  h += '<div class="section-title">礼物偏好</div>';
  h += help('标签匹配送礼时的好感加成（喜好 ×2.0，厌恶 ×0.3）。参考 gifts.toml 中的 tag。');
  var gp = c.gift_preferences || {};
  h += '<div class="grid-2">';
  h += '<div class="form-group"><label>喜爱标签（逗号分隔）</label><input id="f-gift_liked" value="' + esc((gp.liked_tags || []).join(', ')) + '"></div>';
  h += '<div class="form-group"><label>厌恶标签（逗号分隔）</label><input id="f-gift_disliked" value="' + esc((gp.disliked_tags || []).join(', ')) + '"></div>';
  h += '</div>';
  var giftTags = meta.gift_tags || [];
  if (giftTags.length) {
    h += '<div style="color:#8fa3c8;font-size:11px;margin-top:4px">可用礼物标签：' + giftTags.map(esc).join(' / ') + '</div>';
  }

  h += '<div class="section-title">饮食偏好</div>';
  h += help('与料理指令相关。tag 可自定义（如 savory/sweet/meat/sour）。');
  var fp = c.food_preferences || {};
  h += '<div class="grid-2">';
  h += '<div class="form-group"><label>喜爱标签（逗号分隔）</label><input id="f-food_liked" value="' + esc((fp.liked_tags || []).join(', ')) + '"></div>';
  h += '<div class="form-group"><label>厌恶标签（逗号分隔）</label><input id="f-food_disliked" value="' + esc((fp.disliked_tags || []).join(', ')) + '"></div>';
  h += '</div>';

  return h;
}

// ── Personal info tab ────────────────────────────────
let personalWorkCache = [];

async function ensurePersonalData() {
  if (!currentKey) return;
  const res = await fetch('/api/work_schedules?actor=' + encodeURIComponent(currentKey));
  personalWorkCache = await res.json();
  renderContent();
}

function renderPersonal() {
  var c = currentData.character || {};
  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="savePersonal()">保存工作情报</button>';
  h += '<button class="btn btn-secondary" onclick="addWorkSchedule()">+ 添加工作情报</button>';
  h += '<span class="status" id="save-status"></span></div>';

  h += '<div class="section-title">派生信息（来自基本信息/日程表，不可直接编辑）</div>';
  var personality = personalityFromTags(c.tags || []);
  var hoursLabel = derivedActivityHours(c);
  var freqAreas = derivedFrequentAreas(c);
  var homeLabel = derivedHomeLabel(c);
  h += '<div class="info-grid">';
  h += '<div><span class="info-label">性格（由 tags 推导）：</span>' + esc(personality) + '</div>';
  h += '<div><span class="info-label">活动时间带：</span>' + esc(hoursLabel) + '</div>';
  h += '<div><span class="info-label">常去区域：</span>' + esc(freqAreas) + '</div>';
  h += '<div><span class="info-label">自宅位置：</span>' + esc(homeLabel) + '</div>';
  h += '</div>';
  h += help('以上信息由"基本信息"tab 中的 tags、日程表、自宅位置派生。性格 = tags 第一个非分类标签（era 体系无独立性格字段，由 TALENT + tags 联合决定）。要修改请回"基本信息"tab。');

  h += '<div class="section-title">角色介绍</div>';
  h += '<div style="background:#16213e;border:1px solid #0f3460;border-radius:6px;padding:12px;white-space:pre-wrap;min-height:60px;color:#d0d6e2">' + esc(c.intro || '(尚未填写，请在"基本信息"tab 编辑)') + '</div>';

  h += '<div class="section-title">工作情报</div>';
  h += help('定义角色的定期工作：工种、时段、地点。保存后写入 work_schedules.toml。');
  var work = personalWorkCache || [];
  if (work.length === 0) {
    h += '<div style="color:#666;padding:10px">当前角色没有工作情报。点击"+ 添加工作情报"创建。</div>';
  }
  for (var i = 0; i < work.length; i++) {
    var w = work[i];
    h += '<div class="entry-card" data-widx="' + i + '">';
    h += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">';
    h += '<b style="color:#e94560">' + esc(w.work_label || w.work_key || '(未命名)') + '</b>';
    h += '<button class="btn btn-danger" onclick="removeWorkSchedule(' + i + ')">删除</button>';
    h += '</div>';
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>工作条目 key</label><input data-work="key" data-idx="' + i + '" value="' + esc(w.key || '') + '">' + help('如 enterprise_office_morning') + '</div>';
    h += '<div class="form-group"><label>工种 work_key</label><input data-work="work_key" data-idx="' + i + '" value="' + esc(w.work_key || '') + '">' + help('如 office_duty / patrol / maid') + '</div>';
    h += '<div class="form-group"><label>工种显示名</label><input data-work="work_label" data-idx="' + i + '" value="' + esc(w.work_label || '') + '">' + help('如 文书值班 / 夜间巡逻') + '</div>';
    h += '</div>';
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>工作地点</label><select data-work="location_key" data-idx="' + i + '">' + locOpts(w.location_key) + '</select></div>';
    h += '<div class="form-group"><label>开始时间</label><input data-work="start_time" data-idx="' + i + '" value="' + esc(w.start_time || '09:00') + '" placeholder="HH:MM"></div>';
    h += '<div class="form-group"><label>结束时间</label><input data-work="end_time" data-idx="' + i + '" value="' + esc(w.end_time || '17:00') + '" placeholder="HH:MM"></div>';
    h += '</div>';
    var rules = w.date_rules || {};
    var weekdays = (rules.weekdays || []).join(', ');
    var months = (rules.months || []).join(', ');
    var festivals = (rules.festival_tags || []).join(', ');
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>周内生效日（逗号分隔）</label><input data-work="weekdays" data-idx="' + i + '" value="' + esc(weekdays) + '" placeholder="mon, tue, wed">' + help('mon/tue/wed/thu/fri/sat/sun。留空表示每日。') + '</div>';
    h += '<div class="form-group"><label>月份（逗号分隔）</label><input data-work="months" data-idx="' + i + '" value="' + esc(months) + '" placeholder="6, 7, 8">' + help('数字 1-12。留空表示全年。') + '</div>';
    h += '<div class="form-group"><label>节日标签（逗号分隔）</label><input data-work="festival_tags" data-idx="' + i + '" value="' + esc(festivals) + '" placeholder="summer_festival"></div>';
    h += '</div>';
    h += '</div>';
  }
  return h;
}

// ── Relations tab ────────────────────────────────────
let relationsCache = [];

async function ensureRelationsData() {
  if (!currentKey) return;
  const res = await fetch('/api/relations?actor=' + encodeURIComponent(currentKey));
  relationsCache = await res.json();
  renderContent();
}

function renderRelations() {
  var curDisp = (characters.find(function(c) { return c.key === currentKey; }) || {}).display_name || currentKey;
  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveRelations()">保存</button>';
  h += '<button class="btn btn-secondary" onclick="addRelation(\'out\')">+ 本舰娘 → 其他舰娘</button>';
  h += '<button class="btn btn-secondary" onclick="addRelation(\'in\')">+ 其他舰娘 → 本舰娘</button>';
  h += '<span class="status" id="save-status"></span></div>';
  h += help('舰娘之间的有向好感预设（范围 -100~+100），不涉及玩家。A→B 与 B→A 独立，未列出默认 0。标签用于事件条件匹配。');

  var out = relationsCache.filter(function(r) { return r.from === currentKey; });
  var inn = relationsCache.filter(function(r) { return r.to === currentKey && r.from !== currentKey; });

  h += '<div class="section-title">本舰娘 → 其他舰娘（' + esc(curDisp) + ' 主动对他人的好感）</div>';
  if (out.length === 0) {
    h += '<div style="color:#666;padding:10px">暂无关系记录。</div>';
  }
  for (var i = 0; i < out.length; i++) {
    h += renderRelationCard(out[i], true);
  }
  h += '<div class="section-title">其他舰娘 → 本舰娘（他人对 ' + esc(curDisp) + ' 的好感）</div>';
  if (inn.length === 0) {
    h += '<div style="color:#666;padding:10px">暂无关系记录。</div>';
  }
  for (var i = 0; i < inn.length; i++) {
    h += renderRelationCard(inn[i], false);
  }
  return h;
}

function renderRelationCard(r, isOut) {
  var otherKey = isOut ? r.to : r.from;
  var otherDisp = characters.find(function(c) { return c.key === otherKey; });
  var otherLabel = otherDisp ? otherDisp.display_name : otherKey;
  var origin = (isOut ? 'out:' : 'in:') + r.from + ':' + r.to;
  var h = '<div class="entry-card" data-rel="' + esc(origin) + '">';
  h += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">';
  h += '<b style="color:#e94560">' + esc(otherLabel) + ' (' + esc(otherKey) + ')</b>';
  h += '<button class="btn btn-danger" onclick="removeRelation(\'' + esc(origin) + '\')">删除</button>';
  h += '</div>';
  h += '<div class="grid-3">';
  h += '<div class="form-group"><label>from</label><select data-rel-field="from">' + characterOpts(r.from) + '</select></div>';
  h += '<div class="form-group"><label>to</label><select data-rel-field="to">' + characterOpts(r.to) + '</select></div>';
  h += '<div class="form-group"><label>好感 affinity (-100~+100)</label><input type="number" data-rel-field="affinity" value="' + (r.affinity || 0) + '"></div>';
  h += '</div>';
  h += '<div class="form-group"><label>关系标签（逗号分隔）</label><input data-rel-field="tags" value="' + esc((r.tags || []).join(', ')) + '">' + help('如 姐妹舰, 挚友, 宿敌') + '</div>';
  h += '</div>';
  return h;
}

function characterOpts(sel) {
  return characters.map(function(c) {
    return '<option value="' + esc(c.key) + '"' + (c.key === sel ? ' selected' : '') + '>' + esc(c.display_name) + ' (' + esc(c.key) + ')</option>';
  }).join('');
}

// ── Personal/Relations data helpers ──────────────────
function personalityFromTags(tags) {
  var category = ['destroyer', 'carrier', 'cruiser', 'battleship', 'eagle_union', 'royal_navy', 'sakura', 'iron_blood', 'iris'];
  for (var i = tags.length - 1; i >= 1; i--) {
    if (category.indexOf(tags[i]) === -1) return tags[i];
  }
  return '普通';
}

function derivedActivityHours(c) {
  var slotRange = {
    dawn: [5, 8], morning: [8, 12], afternoon: [12, 17],
    evening: [17, 20], night: [20, 24], late_night: [0, 5]
  };
  var home = c.home_location_key || '';
  var schedule = c.schedule || {};
  var starts = [], ends = [];
  for (var slot in schedule) {
    if (schedule[slot] === home) continue;
    if (!slotRange[slot]) continue;
    starts.push(slotRange[slot][0]);
    ends.push(slotRange[slot][1]);
  }
  if (starts.length === 0) return '—';
  var s = Math.min.apply(null, starts);
  var e = Math.max.apply(null, ends);
  if (e === 0) e = 24;
  return s + '时～' + e + '时';
}

function derivedFrequentAreas(c) {
  var schedule = c.schedule || {};
  var seen = {};
  var labels = [];
  for (var slot in schedule) {
    var loc = (meta.locations || []).find(function(l) { return l.key === schedule[slot]; });
    if (loc && loc.zone && !seen[loc.zone]) {
      seen[loc.zone] = true;
      labels.push(loc.zone);
    }
  }
  return labels.length ? labels.join(' / ') : '—';
}

function derivedHomeLabel(c) {
  var home = c.home_location_key;
  if (!home) return '—';
  var loc = (meta.locations || []).find(function(l) { return l.key === home; });
  return loc ? loc.display_name + ' (' + home + ')' : home;
}

// ── Personal/Relations save ─────────────────────────
function collectWorkFromDOM() {
  var cards = document.querySelectorAll('#content .entry-card[data-widx]');
  var schedules = [];
  cards.forEach(function(card) {
    var w = {};
    card.querySelectorAll('input[data-work],select[data-work]').forEach(function(el) {
      var k = el.dataset.work;
      if (k === 'weekdays' || k === 'festival_tags') {
        w._rules = w._rules || {};
        w._rules[k] = el.value.split(',').map(function(s){return s.trim();}).filter(Boolean);
      } else if (k === 'months') {
        w._rules = w._rules || {};
        w._rules[k] = el.value.split(',').map(function(s){return parseInt(s.trim(),10);}).filter(function(n){return !isNaN(n);});
      } else {
        w[k] = el.value;
      }
    });
    w.actor_key = currentKey;
    w.date_rules = w._rules || {};
    delete w._rules;
    schedules.push(w);
  });
  return schedules;
}

async function savePersonal() {
  var updated = collectWorkFromDOM();
  // Merge: drop current actor's entries, then append the updated ones
  const allRes = await fetch('/api/work_schedules');
  const all = await allRes.json();
  const filtered = all.filter(function(s) { return s.actor_key !== currentKey; });
  const merged = filtered.concat(updated);
  const res = await fetch('/api/work_schedules', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(merged),
  });
  await res.json();
  personalWorkCache = updated;
  flash('已保存');
  renderContent();
}

function addWorkSchedule() {
  personalWorkCache = personalWorkCache || [];
  personalWorkCache.push({
    key: currentKey + '_work_' + Date.now(),
    actor_key: currentKey,
    location_key: '',
    work_key: '',
    work_label: '',
    start_time: '09:00',
    end_time: '17:00',
    date_rules: { weekdays: ['mon','tue','wed','thu','fri'] },
  });
  renderContent();
}

function removeWorkSchedule(idx) {
  personalWorkCache.splice(idx, 1);
  renderContent();
}

function collectRelationsFromDOM() {
  var cards = document.querySelectorAll('#content .entry-card[data-rel]');
  var out = [];
  cards.forEach(function(card) {
    var r = { from: '', to: '', affinity: 0, tags: [] };
    card.querySelectorAll('[data-rel-field]').forEach(function(el) {
      var k = el.dataset.relField;
      if (k === 'affinity') {
        r.affinity = parseInt(el.value, 10) || 0;
      } else if (k === 'tags') {
        r.tags = el.value.split(',').map(function(s){return s.trim();}).filter(Boolean);
      } else {
        r[k] = el.value;
      }
    });
    if (r.from && r.to) out.push(r);
  });
  return out;
}

async function saveRelations() {
  var updated = collectRelationsFromDOM();
  // Merge: drop current actor's entries (from or to == currentKey), then append
  const allRes = await fetch('/api/relations');
  const all = await allRes.json();
  const filtered = all.filter(function(r) { return r.from !== currentKey && r.to !== currentKey; });
  const merged = filtered.concat(updated);
  const res = await fetch('/api/relations', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(merged),
  });
  await res.json();
  relationsCache = updated;
  flash('已保存');
  renderContent();
}

function addRelation(direction) {
  var other = characters.find(function(c) { return c.key !== currentKey; });
  if (!other) { alert('需要至少两个角色才能建立关系'); return; }
  relationsCache.push({
    from: direction === 'out' ? currentKey : other.key,
    to: direction === 'out' ? other.key : currentKey,
    affinity: 0,
    tags: [],
  });
  renderContent();
}

function removeRelation(origin) {
  var updated = collectRelationsFromDOM();
  var parts = origin.split(':');
  var fromKey = parts[1];
  var toKey = parts[2];
  relationsCache = updated.filter(function(r) {
    return !(r.from === fromKey && r.to === toKey);
  });
  renderContent();
}

// ── Stats tab ─────────────────────────────────────────
// ABL 按业务含义重新分区。只显示编辑器中真正需要的条目；
// abl_42(战斗能力) 在 skills 中被剔除 —— 保留在数据里但不对编辑器暴露。
var ABL_GROUPS = [
  {title: '感觉（感官敏感度）', keys: [0, 1, 2, 3, 4]},
  {title: '心性（核心成长）', keys: [9, 10, 11, 12, 13]},
  {title: '倾向（属性偏好）', keys: [14, 15, 16, 17]},
  {title: '中毒（依赖状态）', keys: [30, 31, 32, 34, 35]},
  {title: '性技', keys: [50, 51, 52, 53, 54, 55]},
  {title: '技能（游戏五大技能）', keys: [43, 41, 44, 45, 40]}
];

// TALENT 分区（基于 section 字段自动分组；此常量仅用于排序提示）

function renderStats() {
  var h = '<div class="save-bar"><button class="btn btn-primary" onclick="saveStats()">保存</button><span class="status" id="save-status"></span></div>';

  // ── BASE：只暴露体力/气力上限 ──
  var baseCurrent = currentData.base || {};
  h += '<div class="section-title">BASE — 体力 / 气力 上限</div>';
  h += help('这里设置本角色的体力/气力上限。进入游戏时当前值默认等于上限（满）。其他 BASE 轴（射精/母乳/醉意等）由游戏运行时维护，编辑器不暴露。');
  h += '<div class="stat-grid">';
  h += '<div class="stat-item"><label>体力上限</label>';
  h += '<input type="number" data-section="base" data-field="stamina" value="' + (baseCurrent.stamina != null ? baseCurrent.stamina : 2000) + '" min="1"></div>';
  h += '<div class="stat-item"><label>气力上限</label>';
  h += '<input type="number" data-section="base" data-field="spirit" value="' + (baseCurrent.spirit != null ? baseCurrent.spirit : 1500) + '" min="1"></div>';
  h += '</div>';

  // ── PALAM：通常初始为 0，但允许少数特殊角色预置 ──
  var palamAxes = (meta.stat_axes || {}).palam || [];
  var palamCurrent = currentData.palam || {};
  h += '<div class="section-title">PALAM（累积参数，初始值）</div>';
  h += help('通过指令 SOURCE 结算后累积。绝大多数角色初始全为 0；特殊设定（如开局就对玩家怀有羞情/好意）才填。');
  h += '<div class="stat-grid">';
  for (var i = 0; i < palamAxes.length; i++) {
    var ax = palamAxes[i];
    var val = palamCurrent[ax.key] != null ? palamCurrent[ax.key] : 0;
    h += '<div class="stat-item"><label title="' + esc(ax.key) + '">' + esc(ax.label || ax.key) + '</label>';
    h += '<input type="number" data-section="palam" data-field="' + esc(ax.key) + '" value="' + val + '"></div>';
  }
  h += '</div>';

  // ── ABL（能力）：按业务分区展示 ──
  var ablAxes = (meta.stat_axes || {}).abl || [];
  var ablByIdx = {};
  for (var i = 0; i < ablAxes.length; i++) {
    ablByIdx[ablAxes[i].era_index] = ablAxes[i];
  }
  var ablCurrent = currentData.abl || {};
  h += '<div class="section-title">ABL（能力等级）</div>';
  h += help('通过指令积累经验后升级。"技能"列是游戏的五大技能：教养/话术/料理/艺术/整备。战斗能力为系统内部使用，不在编辑器暴露。');
  for (var g = 0; g < ABL_GROUPS.length; g++) {
    var group = ABL_GROUPS[g];
    h += '<div style="margin:8px 0 4px;color:#9fb3d9;font-size:12px;font-weight:600">' + esc(group.title) + '</div>';
    h += '<div class="stat-grid">';
    for (var k = 0; k < group.keys.length; k++) {
      var idx = group.keys[k];
      var reg = ablByIdx[idx];
      if (!reg) continue;
      var fieldKey = String(idx);
      var val = ablCurrent[fieldKey] != null ? ablCurrent[fieldKey] : 0;
      h += '<div class="stat-item"><label title="abl_' + idx + '">' + esc(reg.label || reg.key) + '</label>';
      h += '<input type="number" data-section="abl" data-field="' + esc(fieldKey) + '" value="' + val + '"></div>';
    }
    h += '</div>';
  }

  // ── TALENT（素质）：按 group 分组 ──
  var talentAxes = (meta.stat_axes || {}).talent || [];
  var talentCurrent = currentData.talent || {};
  h += '<div class="section-title">TALENT（素质）</div>';
  h += help('角色的先天素质。0=无，1=有，-1=相反素质。带区间的（如 体型/胸围/C感度）是等级值。性别默认女不可改。');
  h += '<div class="stat-grid">';
  for (var i = 0; i < talentAxes.length; i++) {
    var ax = talentAxes[i];
    var fieldKey = String(ax.era_index);
    var val = talentCurrent[fieldKey] != null ? talentCurrent[fieldKey] : 0;
    var isGender = ax.era_index === 2;
    var readonlyAttr = isGender ? ' readonly title="舰娘性别默认为女，不可修改"' : '';
    var labelExtra = isGender ? '（舰娘：女，锁定）' : '';
    h += '<div class="stat-item"><label title="' + esc(ax.key) + ' [' + ax.era_index + ']">' + esc(ax.label || ax.key) + labelExtra + '</label>';
    h += '<input type="number" data-section="talent" data-field="' + esc(fieldKey) + '" value="' + (isGender ? 0 : val) + '"' + readonlyAttr + (isGender ? ' style="opacity:0.5"' : '') + '></div>';
  }
  h += '</div>';

  // CFLAG 整组不暴露。游戏运行时自动维护，默认初值 0。

  // ── MARK（印记） ──
  var marks = currentData.marks || {};
  var markLines = [];
  for (var mk in marks) markLines.push(mk + '=' + marks[mk]);
  h += '<div class="section-title">MARK（印记）</div>';
  h += help('角色身上的印记，如 dislike_mark（反感刻印）。格式：每行一个 key=level。');
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
    h += '<div class="grid-3">';
    h += '<div class="form-group"><label>需要调教中</label><select data-dlg="requires_training" data-idx="' + i + '">' + boolOpts(e.requires_training) + '</select></div>';
    h += '<div class="form-group"><label>需要已脱除槽位（逗号分隔）</label><input data-dlg="required_removed_slots" data-idx="' + i + '" value="' + esc((e.required_removed_slots || []).join(', ')) + '">' + help('如 underwear_bottom, top') + '</div>';
    h += '<div class="form-group"><label>需要调教结果（逗号分隔）</label><input data-dlg="required_training_results" data-idx="' + i + '" value="' + esc((e.required_training_results || []).join(', ')) + '">' + help('如 orgasm_c, rejected') + '</div>';
    h += '<div class="form-group"><label>需要记忆（逗号分隔 key=min）</label><input data-dlg="required_memories" data-idx="' + i + '" value="' + esc(Object.entries(e.required_memories || {}).map(([k,v])=>k+'='+v).join(', ')) + '">' + help('如 cmd:kiss=3, evt:first_date=1') + '</div>';
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
  c.nickname = document.getElementById('f-nickname').value;
  c.intro = document.getElementById('f-intro').value;
  c.gender = document.getElementById('f-gender').value;
  c.ship_class = document.getElementById('f-ship_class').value;
  c.rarity = document.getElementById('f-rarity').value;
  c.faction_key = document.getElementById('f-faction_key').value;
  c.residence_area_key = document.getElementById('f-residence_area_key').value;
  c.dorm_group_key = document.getElementById('f-dorm_group_key').value;
  c.home_location_key = document.getElementById('f-home_location_key').value;
  c.tags = document.getElementById('f-tags').value.split(',').map(s => s.trim()).filter(Boolean);
  c.default_activity_tags = document.getElementById('f-default_activity_tags').value.split(',').map(s => s.trim()).filter(Boolean);
  c.initial_location = document.getElementById('f-initial_location').value;
  c.schedule = {};
  for (const ts of meta.time_slots) {
    c.schedule[ts] = document.getElementById('f-sched-' + ts).value;
  }
  var giftLiked = document.getElementById('f-gift_liked').value.split(',').map(s => s.trim()).filter(Boolean);
  var giftDisliked = document.getElementById('f-gift_disliked').value.split(',').map(s => s.trim()).filter(Boolean);
  c.gift_preferences = { liked_tags: giftLiked, disliked_tags: giftDisliked };
  var foodLiked = document.getElementById('f-food_liked').value.split(',').map(s => s.trim()).filter(Boolean);
  var foodDisliked = document.getElementById('f-food_disliked').value.split(',').map(s => s.trim()).filter(Boolean);
  c.food_preferences = { liked_tags: foodLiked, disliked_tags: foodDisliked };
  currentData.character = c;
  await saveAll(currentData);
  await loadList();
  flash('已保存');
}

async function saveStats() {
  // 编辑器只负责 base/palam/abl/talent/marks，CFLAG 整组由运行时维护，不在此覆写
  var sections = ['base', 'palam', 'abl', 'talent'];
  for (var si = 0; si < sections.length; si++) {
    var sec = sections[si];
    var inputs = document.querySelectorAll('input[data-section="' + sec + '"]');
    if (inputs.length === 0) continue;
    var obj = {};
    inputs.forEach(function(inp) {
      var val = parseInt(inp.value) || 0;
      if (val !== 0) obj[inp.dataset.field] = val;
    });
    // 性别永远锁定为 0（女）——不论 UI 传了什么
    if (sec === 'talent') { delete obj['2']; }
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
      if (inp.dataset.dlg === 'time_slots' || inp.dataset.dlg === 'location_keys' || inp.dataset.dlg === 'required_removed_slots' || inp.dataset.dlg === 'required_training_results') {
        e[inp.dataset.dlg] = inp.value.split(',').map(function(s){return s.trim();}).filter(Boolean);
      } else if (inp.dataset.dlg === 'required_memories') {
        var mm = {};
        inp.value.split(',').map(function(s){return s.trim();}).filter(Boolean).forEach(function(pair) {
          var parts = pair.split('=');
          mm[parts[0]] = parseInt(parts[1] || '1');
        });
        e.required_memories = mm;
      } else {
        e[inp.dataset.dlg] = inp.value;
      }
    });
    card.querySelectorAll('select[data-dlg]').forEach(function(sel) {
      if (sel.dataset.dlg === 'action_key') {
        e.action_key = sel.value || '';
      } else if (sel.dataset.dlg === 'required_stage') {
        e.required_stage = sel.value || null;
      } else if (sel.dataset.dlg === 'requires_private' || sel.dataset.dlg === 'requires_date' || sel.dataset.dlg === 'requires_training') {
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

    if args.root:
        root = Path(args.root)
    else:
        # src/eral/tools/editor.py -> parents[3] is project root (erAL)
        root = Path(__file__).resolve().parents[3]
        # Fallback for unusual launch layouts: prefer current working directory if it has data files.
        cwd_root = Path.cwd()
        if not (_port_map_path(root).exists() and _commands_path(root).exists()) and (
            _port_map_path(cwd_root).exists() and _commands_path(cwd_root).exists()
        ):
            root = cwd_root

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

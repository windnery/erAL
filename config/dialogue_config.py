"""口上（对白）action 契约与 json schema 规范。

本模块是口上系统的**单一事实来源**：
- ``ACTION_CONTRACT`` 定义当前全部可触发口上的 action key，供覆盖率脚本与工具链使用；
- 模块 docstring 定义 json 口上数据格式与 ``when`` 条件标签词汇表。

新增指令的 DoD 必须包含：在 ``ACTION_CONTRACT`` 中登记 action key，
并在至少一个角色上给出通用 fallback 文本。

--------------------------------------------------------------------------
json 口上数据格式（``data/dialogue/<chara_id>.json``）
--------------------------------------------------------------------------

::

    {
      "id": "javelin",
      "actions": {
        "first_encounter": [
          {"variants": [["第一句", "第二句"]]}
        ],
        "talk": [
          {"when": {"relationship": 4, "dating": true}, "variants": [[...], [...]]},
          {"when": {"relationship": 3},                "variants": [[...]]},
          {"variants": [["兜底台词"]]}
        ]
      }
    }

- ``actions``：action key -> 条目列表（有序）。
- 每个条目：
  - ``when``（可选）：条件字典，见下方词汇表；省略表示无条件命中。
  - ``variants``（必填）：场景列表，每个场景是字符串列表（与 Python 口上返回结构一致）。
- **选择语义与 Python 版 if/elif 完全一致**：按条目顺序取**第一个** ``when`` 命中的条目，
  再在其中 ``variants`` 内随机选一个场景。需要并行分支时写多个条目。
- 文本占位符：``{name}`` -> 玩家名，``{chara}`` -> 舰娘名，渲染时替换。
- 找不到 json 或 json 无该 action 时，自动回退到 Python 模块（逃生舱），
  Python 端可继续写复杂条件逻辑。

--------------------------------------------------------------------------
``when`` 条件标签词汇表（最小集，够用即可扩展）
--------------------------------------------------------------------------

- ``relationship``: int 或 int 列表或 ``{"min": int, "max": int}``
  陷落阶段，对应 talent ``relationship``（0 陌生 / 1 友好 / 2 喜欢 / 3 爱 / 4 誓约）。
- ``lover``: bool —— 是否拥有 talent ``lover``（恋人）。
- ``dating``: bool —— cflag ``dating``（约会中）。
- ``flags``: ``{"any": [...], "all": [...], "not": [...]}`` —— cflag 判定，
  可用键见 ``config/cflag_config.py`` 与源码（sleeping/working/resting/following/
  secretary_ship/unconscious/have_encountered/tired 等）。
- ``talents``: ``{"any": [...], "all": [...], "not": [...]}`` —— talent 存在性判定。
- ``talent_values``: ``{talent_key: int | [int, ...]}`` —— talent 数值判定，
  如 ``{"virgin": 1, "sense_of_shame": [0, 1]}``。
- ``marks``: ``{mark_key: {"min": int}}`` —— 刻印等级下限，如 ``{"disappointment_mark": {"min": 1}}``。
- ``mood``: int 或 ``{"min": int, "max": int}`` —— 心情（-1 生气 / 0 普通 / 1 好心情 / 2 幸福）。
- ``outcome``: ``"success"`` | ``"fail"`` —— 带成功率判定的指令的结果分支；
  仅在调用方传入对应 ``outcome`` 时命中（见各 action 的 ``outcomes`` 字段）。
- ``favor`` / ``trust``: ``{"min": int, "max": int}`` —— 数值区间判定（能用 relationship 表达时优先用 relationship）。

同一 ``when`` 内多个键为**与**关系；列表类型的值为**或**关系。
"""

from __future__ import annotations

# ==============================================================================
# action 契约（当前全部可触发口上的 action key）
# 字段：name 中文名 / cat 分类 / source 触发点 / outcomes 结果分支 / note 备注
# 本表以「全部已注册指令与事件」为基准盘点，不以任何单个角色的现有口上为准。
# ==============================================================================

ACTION_CONTRACT: dict[str, dict] = {
    # ---------------- 日常 ----------------
    "talk": {"name": "会话", "cat": "日常", "source": "commands/interact/talk.py"},
    "listen_to_complaints": {"name": "听牢骚", "cat": "日常", "source": "commands/interact/listen_to_complaints.py"},
    "relax_together": {"name": "一起放松", "cat": "日常", "source": "commands/interact/relax_together.py"},
    "work_together": {"name": "一起工作", "cat": "日常", "source": "commands/interact/work_together.py"},
    "invite_date": {"name": "约会邀请", "cat": "日常", "source": "commands/interact/invite_date.py", "outcomes": ("success", "fail")},
    "invite_follow": {"name": "邀请同行", "cat": "日常", "source": "commands/interact/invite_follow.py", "outcomes": ("success", "fail")},
    "cancel_follow": {"name": "解除同行", "cat": "日常", "source": "commands/interact/cancel_follow.py"},
    "confess": {"name": "告白", "cat": "日常", "source": "commands/interact/confess.py", "outcomes": ("success", "fail")},
    "oath": {"name": "誓约", "cat": "日常", "source": "commands/interact/oath.py", "outcomes": ("success", "fail")},

    # ---------------- 亲昵 ----------------
    "hug": {"name": "拥抱", "cat": "亲昵", "source": "commands/interact/hug.py"},
    "body_touch": {"name": "身体接触", "cat": "亲昵", "source": "commands/interact/body_touch.py"},
    "kiss_i": {"name": "亲吻", "cat": "亲昵", "source": "commands/interact/kiss_i.py", "outcomes": ("success", "fail")},
    "rub_the_head": {"name": "摸头", "cat": "亲昵", "source": "commands/interact/rub_the_head.py"},
    "pinching_cheeks": {"name": "捏脸颊", "cat": "亲昵", "source": "commands/interact/pinching_cheeks.py"},
    "poke_the_cheek": {"name": "戳脸颊", "cat": "亲昵", "source": "commands/interact/poke_the_cheek.py"},
    "request_a_lap_pillow": {"name": "索求膝枕", "cat": "亲昵", "source": "commands/interact/request_a_lap_pillow.py"},

    # ---------------- 性骚扰 ----------------
    "push_down": {"name": "推倒", "cat": "性骚扰", "source": "commands/interact/push_down.py", "outcomes": ("success", "fail")},
    "breast_caress_i": {"name": "胸爱抚（骚扰）", "cat": "性骚扰", "source": "commands/interact/breast_caress_i.py"},
    "ass_caress_i": {"name": "肛门爱抚（骚扰）", "cat": "性骚扰", "source": "commands/interact/ass_caress_i.py"},
    "pussy_caress_i": {"name": "秘穴爱抚（骚扰）", "cat": "性骚扰", "source": "commands/interact/pussy_caress_i.py"},
    "finger_insert_i": {"name": "指插入（骚扰）", "cat": "性骚扰", "source": "commands/interact/finger_insert_i.py"},
    "rub_the_belly": {"name": "抚摸肚子", "cat": "性骚扰", "source": "commands/interact/rub_the_belly.py"},
    "rub_the_butt": {"name": "摸屁股", "cat": "性骚扰", "source": "commands/interact/rub_the_butt.py"},

    # ---------------- 调教 ----------------
    "kiss": {"name": "亲吻", "cat": "调教", "source": "commands/train/kiss.py"},
    "caress": {"name": "爱抚", "cat": "调教", "source": "commands/train/caress.py"},
    "breast_caress": {"name": "胸爱抚", "cat": "调教", "source": "commands/train/breast_caress.py"},
    "breast_massage": {"name": "揉胸", "cat": "调教", "source": "commands/train/breast_massage.py"},
    "nipple_caress": {"name": "玩弄乳头", "cat": "调教", "source": "commands/train/nipple_caress.py"},
    "nipple_sucking": {"name": "吸乳头", "cat": "调教", "source": "commands/train/nipple_sucking.py"},
    "ass_caress": {"name": "抚摸臀部", "cat": "调教", "source": "commands/train/ass_caress.py"},
    "spread_the_ass": {"name": "扒开臀瓣", "cat": "调教", "source": "commands/train/spread_the_ass.py", "outcomes": ("success", "fail")},
    "spread_the_labia": {"name": "扒开阴唇", "cat": "调教", "source": "commands/train/spread_the_labia.py", "outcomes": ("success", "fail")},
    "finger_insert": {"name": "手指插入", "cat": "调教", "source": "commands/train/finger_insert.py"},
    "pussy_caress": {"name": "秘穴爱抚", "cat": "调教", "source": "commands/train/pussy_caress.py"},
    "lick_pussy": {"name": "舔阴", "cat": "调教", "source": "commands/train/lick_pussy.py"},
    "lick_ass": {"name": "舔肛", "cat": "调教", "source": "commands/train/lick_ass.py"},
    "common_position": {"name": "正常位", "cat": "调教", "source": "commands/train/common_position.py"},
    "do_nothing": {"name": "什么都不做", "cat": "调教", "source": "commands/train/do_nothing.py"},

    # ---------------- 调教差分 ----------------
    "defloration": {"name": "破处", "cat": "差分", "source": "commands/train/common_position.py", "note": "处女丧失时插入"},
    "ejaculation": {"name": "射精", "cat": "差分", "source": "commands/_common.py", "note": "调教中玩家射精"},

    # ---------------- 事件 ----------------
    "first_encounter": {"name": "初次见面", "cat": "事件", "source": "managers/TimeManager.py"},
    "date_end": {"name": "约会道别", "cat": "事件", "source": "events/date/date_end_normal.py"},
    "date_end_kiss": {"name": "归途初吻", "cat": "事件", "source": "events/date/date_end_kiss.py"},
    "date_end_confess": {"name": "归途告白", "cat": "事件", "source": "events/date/date_end_confess.py"},
    "date_end_confess_reject": {"name": "归途告白被拒", "cat": "事件", "source": "events/date/date_end_confess.py"},
    "date_end_disappointment_clear": {"name": "消除失望刻印", "cat": "事件", "source": "events/date/date_end_disappointment_clear.py"},
}

# 需要覆盖率脚本检查的 action（当前=全部）
REQUIRED_ACTIONS: tuple[str, ...] = tuple(ACTION_CONTRACT.keys())

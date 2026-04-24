# TW 计算公式迁移策略

**分析日期**: 2026-04-23
**核心结论**: TW 的公式不是"几百条独立规则"，而是"五六种模式重复几百次"。不需要一条条翻译，只需要把模式批量迁移到 erAL 的数据/代码架构中。

---

## 1. TW 公式的五种核心模式

我读完 TW 的 COMF、SOURCE、SOURCE_EXTRA、TRACHECK 系列文件后，所有公式可以归纳为以下模式：

### 模式 A：基础值 + ABL 线性加成

```erb
SOURCE:快Ｃ = 40
SOURCE:快Ｃ += ABL:PLAYER:指 * 4
```

**在 erAL 中的映射**:
- 当前 `commands.toml` 的 `[commands.source]` 只支持静态值。
- 需要扩展为支持 `"abl_bonus": {"who": "player", "key": "abl_50", "scale": 4}`。

### 模式 B：TALENT 条件乘算

```erb
IF TALENT:PLAYER:器用な指
    TIMES SOURCE:快Ｃ , 1.50
ENDIF
IF TALENT:自己愛 < 0 || TALENT:抵抗
    SOURCE:鬱屈 += 20
ENDIF
```

**在 erAL 中的映射**:
- 已有 `source_extra.py` 做全局 TALENT 乘算，但**只覆盖了部分 TALENT**。
- 关系状态 TALENT（恋慕/服従/淫乱/恋人/思慕）全部 deferred，等于**没接**。
- 需要把 deferred 的 TALENT 接入，并扩展到**指令级别**的条件判断。

### 模式 C：状态条件修正

```erb
IF 接吻
    SOURCE:快Ｍ = 20 + ABL:PLAYER:舌 * 3
ENDIF
IF CFLAG:睡眠
    TIMES SOURCE:恭順 , 0.10
ENDIF
IF FLAG:70 == 1  ;时间停止
    BASE:MASTER:TSP -= 20
    SOURCE:快Ｃ = 40
ENDIF
```

**在 erAL 中的映射**:
- erAL 没有等价的状态条件系统。
- 需要增加 `"condition_bonuses"` 配置，或部分用代码实现。

### 模式 D：药物/环境全局修正

```erb
IF TCVAR:発情
    TIMES CUP:恭順 , 1.50
    TIMES CUP:欲情 , 2.00
ENDIF
IF TCVAR:媚薬
    TIMES CUP:恭順 , 1.20
    TIMES CUP:欲情 , 1.50
ENDIF
IF TCVAR:烂醉
    TIMES CUP:恭順 , 0.30
ENDIF
```

**在 erAL 中的映射**:
- erAL **没有药物系统**。
- 需要新增 `DrugStatus` 或类似机制，并在 `source_extra.py` 中接入修正。

### 模式 E：技巧/好感度/情绪的分段函数

```erb
;好感度加成
@MASTER_FAVOR_CHECK(ARG,ARG:1)
RETURNF GET_REVISION(CFLAG:ARG:2, 200, 20000) + 100

;技巧加成
@TECHNIQUE_CHECK(ARG,ARG:1)
RETURNF GET_REVISION(ABL:(TCVAR:ARG:116):技巧 + 2, 500, 10)

;情绪加成
@MOOD_CHECK(ARG,ARG:1)
;...分段函数
```

**在 erAL 中的映射**:
- `favor_calc.py` 已有好感度/信赖度计算，但**没有 TW 的分段加成公式**。
- 需要把 `GET_REVISION` 这类函数翻译成 Python，接入结算流程。

---

## 2. erAL 当前结算流程 vs TW 结算流程

### erAL 当前流程（简图）

```
commands.toml [静态 SOURCE]
    ↓
actor.stats.source.add(静态值)
    ↓
source_extra.py [TALENT 乘算 + 刻印效果]
    ↓
settlement_rules.toml [SOURCE → PALAM/BASE/CFLAG]
    ↓
favor_calc.py [好感度/信赖度计算]
```

### TW 完整流程（简图）

```
COMF [动态 SOURCE = 基础值 + ABL加成 + TALENT条件]
    ↓
SOURCE_EXTRA [全局修正：药物/状态/关系TALENT]
    ↓
TRACHECK [好感度/技巧/情绪分段加成]
    ↓
CUP累积 [SOURCE → CUP]
    ↓
PALAM结算 [CUP → PALAM]
    ↓
MARK_GOT_CHECK [刻印取得判定 + ABL副作用]
    ↓
ABLUP [ABL升级检查]
```

### 差距总结

| TW 阶段 | erAL 对应 | 状态 |
|---------|----------|------|
| COMF 动态 SOURCE | commands.toml 静态 SOURCE | ❌ 缺失动态计算 |
| SOURCE_EXTRA 全局修正 | source_extra.py | ⚠️ 部分覆盖，缺少药物/关系TALENT |
| TRACHECK 分段加成 | favor_calc.py | ⚠️ 公式不同，缺少技巧/情绪加成 |
| CUP 累积 | settlement | ✅ 基本等价 |
| 刻印取得 + ABL副作用 | imprint.py + marks | ⚠️ 只有阈值判定，缺少副作用 |
| ABL 升级 | abl_upgrade.py | ⚠️ 有经验曲线但缺少升级条件检查 |

---

## 3. 推荐迁移方案：混合策略

不要全部翻译，也不要全部数据化。按**复杂度分层**处理：

### 第一层：数据层扩展（简单模式 A）

扩展 `commands.toml`，增加 `source_formula` 字段：

```toml
[[commands]]
key = "caress"
display_name = "爱抚"

[commands.source_formula]
# 基础值 + ABL 加成模式
pleasure_c = { base = 40, abl_bonuses = [
    { who = "player", key = "abl_50", scale = 4 }
]}
pleasure_b = { base = 40, abl_bonuses = [
    { who = "player", key = "abl_50", scale = 4 }
]}
pleasure_m = { base = 20, abl_bonuses = [
    { who = "player", key = "abl_51", scale = 3 }
], condition = "kissing" }

affection = { base = 50 }
sexual_act = { base = 60 }
exposure = { base = 20 }
unclean = { base = 30 }
deviation = { base = 20 }
disgust = { base = 20 }
```

**工作量**: 为 50~100 条指令写公式配置，每条 5~10 行。

### 第二层：代码层扩展（复杂模式 B/C）

在 `source_extra.py` 旁边新增 `source_conditions.py`，处理无法用纯数据表达的条件：

```python
def apply_command_conditions(
    actor: CharacterState,
    player: CharacterState,
    command_key: str,
    scene: SceneContext,
) -> dict[str, int]:
    """Apply conditional SOURCE modifiers ( Mode B & C from TW )."""
    deltas = {}
    
    # 接吻加成
    if scene.has_condition("kissing"):
        deltas["pleasure_m"] = 20 + player.compat.abl.get(51, 0) * 3
    
    # 压抑/抵抗 → 郁屈
    if actor.compat.talent.get(32, 0) > 0 or actor.compat.talent.get(20, 0) < 0:
        deltas["frustration"] = 20
    
    # 睡眠状态修正（如果实现了）
    if actor.compat.cflag.get(313, 0):  # CFLAG:313=睡眠
        for key in ["obedience", "lust", "submission"]:
            current = actor.stats.source.get(key, 0)
            if current > 0:
                actor.stats.source.set(key, int(current * 0.1))
    
    return deltas
```

**工作量**: 一个通用条件处理器，100~200 行代码。

### 第三层：全局修正扩展（模式 D/E）

扩展 `source_extra.py`，接入：

1. **药物状态**（新增 `DrugStatus` 数据结构）
2. **关系状态 TALENT**（把 deferred 的接入）
3. **技巧检查**（`GET_REVISION` 翻译）
4. **好感度/情绪分段加成**

```python
# 新增：药物修正
def apply_drug_effects(actor: CharacterState) -> None:
    drugs = actor.conditions.get("drugs", {})
    if drugs.get("aphrodisiac"):  # 媚药
        _scale_source(actor, "obedience", 1.2)
        _scale_source(actor, "lust", 1.5)
    if drugs.get("estrus"):  # 发情
        _scale_source(actor, "obedience", 1.5)
        _scale_source(actor, "lust", 2.0)

# 新增：关系状态 TALENT 修正
def apply_relationship_talents(actor: CharacterState) -> None:
    # 恋慕
    if actor.compat.talent.get(3, 0) > 0:
        _scale_source(actor, "obedience", 1.5)
        _scale_source(actor, "favor", 1.5)
        _scale_source(actor, "disgust", 0.2)
    # 服従
    if actor.compat.talent.get(5, 0) > 0:
        _scale_source(actor, "obedience", 1.5)
        _scale_source(actor, "submission", 1.5)
```

**工作量**: 200~300 行代码，接入 10~15 个关键 TALENT。

### 第四层：刻印副作用 + ABL 升级（模式 E 的后续）

扩展 `imprint.py` 和 `abl_upgrade.py`：

1. **刻印取得后 ABL 升级**: 痛苦刻印 Lv1 取得时，如果顺从=0 且胆量>0，则顺从=1。
2. **ABL 升级条件检查**: 不只是经验够就升级，还要检查前置条件。

**工作量**: 100~150 行代码。

---

## 4. 分批实施计划

### 第一批（1~2 周）：基础动态化

1. **扩展 commands.toml 格式**：支持 `source_formula`。
2. **写 SourceFormulaCalculator**：解析公式配置，计算动态 SOURCE。
3. **迁移高频指令**：先把 chat、touch_head、caress 等 10~20 条日常指令从静态改为动态。

**验收标准**: `caress` 指令的 pleasure_c 会随玩家 abl_50(指) 变化。

### 第二批（2~3 周）：TALENT 全面接入

1. **把 deferred 的关系状态 TALENT 接入 source_extra**。
2. **写药物状态系统和修正**。
3. **写技巧检查（TECHNIQUE_CHECK）**。

**验收标准**: 有恋慕 TALENT 的角色，接受互动时好感度加成明显高于无恋慕角色。

### 第三批（2~3 周）：刻印 + ABL 副作用

1. **刻印取得后的 ABL 副作用**。
2. **ABL 升级条件检查**。
3. **好感度/情绪的分段加成**。

**验收标准**: 取得痛苦刻印后，顺从自动升到 1。

### 第四批（持续）：指令全覆盖

1. 把剩余 100+ 条指令的 SOURCE 公式从 TW 迁移过来。
2. 每条指令只需要写 TOML 配置，不需要改代码。

---

## 5. 不是"翻译"而是"映射"

最关键的心态调整：**不要试图让 erAL 的代码和 TW 的 ERB 一一对应**。

TW 的 ERB 是过程式代码，erAL 是数据驱动架构。正确的做法是：

1. **提取 TW 公式的"意图"**（这条指令应该产生多少快感？受什么影响？）。
2. **用 erAL 的架构表达同样的意图**（TOML 配置 + Python 计算器）。
3. **数值不需要完全复刻**，保持同一数量级和相对关系即可。

例如 TW 的 `GET_REVISION(CFLAG:2, 200, 20000)` 可以翻译成：

```python
def favor_bonus(affection: int) -> float:
    # 好感度 0→200 时从 100 线性增长到 200
    # 好感度 200→20000 时从 200 缓慢增长到 300
    if affection < 200:
        return 100 + affection * 0.5
    else:
        return 150 + min(affection / 400, 150)
```

不需要完全复刻 TW 的 `GET_REVISION` 函数行为，只需要保持"好感度越高加成越高，但有上限"的意图。

---

## 6. 你需要决定的三个问题

1. **药物系统 β 版是否要做？** 媚药/发情/利尿剂/烂醉 需要新增数据结构和管理逻辑。
2. **时间停止系统 β 版是否要做？** 如果不要，可以删掉 BASE:8(TSP) 和相关代码。
3. **公式精度要求**：是要"和 TW 完全一致"，还是"数量级和趋势一致即可"？后者工作量少 80%。

确认这三个问题后，我可以直接开始写第一批代码。

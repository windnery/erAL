# 角色包格式

## 1. 目的

定义 `erAL` 角色包的基础格式，让单角色内容独立存放，加载器和校验器有稳定入口，后续扩展不返工。

## 2. 目录结构

```text
data/base/characters/<character_key>/
  character.toml    （必填）
  events.toml       （可选）
  dialogue.toml     （可选）
  base.toml         （可选，命名轴 BASE 初值）
  palam.toml        （可选，命名轴 PALAM 初值）
  abl.toml          （可选，索引轴 ABL 初值）
  talent.toml       （可选，索引轴 TALENT 初值）
  cflag.toml        （可选，索引轴 CFLAG 初值）
  marks.toml        （可选，标记初值）
```

数值初值优先从拆分数值文件（`base.toml` 等）加载；若无拆分文件但 `character.toml` 中有 `[initial_stats]` 段，则从内嵌段加载。两种方式不能同时存在。

## 3. `character.toml`

### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `key` | str | 唯一标识，必须与目录名一致 |
| `display_name` | str | 显示名称 |
| `initial_location` | str | 初始地点 key |
| `schedule` | dict[str, str] | 时段 → 地点 key 映射 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `tags` | [str] | 角色标签，用于事件匹配 |

示例：

```toml
key = "starter_secretary"
display_name = "秘书舰"
tags = ["starter", "secretary"]
initial_location = "command_office"

[schedule]
dawn = "dormitory_a"
morning = "command_office"
afternoon = "training_ground"
evening = "cafeteria"
night = "bathhouse"
late_night = "dormitory_a"
```

## 4. `events.toml`

每个事件通过 `[[events]]` 定义，支持以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key` | str | 是 | 事件唯一标识 |
| `action_key` | str | 是 | 关联的指令 key，必须在 commands.toml 中存在 |
| `actor_tags` | [str] | 是 | 触发角色的标签匹配（OR 逻辑） |
| `location_keys` | [str] | 否 | 地点限制（空=不限） |
| `time_slots` | [str] | 否 | 时段限制（空=不限） |
| `min_affection` | int | 否 | 最低好感 |
| `min_trust` | int | 否 | 最低信赖 |
| `min_obedience` | int | 否 | 最低服从 |
| `required_stage` | str | 否 | 所需关系阶段（rank ≥ 匹配） |
| `requires_date` | bool | 否 | 是否需要约会状态 |
| `requires_private` | bool | 否 | 是否需要私密地点（默认 false） |
| `required_marks` | dict[str, int] | 否 | 所需标记及其最低等级 |

示例：

```toml
[[events]]
key = "secretary_tease_private"
action_key = "tease"
actor_tags = ["secretary"]
location_keys = ["bathhouse", "dormitory_a"]
time_slots = ["night", "late_night"]
min_affection = 1
required_stage = "friendly"
requires_private = true
required_marks = { embarrassed = 1 }
```

## 5. `dialogue.toml`

每个条目通过 `[[entries]]` 定义，支持以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key` | str | 是 | 指令 key 或事件 key |
| `actor_key` | str | 是 | 角色标识，必须与角色包 key 一致 |
| `lines` | [str] | 是 | 对话文本列表 |
| `priority` | int | 否 | 优先级，高者优先（默认 0） |
| `required_stage` | str | 否 | 所需关系阶段（当前 == 精确匹配） |
| `time_slots` | [str] | 否 | 时段限制 |
| `location_keys` | [str] | 否 | 地点限制 |
| `min_affection` | int | 否 | 最低好感 |
| `min_trust` | int | 否 | 最低信赖 |
| `min_obedience` | int | 否 | 最低服从 |
| `requires_private` | bool | 否 | 是否需要私密地点 |
| `requires_date` | bool | 否 | 是否需要约会状态 |
| `requires_following` | bool | 否 | 是否需要同行状态 |
| `required_marks` | dict[str, int] | 否 | 所需标记及其最低等级 |

### 选择逻辑

1. 事件命中时优先按事件 key 找文本
2. 未命中事件时按动作 key 找兜底文本
3. 同 key 多条目时，priority 高者优先；条件全部满足才匹配
4. `actor_key = "_any"` 为全局兜底，不限定角色

### 三种条目类型

```toml
# 兜底对话（最低优先级，无条件）
[[entries]]
key = "chat"
actor_key = "starter_secretary"
priority = 0
lines = ["你和秘书舰安静地聊了一会儿。"]

# 条件变体（中优先级，按场景条件区分）
[[entries]]
key = "chat"
actor_key = "starter_secretary"
priority = 5
required_stage = "like"
lines = ["秘书舰的语气比往常随意了些。"]

# 事件触发型（高优先级，条件精确匹配）
[[entries]]
key = "secretary_chat_command_office"
actor_key = "starter_secretary"
priority = 10
lines = ["秘书舰放下手中的报告文件夹，露出一个恰到好处的微笑。"]
```

## 6. 拆分数值文件

当角色包目录中存在拆分数值文件时，加载器会从中读取初值并注入到 `InitialStatOverrides`。若目录中无任何拆分数值文件，则回退到 `character.toml` 内嵌的 `[initial_stats]` 段。

### `base.toml`

命名轴 BASE 初值，键为轴定义中的合法 key。

```toml
stamina = 1200
spirit = 900
```

### `palam.toml`

命名轴 PALAM 初值，键为轴定义中的合法 key。

```toml
favor = 3
obedience = 1
```

### `abl.toml`

索引轴 ABL 初值，键为字符串形式的 `era_index`。

```toml
"41" = 2
```

### `talent.toml`

索引轴 TALENT 初值，键为字符串形式的 `era_index`。

```toml
"92" = 1
```

### `cflag.toml`

索引轴 CFLAG 初值，键为字符串形式的 `era_index`。

```toml
"2" = 4
"4" = 3
```

### `marks.toml`

标记初值，键为 `data/base/marks.toml` 中定义的合法 mark key。

```toml
kissed = 1
confessed = 1
```

## 7. 校验规则

1. `character.toml` 必须存在
2. `events.toml` 和 `dialogue.toml` 可以缺省
3. 拆分数值文件（`base.toml` 等）可以缺省，但一旦存在就必须通过对应族的格式校验
4. `base.toml` 和 `palam.toml` 中的 key 必须在轴定义中存在，否则视为内容错误
5. `abl.toml`、`talent.toml`、`cflag.toml` 中的 `era_index` 必须在兼容轴注册表中存在，否则视为内容错误
6. `marks.toml` 中的 key 必须在 mark 定义中存在，否则视为内容错误
7. `dialogue.actor_key` 必须和角色包 key 一致（`_any` 除外）
8. `events.action_key` 必须能在命令表里找到
9. `schedule` 和 `events.location_keys` 中引用的地点必须存在
10. 这些规则由 `python -m eral.tools.validate_content --root .` 检查

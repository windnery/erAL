# ABL 成长系统

## 概述

ABL 成长系统负责能力成长、经验转换和 ABL 等级的游戏效果。erAL 已有 ABL 升级骨架（经验累积 → 阈值检查 → 等级提升），但还缺少"ABL 等级被消费"的完整闭环。

## 当前状态

- `abl_upgrade.toml` 定义了 ABL 升级阈值和经验需求
- `check_and_apply_abl_upgrades()` 在结算后自动检查升级
- `SOURCE` 中可产出 `abl_*` 经验值（如 `abl_9` = 亲密、`abl_10` = 顺从）
- **缺失**：ABL 升级后没有消费方——没有命令/事件/结算根据 ABL 等级改变行为

## ABL 等级的消费方式

### 1. 作为命令门禁条件

在 `commands.toml` 中用 `required_conditions` 引用 ABL 轴：

```toml
# 示例：需要顺从 ABL >= 3 才能使用某些奉仕命令
required_conditions = { abl_10 = 3 }
```

`CommandSpecificGate` 已经支持 `required_conditions`，只需在命令定义中配置即可。

### 2. 影响 SOURCE 倍率

在 `talent_effects.toml` 中新增 ABL 等级对 SOURCE 的影响：

```toml
# 示例：ABL 顺从等级影响服从类 SOURCE
[[effect]]
era_index = 10
label = "Obedience ABL"
category = "abl"
source_key = "obedience"
formula = "multiply"
expression = "1.0 + 0.1 * v"
```

### 3. 影响口上分支

ABL 等级通过 `SceneContext` 暴露（需要扩展），口上可用 `min_obedience` 等条件匹配差分。

当前已有的 ABL 相关口上条件：`min_affection` / `min_trust` / `min_obedience`（走 cflag 而非 ABL 索引，暂够用）。

## 关键 ABL 索引

| era_index | 名称 | 用途 | 当前消费状态 |
|-----------|------|------|------------|
| 9 | 亲密 | 关系推进 | ⚠️ 有升级但未做门禁 |
| 10 | 顺从 | 调教推进 | ⚠️ 有升级但未做门禁 |
| 13 | 服务 | 奉仕类行为 | ⚠️ 有 SOURCE 产出但未消费 |
| 42 | 战斗 | — | ❌ 无消费 |
| 43 | 话术 | — | ❌ 无消费 |
| 44 | 清扫 | — | ❌ 无消费 |

## 建议实施

### 第一步：数据配置（改动量最小）

1. 在 `commands.toml` 中为部分命令添加 `required_conditions`，引用 ABL 轴
2. 在 `talent_effects.toml` 中新增 ABL 等级对 SOURCE 的倍率影响
3. 更新 `_CONDITION_DISPLAY` 映射添加 ABL 中文名

### 后续扩展

- ABL 等级面板展示
- ABL 等级与事件/口上条件联动
- ABL 等级与刻印系统联动（如顺从 ABL 高 → 屈服刻印更易获得）

## 与现有系统的关系

- 依赖 [结算系统](结算系统.md)（ABL 经验来源）
- 影响 [指令系统](指令系统.md)（门禁条件）
- 影响 [调教系统设计](调教系统设计.md)（开发度解锁可逐步替换为 ABL 门禁）
- 影响 [横切支撑系统](横切支撑系统.md)（talent_effects 扩展）

## 参考自 eraTW

- `Abl.csv`
- `ERB/ステータス計算関連/ABL.ERB`
- `ERB/ステータス計算関連/ABLUP.ERB`

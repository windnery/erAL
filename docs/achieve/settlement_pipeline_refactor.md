# 结算管线全面重构完成报告

完成时间：2026-04-25

---

## 概述

erAL 的核心结算管线已彻底对齐 eraTW 的相位式架构，从"指令产生 SOURCE → 多阶段修正 → 最终写入角色状态"的完整链路已经打通。所有中间层均使用结构化数据（无 eval），所有修正按结算相位组织，不再按 talent/abl 集中注册。

---

## 已完成的相位

### Phase 0: 指令执行与 SOURCE 生成

- `command_effects.toml` 定义每条指令的 `source` / `vitals` / `experience` / `conditions`
- `apply_command_effect()` 将声明式效果写入 actor 状态
- `vitals` 直接扣减 BASE（体力/气力），不走 CUP 管线（DOWNBASE 独立）
- `experience` 写入独立 EXP 轴

### Phase 0.5: SOURCE_EXTRA 全局修正

- **文件**：`data/base/rules/source_extra.toml`
- **系统**：`systems/source_extra.py`
- **作用**：在 SOURCE 进入 CBVA 之前，应用全局 TALENT 倍率
- **示例**：胆量提升 pain、献身的提升 service、恋慕/淫乱/服従提升全局快感
- **公式**：`(base + coeff * talent_value) / base`，无 eval

### Phase 1: SOURCE_CBVA 修正 → CUP

- **文件**：`data/base/rules/source_cbva.toml`
- **系统**：`systems/source_modifiers.py`
- **作用**：每条 SOURCE 按自己的修正链计算最终 CUP 值
- **支持的因子类型**：
  - `sensitivity` — 感度 TALENT `(2+v)/2`
  - `abl_scale` — ABL 线性倍率 `1 + v * scale`
  - `palam_level` — PALAM 等级分段倍率
  - `talent_linear` — TALENT 线性修正 `(base + coeff*v) / base`
- **无 eval**，所有公式由 Python 代码硬编码执行

### Phase 2: CUP Routing → PALAM / CFLAG / BASE / TFLAG

- **文件**：`data/base/rules/cup_routing.toml`（原 settlement_rules.toml）
- **系统**：`systems/settlement.py` Phase 1
- **作用**：CUP 正向累积进 PALAM，CDOWN 负向累积；CFLAG/TFLAG 直接写入

### Phase 3: FAVOR_CALC / TRUST_CALC

- **文件**：`data/base/rules/relationship_growth.toml`
- **系统**：`systems/favor_calc.py`
- **作用**：基于 PALAM 等级计算好感/信赖增量，写入 CFLAG affection/trust
- 支持设施倍率修正

### Phase 4: PALAM += CUP - CDOWN

- **系统**：`systems/settlement.py` Phase 2
- 记录 `AppliedChange` 用于反馈和日志

### Phase 5: PALAM → JUEL 转换

- **文件**：`data/base/rules/palam_to_juel.toml`
- **系统**：`systems/settlement.py` Phase 2.5
- **作用**：PALAM 增量按规则转换为 JUEL（珠），供 ABLUP 消耗

### Phase 6: 刻印检查（Imprint Check）

- **文件**：`data/base/axes/marks.toml`
- **系统**：`systems/imprint.py`
- **作用**：本回合 CUP/SOURCE 累积量达到阈值时，自动升级刻印等级
- 已接入 `settlement.py` Phase 3
- 支持 `palam_index` 和 `source_indices` 两种累积源

### Phase 7: 同步与清理

- `sync_derived_fields()` — CFLAG → runtime 字段
- `clear_source()` / `clear_cup()` — 清理本回合临时状态

---

## 已完成的关联系统

### ABLUP（能力升级）

- **文件**：`data/base/rules/abl_upgrade.toml`
- **系统**：`systems/abl_upgrade.py`
- **特性**：
  - 双资源消耗：JUEL + EXP
  - 跨 ABL 依赖检查（如 親密3 需 従順2）
  - 恋慕/誓约上限控制（无恋慕上限 5）
  - 动态折扣（经验等级降低 JUEL 消耗）
  - 快感应答 talent 加速 ABL 成长

### PALAM 衰减

- **文件**：`data/base/rules/palam_decay.toml`
- **系统**：`systems/palam_decay.py`
- **特性**：比例衰减（`PALAM -= PALAM // decay_ratio`），支持按 PALAM 类型配置不同比例

### 体力/气力恢复

- **系统**：`systems/vital.py` / `systems/fatigue.py`
- **特性**：基础恢复 + TALENT 恢复速度修正，支持设施倍率

---

## 删除的遗留系统

1. `talent_effects.toml` — 中央 talent 效果注册表（已按相位分散到 source_cbva / source_extra / relationship_growth）
2. `source_modifiers.toml`（旧版 eval 版）— 已替换为 `source_cbva.toml` + `source_extra.toml`
3. `data/base/imprint_thresholds.toml` — 独立的刻印阈值文件（已合并到 `marks.toml`）

---

## 测试覆盖

- 全部 161 个测试通过
- 新增 `tests/test_source_extra.py` 替换旧版 talent effects 测试
-  golden path 测试覆盖完整 settlement 链路

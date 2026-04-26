# 数据架构重构完成报告

完成时间：2026-04-25

---

## 核心原则

erAL 的数据定义从"按 talent 集中注册"改为"按结算相位分散配置"。这一改动彻底消除了 `talent_effects.toml` 这类中央注册表，使数据归属清晰、维护简单、无 eval 风险。

---

## 文件归属对照表

| eraTW 相位 | erAL 文件 | 内容 |
|-----------|----------|------|
| SOURCE 生成 | `commands.toml` + `command_effects.toml` | 指令定义与效果 |
| SOURCE_EXTRA | `data/base/rules/source_extra.toml` | 全局 TALENT 修正 |
| SOURCE_CBVA | `data/base/rules/source_cbva.toml` | 每条 SOURCE 的修正链 |
| CUP Routing | `data/base/rules/cup_routing.toml` | SOURCE → PALAM/CFLAG/TFLAG |
| FAVOR_CALC | `data/base/rules/relationship_growth.toml` | 好感/信赖公式 |
| TRUST_CALC | `data/base/rules/relationship_growth.toml` | 同上 |
| PALAM→JUEL | `data/base/rules/palam_to_juel.toml` | 珠转换规则 |
| PALAM decay | `data/base/rules/palam_decay.toml` | 衰减比例 |
| ABLUP | `data/base/rules/abl_upgrade.toml` | 升级成本与需求 |
| 刻印阈值 | `data/base/axes/marks.toml` | 刻印定义与触发阈值 |
| PALAM 等级 | `data/base/rules/palamlv_curves.toml` | 等级阈值曲线 |

---

## 关键去 eval 改造

### 旧架构（已删除）

```toml
[[modifier.factor]]
kind = "talent"
index = 101
expr = "(2 + v) / 2"
```

Python 侧使用 `eval(expr)`，存在安全风险且难以验证。

### 新架构

```toml
[[rule.factor]]
kind = "sensitivity"
talent_index = 101
```

Python 侧使用结构化匹配：

```python
if factor.kind == "sensitivity":
    return (2.0 + v) / 2.0
```

所有公式由代码硬编码，数据只负责"选哪个公式、参数是什么"。

---

## 新增数据加载器

| 加载器 | 文件 | 加载目标 |
|-------|------|---------|
| `content/source_modifiers.py` | `source_cbva.toml` | `SourceCbvaRule` |
| `content/source_extra.py` | `source_extra.toml` | `SourceExtraModifier` |
| `content/imprint.py` | `marks.toml` | `ImprintThreshold` |
| `content/palamlv.py` | `palamlv_curves.toml` | `PalamCurve` + `PalamToJuelRule` |
| `content/abl_upgrade.py` | `abl_upgrade.toml` | `AblUpgradeConfig` |

---

## 数据验证工具

- `python -m eral.tools.validate_content` — 检查内容包引用完整性
- `python -m eral.tools.command_coverage` — 检查指令覆盖矩阵
- `python -m eral.tools.import_tw_axes` — 从 eraTW CSV 导入轴定义

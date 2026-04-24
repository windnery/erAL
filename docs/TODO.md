# erAL TODO

更新时间：2026-04-24

当前目标：完成一次可控的“指令驱动运行时重构”，把旧版 Python 逻辑逐步接到新的 `axes / train / effects` 数据契约上，而不是继续在旧逻辑上补内容。

---

## 1. 当前真相

以下口径已经冻结，后续实现都按这个来：

1. `data/base/axes/*` 是唯一数值轴真相，不修改口径。
2. 运行时数值统一按 index 使用，不再引入语义字符串 key。
3. 指令唯一来源是 `data/base/commands/train.toml`。
4. `data/base/effects/command_effects.toml` 负责声明式效果；目前只完成一部分 SOURCE 产出。
5. `CFLAG` 保留；`FLAG / TFLAG` 视为废弃，不再作为新运行时设计目标。
6. 游戏是“指令驱动”而不是“界面驱动”：
   移动、日常互动、调教、约会、休息、购物都应统一走命令执行入口。
7. 目前只有 `axes / train / command_effects` 明确进入新重构，其余大部分 Python 逻辑仍然属于旧版实现。

---

## 2. 本轮重构原则

1. 先冻结契约，再填内容。
2. 先打通主链，再批量补指令。
3. `train.toml` 负责“指令定义层”，不承担全部业务逻辑。
4. `command_effects.toml` 负责“声明式效果层”，优先承载 SOURCE、体力消耗等可数据化内容。
5. 复杂 gate、位置变化、跟随、约会、装备切换、特殊副作用，优先落在 Python 的 operation/gate 层。
6. 任何新增字段都必须回答：
   谁写它、谁读它、玩家怎么感知它、哪个测试保护它。

---

## 3. 已完成

### 3.1 我已完成

1. 启动链修复：
   `create_application()` 不再依赖已删除的全局 `maxbase` 文件。
2. 角色基础数值 schema 打底：
   角色 `base.toml` 现在支持显式 `[current] / [cap] / [recover]` 结构。
3. 兼容策略明确：
   旧扁平 `base.toml` 只作为初始值，不自动当作上限。
4. 角色运行时状态增加：
   `base_caps` / `base_recover_rates`。
5. `VitalService` 优先读取角色自身上限和恢复率，缺省回退到默认值。
6. `command_effects.source.player` 的运行时写入错误已修复。
7. 存档已支持角色级 `base_caps` / `base_recover_rates`。
8. 文档系统已清理：
   删除 `BETA_*` 三份过时文档，保留当前有效入口。
9. 当前测试基线：
   `python -m unittest discover -s tests -t .` 全部通过。

---

## 4. 现在开始的重构顺序

### P0：先做运行时契约，不继续盲填内容

| 编号 | 任务 | 负责 | 完成定义 |
|------|------|------|----------|
| P0-01 | 固定 `train.toml` 的字段边界 | 我 | 明确哪些字段属于指令定义层，并形成 loader 约束 |
| P0-02 | 固定 `command_effects.toml` 的字段边界 | 我 | 明确哪些字段属于声明式效果层，并形成 loader 约束 |
| P0-03 | 固定 Python operation / gate 边界 | 我 | 明确哪些行为不应进入 `train` 或 `command_effects`，而应由代码承接 |
| P0-04 | 更新 `CommandDefinition` / `CommandEffect` 数据模型 | 我 | 新旧数据可兼容加载，并能表达后续指令驱动运行时需求 |
| P0-05 | 建立一份“指令覆盖矩阵” | 我 | 可追踪每条 train 指令是否已有 category / operation / gate / effect / test |

### P1：重写指令执行主链

| 编号 | 任务 | 负责 | 完成定义 |
|------|------|------|----------|
| P1-01 | 收束 `CommandService` 执行阶段 | 我 | 形成固定顺序：gate → operation → declarative effects → settlement → feedback |
| P1-02 | 把旧版散乱 operation 归类 | 我 | 移动、休息、约会、跟随、训练位变更等都落到统一 operation 层 |
| P1-03 | 把旧版直接写核心状态的分支找出来 | 我 | 列出绕过主链的旧逻辑，并逐个迁出或标记待迁 |
| P1-04 | 建立最小金路径回归 | 我 | 新游戏 → 移动 → 会话 → 等待/休息 → 存档/读档 可稳定回归 |

### P2：再补指令内容和数值规则

| 编号 | 任务 | 负责 | 完成定义 |
|------|------|------|----------|
| P2-01 | 按类别补 `command_effects` | 我 | 先补高频指令，再补深层指令，不乱序填表 |
| P2-02 | 接入 `source_modifiers` 的关键消费者 | 我 | SOURCE → CUP → PALAM 链在代表性指令上完整可见 |
| P2-03 | 补指令级 gate | 我 | 至少覆盖地点、时段、关系阶段、服装/状态、必要 ABL/TALENT |
| P2-04 | 统一反馈格式 | 我 | 成功、失败、状态变化能稳定给出玩家可见结果 |

### P3：最后做内容工业化和调优

| 编号 | 任务 | 负责 | 完成定义 |
|------|------|------|----------|
| P3-01 | 指令 SOURCE / effect 数值手调 | 你 | 在真实游玩下按体验微调，不追求照抄 TW 原值 |
| P3-02 | 角色基础体力/恢复调参 | 你 | 为角色包补齐 `[cap] / [recover]`，形成角色差异 |
| P3-03 | TALENT 保留/删除清单 | 你 | 标出 β 版暂时只展示、完全冻结、必须接入的 TALENT |
| P3-04 | 口上与事件消费者补齐 | 你 | 让新增状态和指令有文本反馈，而不是只改后台数值 |

---

## 5. 明确分工

### 我来做

1. 运行时契约设计和代码改造。
2. `train.toml` / `command_effects.toml` schema 设计与 loader 收束。
3. `CommandService`、operation、gate、settlement 主链重构。
4. 指令覆盖矩阵、自动化回归测试、内容校验工具。
5. 与 TW 的“机制映射”工作：
   提取语义，不照搬引擎限制。

### 你来做

1. 角色数值调参：
   按角色特色填写 `base.toml` 的 `[current] / [cap] / [recover]`。
2. 指令体验调参：
   我先把字段和骨架定下来，你按游玩体验微调数值。
3. TALENT 设计裁剪：
   哪些先保留展示、哪些必须尽快接入消费者、哪些直接冻结。
4. 文本内容补齐：
   事件、口上、皮肤相关差分表达。
5. 玩法裁决：
   当 TW 语义和 `erAL` 体验冲突时，由你拍板采用哪种体验。

### 需要你及时答复的事项

1. 某类指令是否应该存在。
2. 某类 TALENT 在 β 版是“必须生效”还是“先展示”。
3. 某个 operation 是否符合你的玩法预期。
4. 某个数值表现是否偏离你想要的节奏。

---

## 6. 当前文档清理结论

### 已保留

1. `docs/README.md`
2. `docs/TODO.md`
3. `docs/系统清单.md`
4. `docs/PRD.md`
5. `docs/玩家体验映射.md`
6. `docs/TW公式迁移策略.md`
7. `docs/specs/*`

### 已删除

1. `docs/BETA_REQUIREMENTS_ANALYSIS.md`
2. `docs/BETA_REQUIREMENTS_INTERVIEW.md`
3. `docs/BETA_ROADMAP.md`

### 当前处理原则

1. `TODO / 系统清单 / PRD` 是当前权威。
2. `specs/*` 里还带旧字段名和旧命令来源的内容，暂时降级为参考。
3. 等 `train + command_effects + CommandService` 新契约稳定后，再逐个回写 spec。

---

## 7. 下一步直接执行项

### 我下一步

1. 提出 `train.toml` 的最小必要字段集。
2. 提出 `command_effects.toml` 的最小必要字段集。
3. 明确哪些内容必须留在 Python operation/gate 层。
4. 把这套字段边界真正落进 loader 和校验逻辑。

### 你下一步

1. 决定角色 `base.toml` 是否统一切到显式 schema。
2. 给出你最想优先打通的 1 组指令：
   日常、移动、调教、约会四类里各选最关键的一两条也可以。
3. 标出哪些 TALENT 在下一阶段必须先接入。

---

## 8. 暂不做

1. 一口气补完全部 165 条 train 指令的全部效果。
2. 全量重写全部 `specs` 文档。
3. 新开大型前端重构。
4. 扩内容规模优先于主链收束。

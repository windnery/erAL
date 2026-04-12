# docs 索引与权威边界

## 阅读顺序

1. `docs/README.md`（本文件）
2. `docs/AI_LONG_TERM_VIBE_GUIDE.md`（执行规则与质量门）
3. `docs/PRD.md`（目标与验收）
4. `docs/TODO.md`（任务状态与排期）
5. 如涉及指令迁移，再读 `docs/COMMAND_MIGRATION.md`
6. 如涉及系统设计，再读 `docs/specs/`
7. `docs/reference/` 仅在需要细节时查阅

## 文档分级

### A 级：权威执行文档（可直接驱动开发）

| 文档 | 角色 | 更新触发 |
|------|------|----------|
| `docs/AI_LONG_TERM_VIBE_GUIDE.md` | 开发治理规则、质量门、AI 协作协议 | 执行规范或质量门变化 |
| `docs/PRD.md` | 产品目标、范围边界、验收标准 | 目标范围或验收变化 |
| `docs/TODO.md` | 任务看板、优先级、状态 | 每次任务状态变化 |
| `docs/COMMAND_MIGRATION.md` | 指令迁移计划与进度 | 新增/调整指令迁移 |

### B 级：架构与设计文档（受控执行依据）

| 文档 | 角色 | 更新触发 |
|------|------|----------|
| `docs/specs/` | 各子系统规格（数据结构→流程→配置→扩展方法） | 系统行为变化时 |
| `docs/superpowers/specs/` | 批次设计规格（如角色批次设计） | 批次设计变化时 |
| `docs/superpowers/plans/` | 批次实现计划 | 计划变化时 |
| `docs/archive/architecture-plan.md` | 早期架构规划（已归档，仅供历史参考） | 不再主动维护 |

### C 级：参考资料（不可直接作为任务指令）

| 文档 | 角色 |
|------|------|
| `docs/reference/character-pack-format.md` | 角色包 TOML 格式定义（含拆分数值文件） |
| `docs/reference/ark-engine-patterns.md` | erArk 工程模式分析 |
| `docs/reference/tw-system-mapping.md` | eraTW → erAL 概念映射 |
| `docs/reference/tw-kojo-migration-strategy.md` | 口上迁移策略 |
| `docs/reference/tw-state-index-tables.md` | CFLAG/TFLAG/FLAG 索引表 |
| `docs/reference/tw-callchain-rule-matrix.md` | 调用链规则矩阵 |
| `docs/reference/tw-comable-rule-matrix.md` | 可执行规则矩阵 |
| `docs/reference/tw-talent-index-table.md` | 素质索引表 |
| `docs/reference/tw-train-full-group-table.md` | 训练分组表 |

### 归档

| 文档 | 归档原因 |
|------|----------|
| `docs/archive/architecture-plan.md` | 内容已被 specs/ 和实际代码覆盖 |
| `docs/archive/adoption-backlog.md` | 条目已完成或已被 specs 覆盖 |

## 冲突处理规则

1. 若 `TODO` 与 `PRD` 冲突：以 `PRD` 验收口径为准。
2. 若任务与 `AI_LONG_TERM_VIBE_GUIDE` 冲突：以质量门和治理规则为准。
3. 若 `specs/` 与实现冲突：以实际代码为准，同步更新 spec。
4. 任何冲突都必须在提交说明中记录"冲突 → 决议 → 影响范围"。

## 最小维护要求

1. 每周至少一次检查 A 级文档是否口径一致。
2. 每次大改后更新本文件中的文档分级或阅读顺序。
3. 新增 docs 文档时，必须在本文件登记其级别和用途。

## 新增文档登记模板

```markdown
- 文档：docs/xxx.md
- 级别：A / B / C
- 用途：
- 是否可直接驱动开发：是 / 否
- 维护频率：按需 / 每周 / 每次迭代
```

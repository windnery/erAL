# erAL Vibe TODO

> 目标：把项目推进方式从“大清单打勾”升级为“可持续交付（可靠性优先）”。
> 
> 约束：玩法语义优先继承 eraTW，工程实现参考 erArk 的长期迭代经验（日志化、频繁发布、内容与系统分离协作）。

## 长期模式入口（可靠性优先）

1. 本看板的执行规则由 `docs/AI_LONG_TERM_VIBE_GUIDE.md` 统一定义。
2. 当“短期可玩性目标”与“可靠性质量门”冲突时，必须优先满足质量门。
3. 本看板用于排期与状态，不再单独定义质量标准。

## 0. 这份 TODO 怎么用

1. 这份文件是唯一任务看板，`PRD.md` 是唯一验收口径。
2. 每次开发会话只做 `1 个主任务 + 2 个次任务`，禁止并行开太多支线。
3. 每个任务都必须是 25 到 90 分钟可完成的颗粒度。
4. 任务必须写清可验证结果，不写“继续优化”“补一补”这类模糊描述。

## 1. 任务卡字段（AI 与人共用）

每个任务必须使用下面格式：

```markdown
- [ ] 标题（动词开头）
	- type: code | content | test | docs | tooling
	- priority: P0 | P1 | P2
	- milestone: L0 | L1 | L2 | L3
	- est: 25m | 45m | 90m
	- DoD: 一句话说明“完成后可观察到什么变化”
	- verify: 运行命令或手工步骤
	- owner: human | ai | pair
	- status: todo | doing | blocked | done
	- updated: YYYY-MM-DD
```

## 2. 里程碑定义（固定不漂移）

- `L0 架构与质量基线`：六层边界稳定、主干回归测试稳定、内容加载与校验流程稳定。
- `L1 核心语义完整`：SOURCE 结算、关系阶段、MARK 分支与指令前提一致可回归。
- `L2 内容规模化生产`：角色包模板与内容校验器成熟，新增角色不改核心系统。
- `L3 MVP`：满足 PRD 定义的数量目标与连续游玩目标。

## 3. 本期主线（可靠性优先）

> 规则：先完成 P0 质量门，再推进功能与内容。若出现冲突，质量门优先。

### 主线 A：L0 质量基线收敛

- [ ] 统一 TODO 与指导书的里程碑、优先级、状态口径
	- type: docs
	- priority: P0
	- milestone: L0
	- est: 45m
	- DoD: 里程碑命名、状态字段、优先级在相关文档中一致
	- verify: 人工逐项勾对 docs/PRD.md、docs/TODO.md、docs/AI_LONG_TERM_VIBE_GUIDE.md
	- owner: pair
	- status: todo
	- updated: 2026-04-11

- [x] 建立运行日志最小规范并接入关键链路
	- type: code
	- priority: P0
	- milestone: L0
	- est: 90m
	- DoD: 日志可记录时段、动作、角色、命中事件与失败原因
	- verify: 手工执行指令后检查 runtime/logs 记录
	- owner: pair
	- status: done
	- updated: 2026-04-11

- [x] 增加“连续 3 天可玩”烟测
	- type: test
	- priority: P0
	- milestone: L0
	- est: 90m
	- DoD: 自动化测试可稳定通过并覆盖移动-互动-结算-时间推进
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: done
	- updated: 2026-04-11

### 主线 B：L1 核心语义一致性

- [ ] 完成关系阶段命名统一（陌生->友好->喜欢->爱->誓约）
	- type: code
	- priority: P0
	- milestone: L1
	- est: 90m
	- DoD: 事件/对话/指令前提不再出现旧命名
	- verify: 全仓搜索旧阶段关键字 + 测试通过
	- owner: pair
	- status: todo
	- updated: 2026-04-11

- [ ] 让 embarrassed、angry、drunk 参与至少 3 条真实分支
	- type: content
	- priority: P1
	- milestone: L1
	- est: 90m
	- DoD: 至少 3 条事件或对话在 MARK 条件下走不同分支
	- verify: 对应测试 + 手工触发截图/日志
	- owner: pair
	- status: todo
	- updated: 2026-04-11

## 4. Backlog（按价值排序，不按想到就做）

### P0（近期必须做）

- [x] 地点扩展到 8 到 12，并给每个地点补玩法标签
- [x] 约会四地点分支各至少 1 条（食堂/码头/宿舍/浴场）
- [x] 指令失败反馈标准化（地点/时段/关系/状态原因）

### P1（可延期但重要）

- [ ] 将指令迁移表改为“体感收益优先队列”
- [x] 内容校验器增加“条目数量缺口”检查
- [x] 增加“多角色并行游玩”回归测试
- [x] 生活/工作 B 批 `rest / study / cook / eat_meal / invite_meal / nap` 已进入命令系统
- [x] `library / infirmary / garden` 已开始承载专属事件钩子与口上内容

### P2（MVP 后）

- [ ] 深层 H 相关系统（明确不进入当前迭代）
- [ ] UI 形态升级（CLI 以外）

## 5. AI 长期协作协议

> 这一节直接用于和 AI 对齐工作方式。

### 5.1 每次会话输入模板

```markdown
本次目标：
范围边界：
验收标准：
禁止改动：
需要产出：代码/测试/文档/报告
```

### 5.2 每次会话输出模板

```markdown
完成项：
变更文件：
验证结果：
风险与遗留：
建议下一个最小任务（<=90m）：
```

### 5.3 AI 允许执行的默认动作

1. 优先补测试与文档一致性，再补代码。
2. 新增字段必须绑定可感知玩法效果，否则不加。
3. 不做跨里程碑大改；发现范围膨胀时，改写成 Backlog 任务。

## 6. erArk 启发（用于长期维护）

从 erArk 可借鉴但不照搬的实践：

1. 保持高频迭代与更新日志习惯，避免“做了很多但无法回看”。
2. 让内容生产和系统开发解耦，角色文本可持续协作补量。
3. 采用“错误日志 + 存档复现”方式定位复杂 BUG。

对应到 erAL 的落地任务：

- [ ] 建立 runtime/logs 最小日志规范（日期、时段、动作、触发事件、失败原因）
- [ ] 建立每周 update 记录（本周新增指令、事件、对话、测试）
- [ ] 为复杂 BUG 固化“附存档复现”模板

## 7. 当前事实（避免重复争论）

- [x] `create_application()` 已是装配入口。
- [x] `SOURCE -> settlement -> BASE/PALAM/CFLAG/TFLAG` 已跑通。
- [x] 角色包已支持 `BASE/PALAM/ABL/TALENT/CFLAG/MARK` 初始属性。
- [x] 同行、约会、轻亲密起点与存档系统已存在。
- [x] runtime/logs 已有最小结构化日志链路。
- [x] `python -m unittest discover -s tests -t .` 已可作为统一回归入口。
- [ ] 当前主要瓶颈不是架构，而是内容密度与里程碑收敛。

## 8. 本周复盘区（每周五更新）

- 本周完成：
- 本周阻塞：
- 指标：
	- 新增指令数：
	- 新增事件数：
	- 新增对话数：
	- 自动化测试通过率：
	- 手工可玩天数：
- 下周主线：

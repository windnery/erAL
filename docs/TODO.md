# erAL TODO

> 约束：玩法语义优先继承 eraTW，工程实现参考 erArk 的长期迭代经验。

## 执行规则

1. 本看板定义"做什么"，`docs/AI_LONG_TERM_VIBE_GUIDE.md` 定义"如何做"。
2. 优先级与里程碑定义见 AI_GUIDE 第4节，本文件不重复。
3. 任务卡字段规范见 AI_GUIDE 第5节，本文件不重复。
4. 每次开发会话只做 `1 个主任务 + 2 个次任务`，禁止并行开太多支线。
5. 每个任务必须是 25 到 90 分钟可完成的颗粒度。
6. 任务必须写清可验证结果，不写"继续优化""补一补"这类模糊描述。

## 本期主线

### 主线 A：L0 架构与质量基线

- [x] 统一 TODO 与指导书的里程碑、优先级、状态口径
	- type: docs
	- priority: P0
	- milestone: L0
	- est: 45m
	- DoD: 里程碑命名、状态字段、优先级在相关文档中一致
	- verify: 人工逐项勾对 docs/PRD.md、docs/TODO.md、docs/AI_LONG_TERM_VIBE_GUIDE.md
	- owner: pair
	- status: done
	- updated: 2026-04-12

- [x] 建立运行日志最小规范并接入关键链路
	- type: code
	- priority: P0
	- milestone: L0
	- est: 90m
	- DoD: 日志可记录日期、时段、动作与指令 key、目标角色 key、命中事件 key 与失败原因
	- verify: 手工执行指令后检查 runtime/logs 记录
	- owner: pair
	- status: done
	- updated: 2026-04-11

- [x] 增加"连续 3 天可玩"烟测
	- type: test
	- priority: P0
	- milestone: L0
	- est: 90m
	- DoD: 自动化测试可稳定通过并覆盖移动-互动-结算-时间推进
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: done
	- updated: 2026-04-11

### 主线 B：L1 核心语义完整

- [x] 完成关系阶段命名统一（陌生→友好→喜欢→爱→誓约）
	- type: code
	- priority: P0
	- milestone: L1
	- est: 90m
	- DoD: 事件/对话/指令前提不再出现旧命名
	- verify: 全仓搜索旧阶段关键字 + 测试通过
	- owner: pair
	- status: done
	- updated: 2026-04-12

- [x] 让 embarrassed、angry、drunk 参与至少 3 条真实分支
	- type: content
	- priority: P1
	- milestone: L1
	- est: 90m
	- DoD: 至少 3 条事件或对话在 MARK 条件下走不同分支
	- verify: 对应测试 + 手工触发截图/日志
	- owner: pair
	- status: todo
	- updated: 2026-04-11

## Backlog（按价值排序）

### P0（可靠性与一致性：测试、校验、文档口径、关键 BUG）

- [x] 地点扩展到 8 到 12，并给每个地点补玩法标签
- [x] 约会四地点分支各至少 1 条（食堂/码头/宿舍/浴场）
- [x] 指令失败反馈标准化（地点/时段/关系/状态原因）

### P1（架构与工具能力：可观测性、自动化、内容管线）

- [ ] 将指令迁移表改为"体感收益优先队列"
- [x] 内容校验器增加"条目数量缺口"检查
- [x] 增加"多角色并行游玩"回归测试
- [x] 生活/工作 B 批 `rest / study / cook / eat_meal / invite_meal / nap` 已进入命令系统
- [x] `library / infirmary / garden` 已开始承载专属事件钩子与口上内容

### P2（内容扩展与体感优化）

- [ ] 深层 H 相关系统（明确不进入当前迭代）
- [ ] UI 形态升级（CLI 以外）

## 当前事实（避免重复争论）

- [x] `create_application()` 已是装配入口。
- [x] `SOURCE -> settlement -> BASE/PALAM/CFLAG/TFLAG` 已跑通。
- [x] 角色包已支持 `BASE/PALAM/ABL/TALENT/CFLAG/MARK` 初始属性。
- [x] 角色初值已迁移到按数值族拆分的独立 TOML 文件（base.toml/palam.toml/abl.toml/talent.toml/cflag.toml/marks.toml）。
- [x] 企业、拉菲两个正式测试角色包已就位。
- [x] 同行、约会、轻亲密起点与存档系统已存在。
- [x] runtime/logs 已有最小结构化日志链路。
- [x] `python -m unittest discover -s tests -t .` 已可作为统一回归入口。
- [ ] 当前主要瓶颈不是架构，而是内容密度与里程碑收敛。


### L1 延续任务

- [ ] 为已接命令补齐自动化测试覆盖
	- type: test
	- priority: P0
	- milestone: L1
	- est: 60m
	- DoD: 同行 B 批、约会 C 批、轻亲密 B 批至少各 1 条集成测试
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: todo
	- updated: 2026-04-12

- [ ] MARK 分支扩展至事件层（不只是对话层）
	- type: content
	- priority: P1
	- milestone: L1
	- est: 60m
	- DoD: 至少 2 条事件在 required_marks 条件下触发不同事件
	- verify: 对应测试通过
	- owner: pair
	- status: todo
	- updated: 2026-04-12

- [ ] 为 5 个角色补齐阶段差分文本（like / love 阶段更多对话变体）
	- type: content
	- priority: P1
	- milestone: L1
	- est: 90m
	- DoD: 每个角色至少 3 条已有指令在 like 或 love 阶段有不同对话
	- verify: DialogueService._lookup 在不同 stage 返回不同 lines
	- owner: pair
	- status: todo
	- updated: 2026-04-12

- [ ] 连续 7 天可玩烟测
	- type: test
	- priority: P0
	- milestone: L1
	- est: 60m
	- DoD: 自动化测试模拟 7 天完整循环（移动-互动-结算-时间推进-日程切换）稳定通过
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: todo
	- updated: 2026-04-12

- [ ] 将指令迁移表改为体感收益优先队列
	- type: docs
	- priority: P1
	- milestone: L1
	- est: 45m
	- DoD: COMMAND_MIGRATION.md 按体感收益重排优先级，已接命令标注当前状态
	- verify: 人工审阅
	- owner: pair
	- status: todo
	- updated: 2026-04-12

## 本周复盘区（每周五更新）

- 本周完成：角色初值拆分文件迁移、企业与拉菲角色包、事件/对话/命令扩展
- 本周阻塞：无
- 指标：
	- 新增指令数：
	- 新增事件数：
	- 新增对话数：
	- 自动化测试通过率：
	- 手工可玩天数：
- 下周主线：

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
	- status: done
	- updated: 2026-04-12

### 主线 C：MVP 达标冲刺

> 目标：满足 PRD 2.2 全部完成标准，特别是"连续 7 天可玩"和"完成 1 条约会线与 1 条轻亲密线"。

- [x] 补齐 C/B 批命令测试覆盖
	- type: test
	- priority: P0
	- milestone: L1
	- est: 60m
	- DoD: 同行 B 批、约会 C 批、轻亲密 B 批、日常 C 批各至少 1 条集成测试，14 个"已接命令"全部推进到"完成"
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 充实企业/拉菲事件与对话
	- type: content
	- priority: P0
	- milestone: L1
	- est: 90m
	- DoD: 企业和拉菲各至少 20 事件 + 30 对话条目，覆盖日常/同行/约会/轻亲密至少各 2 条事件
	- verify: python -m eral.tools.validate_content --root . + 事件/对话计数断言
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 端到端约会线 + 轻亲密线可玩测试
	- type: test
	- priority: P0
	- milestone: L1
	- est: 60m
	- DoD: 自动化测试可从陌生推进关系、发起同行、转为约会、完成约会全过程、进入轻亲密，整条链路不断裂
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 连续 7 天可玩烟测
	- type: test
	- priority: P0
	- milestone: L1
	- est: 60m
	- DoD: 自动化测试模拟 7 天完整循环（移动-互动-结算-时间推进-日程切换）稳定通过
	- verify: python -m unittest discover -s tests -t .
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] MARK 分支扩展至事件层
	- type: content
	- priority: P1
	- milestone: L1
	- est: 60m
	- DoD: 至少 2 条事件在 required_marks 条件下触发不同事件
	- verify: 对应测试通过
	- owner: pair
	- status: done
	- updated: 2026-04-12

- [x] 为 5 个角色补齐阶段差分文本（like / love 阶段更多对话变体）
	- type: content
	- priority: P1
	- milestone: L1
	- est: 90m
	- DoD: 每个角色至少 3 条已有指令在 like 或 love 阶段有不同对话
	- verify: DialogueService._lookup 在不同 stage 返回不同 lines
	- owner: pair
	- status: done
	- updated: 2026-04-12

### 主线 D：L2 语义可读层与流程精细化

> 目标：在已稳定兼容层基础上，提高开发可读性与玩法细粒度一致性，减少后续功能迭代的心智成本。

- [ ] 建立 ABL/TALENT 常用语义映射层
	- type: code
	- priority: P0
	- milestone: L2
	- est: 90m
	- DoD: 覆盖首批高频索引（至少 30 项）的命名常量或查询接口，业务层不再直接散落硬编码索引
	- verify: 新增映射层测试 + 替换至少 3 处业务调用
	- owner: ai
	- status: todo
	- updated: 2026-04-12

- [ ] 将指令可用性判定拆分为多层 Gate
	- type: code
	- priority: P0
	- milestone: L2
	- est: 90m
	- DoD: 可用性检查分离为分类门槛、全局模式门槛、指令专用门槛，失败原因保持可读
	- verify: tests/test_commands.py 新增对应用例并全通过
	- owner: pair
	- status: todo
	- updated: 2026-04-12

- [ ] 增加约会后事件结算层（after_date_event）
	- type: code
	- priority: P1
	- milestone: L2
	- est: 90m
	- DoD: end_date 后可独立触发后事件（如告白/赠礼后续），不与普通指令事件混线
	- verify: 新增端到端测试覆盖至少 2 条约会后分支
	- owner: pair
	- status: todo
	- updated: 2026-04-12

- [ ] 建立内容密度自动统计报告
	- type: tooling
	- priority: P1
	- milestone: L2
	- est: 45m
	- DoD: validate_content 输出每角色事件/对话数量与缺口摘要，可直接用于周报
	- verify: python -m eral.tools.validate_content --root . 输出包含统计段
	- owner: ai
	- status: todo
	- updated: 2026-04-12

## Backlog（按价值排序）

### P0（可靠性与一致性：测试、校验、文档口径、关键 BUG）

- [x] 地点扩展到 8 到 12，并给每个地点补玩法标签
- [x] 约会四地点分支各至少 1 条（食堂/码头/宿舍/浴场）
- [x] 指令失败反馈标准化（地点/时段/关系/状态原因）

### P1（架构与工具能力：可观测性、自动化、内容管线）

- [x] 内容校验器增加"条目数量缺口"检查
- [x] 增加"多角色并行游玩"回归测试
- [x] 生活/工作 B 批 `rest / study / cook / eat_meal / invite_meal / nap` 已进入命令系统
- [x] `library / infirmary / garden` 已开始承载专属事件钩子与口上内容

### P2（MVP 后或低优先级）

- [ ] 将指令迁移表改为体感收益优先队列
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
- [x] 54 个指令已接入 commands.toml，迁移表中均已标记"完成"。
- [x] 企业、拉菲内容密度已达到当前主线目标（各 >= 20 事件、>= 30 对话）。
- [x] 端到端链路与 7 天烟测已通过（unittest 全量通过）。
- [ ] 当前主要瓶颈已转为 L2：语义可读层（索引常量化）与流程精细化（多层 gate、约会后事件层）。

## 本周复盘区（每周五更新）

- 本周完成：角色初值拆分文件迁移、企业与拉菲角色包、事件/对话/命令扩展
- 本周阻塞：无
- 指标：
	- 新增指令数：0（本周以补齐与稳定性验证为主）
	- 新增事件数：>= 50（五角色包扩展）
	- 新增对话数：>= 120（五角色包扩展）
	- 自动化测试通过率：100%（193/193）
	- 手工可玩天数：7 天链路已被自动化烟测覆盖
- 下周主线：L2 语义可读层与流程精细化（主线 D）

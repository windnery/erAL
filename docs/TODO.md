# erAL TODO

> 约束：玩法语义优先继承 eraTW，工程实现参考 erArk 的长期迭代经验。

---

## 🚀 当前最优先（下次开发抓手）

选 1 个主任务（蓝框）+ 2 个次任务（绿框）

| # | 任务 | 里程碑 | 类型 | Est | 状态 |
|---|------|--------|------|-----|------|
| 1 | 道具系统最小骨架（Inventory + 存档 + 命令门禁） | L5 | core | 120m | 🔴 next |
| 2 | 誓约最小闭环（戒指校验 + 消耗 + 事件） | L5 | gameplay | 120m | 🟡 gated |
| 3 | 商店最小闭环（3~5 商品 + 购买 + 扣费） | L5 | gameplay | 90m | 🟡 gated |
| 4 | commands.toml 校验器（重复 key + 非法字段） | L4 | tooling | 60m | 🟢 ready |
| 5 | 存档兼容回归包（旧档读取 + 字段降级） | L4 | test | 75m | 🟢 ready |
| 6 | 地图分层规划骨架（阵营区/子区/建筑） | L5 | architecture | 120m | 🟢 ready |
| 7 | 调教系统骨架（判定/执行/结算三段） | L5 | gameplay | 150m | 🟡 gated |
| 8 | 内容校验增强（角色包必填与引用完整性） | L4 | tooling | 60m | 🟢 ready |

**执行顺序**：先做 L5 解耦底座（1/2/3），并行保留 L4 稳定性护栏（4/5/8），再进地图与调教（6/7）

---

## 🧱 解耦优先规则（新增）

1. 任何跨系统功能必须先落地在 `gate + service + data` 三层，不允许把规则硬写进 UI。
2. 前提条件统一放在命令门禁（借鉴 erArk 的 premise 思路），事件层只做触发和表现。
3. 关系阶段配置中的 `requires_item` 必须有运行时强校验，禁止仅显示不生效。
4. 新系统开发顺序固定：`最小数据结构 -> 可执行门禁 -> 最小闭环玩法 -> 内容扩展`。
5. 地图、调教、商店都只能依赖稳定接口，不直接读写彼此内部状态。

---

## ⚙️ 执行规则

1. 本看板定义"做什么"，`docs/AI_LONG_TERM_VIBE_GUIDE.md` 定义"如何做"。
2. 优先级与里程碑定义见 AI_GUIDE 第4节，本文件不重复。
3. 任务卡字段规范见 AI_GUIDE 第5节，本文件不重复。
4. 每次开发会话只做 `1 个主任务 + 2 个次任务`，禁止并行开太多支线。
5. 每个任务必须是 25 到 90 分钟可完成的颗粒度。
6. 任务必须写清可验证结果，不写"继续优化""补一补"这类模糊描述。

---

## 📊 里程碑进度一览表

| 里程碑 | 状态 | 完成度 | 关键指标 |
|--------|------|--------|---------|
| **L0** ✅ | 完成 | 100% | 架构与质量基线已建立 |
| **L1** ✅ | 完成 | 100% | 7天可玩 + 2条剧线 |
| **L2** ✅ | 完成 | 100% | 语义可读层已接入 |
| **L3** ✅ | **完成** | **100%** | 调参 ✅ / 基础测试 ✅ / 全链路测试 ✅ |
| **L4** 🟡 | 部分完成 | **60%** | 经济循环 ✅ / 稳定性工程 🔄 / 数值平衡 ⏸ |
| **L5** 📋 | 筹划中 | 0% | 誓约+新角色+通用口上 |

*标注：✅完成 🔄进行中 🟡部分完成 📋筹划中 ⬜待启动*

---

## 🔴 当前活跃任务（主线 G：L5 解耦底座先行）

> 先解决誓约依赖道具但道具系统未落地的结构缺口，确保后续商店/调教/地图接入时不出现强耦合返工。

### 本轮主任务（先做）

- [ ] 道具系统最小骨架（Inventory + 存档 + 命令门禁）
	- type: core
	- priority: P0
	- milestone: L5
	- est: 120m
	- DoD: WorldState 增加 inventory；SaveService 持久化；CommandGate 支持 required_items；无道具时指令可解释拒绝
	- verify: `python -m unittest tests.test_commands tests.test_save_service -v`
	- owner: pair
	- status: todo
	- updated: 2026-04-16

### 本轮次任务（并行）

- [ ] 誓约最小闭环（戒指校验 + 消耗 + 事件）
	- type: gameplay
	- priority: P1
	- milestone: L5
	- est: 120m
	- DoD: 告白/誓约指令检查 `pledge_ring`；成功后消费道具并写入誓约标记，事件与对话可触发
	- verify: `python -m unittest tests.test_commands tests.test_events tests.test_dialogue_service -v`
	- owner: pair
	- status: todo
	- updated: 2026-04-16

- [ ] commands.toml 校验器（重复 key + 非法字段）
	- type: tooling
	- priority: P1
	- milestone: L4
	- est: 60m
	- DoD: 新增可独立运行的校验入口；发现重复 key 与非法字段时返回非零退出码，并输出问题位置
	- verify: `python -m eral.tools.validate_content --root .`
	- owner: pair
	- status: todo
	- updated: 2026-04-16

### L5 解耦阶段退出条件检查表（阶段一）

- [ ] `requires_item` 在运行时生效（不再仅 UI 提示）
- [ ] 誓约指令对 `pledge_ring` 的校验与消耗可回归验证
- [ ] Inventory 字段可被旧存档平滑降级读取
- [ ] 命令拒绝理由可区分：关系不足/地点不符/道具不足
- [ ] 商店购买 -> 背包入账 -> 指令消费链路打通

---

## 🟡 优先 Backlog（P0 未完成）

- [ ] 建立 commands.toml 重复 key 与非法字段 CI 检查
	- est: 45m
- [ ] 增加内容校验失败样例夹具（bad cases）
	- est: 40m
- [ ] 建立回归日志索引（按日期/测试名/失败点）
	- est: 35m
- [ ] 指令失败反馈文案一致性巡检（地点/时段/关系/状态）
	- est: 50m

---

## 🗓 接下来三周任务包（详细版）

> 原则：每周固定 1 个主任务 + 2 个次任务。先拆依赖，再做玩法；先保接口，再加内容。

### Week 1（依赖拆雷周）

主任务：
- [ ] T1 道具系统最小骨架上线
	- est: 120m
	- DoD: Inventory + Save + Gate 完整接入，`required_items` 可阻断命令
	- verify: `python -m unittest tests.test_commands tests.test_save_service -v`

次任务：
- [ ] T2 命令配置校验闸门上线
	- est: 60m
	- DoD: validate_content 拦截重复 key/非法字段；输出可定位配置行
	- verify: `python -m eral.tools.validate_content --root .`

- [ ] T3 存档兼容回归 3 场景
	- est: 75m
	- DoD: 旧档缺字段/旧字段/脏字段三类均可读且有降级策略（含 inventory 缺失）
	- verify: `python -m unittest tests.test_save_service -v`

### Week 2（誓约与商店闭环周）

主任务：
- [ ] T4 誓约最小可玩闭环
	- est: 120m
	- DoD: 1 条誓约指令 + 2 个事件钩子 + 4 条对话分支；戒指条件与消耗生效
	- verify: `python -m unittest tests.test_events tests.test_commands tests.test_dialogue_service -v`

次任务：
- [ ] T5 商店最小闭环（3~5 商品）
	- est: 90m
	- DoD: 可购买 `pledge_ring` 与至少 2 类消耗品；购买失败理由可解释
	- verify: `python -m unittest tests.test_commands tests.test_smoke_playable -v`

- [ ] T6 指令可用性解释器增强（含道具不足）
	- est: 60m
	- DoD: gate 拒绝时统一原因码 + 中文提示，新增 item_not_enough
	- verify: `python -m unittest tests.test_commands -v`

### Week 3（地图与调教骨架周）

主任务：
- [ ] T7 地图分层骨架（阵营区/子区/建筑）
	- est: 120m
	- DoD: 支持阵营区域与子地区建模；保留现有 navigation 接口兼容
	- verify: `python -m unittest tests.test_navigation tests.test_commands -v`

次任务：
- [ ] T8 调教系统骨架（判定/执行/结算）
	- est: 150m
	- DoD: 至少 3 条调教指令通过统一管线，走 `gate -> source -> settlement`
	- verify: `python -m unittest tests.test_commands tests.test_settlement -v`

- [ ] T9 内容校验增强（角色包必填与引用完整性）
	- est: 60m
	- DoD: character/events/dialogue 增加必填项与引用检查，错误信息带角色 key 与文件路径
	- verify: `python -m eral.tools.validate_content --root .`

### 暂缓队列（明确后置）

- [ ] T10 数值平衡与调参说明（测试员恢复后）
	- est: 60m
	- reason: 需要专门测试员参与体验与边界验证

- [ ] T11 鼠标点击交互（终端点击等效编号）
	- est: 240m
	- reason: 非关键路径，优先级低于稳定性与内容工程

- [ ] T12 Web 交互原型预研
	- est: 120m
	- reason: 需先明确 UI 长线方向，再决定是否投入

---

## 📋 当前事实（系统完成度检查清单）

**核心架构**
- [x] `create_application()` 已是装配入口
- [x] `SOURCE -> settlement -> BASE/PALAM/CFLAG/TFLAG` 已跑通
- [x] 角色包已支持 `BASE/PALAM/ABL/TALENT/CFLAG/MARK` 初始属性

**玩法系统**
- [x] 同行、约会、轻亲密起点与存档系统已存在
- [x] 体力/气力系统规格文档已建立，完整链路已通过
- [x] 关系系统已接入，关系阶段阈值已可配置化
- [x] 事件/口上系统已通过，事件触发匹配已完整

**经济系统**
- [x] 资金系统已实现：双账户 + WalletService + 旧存档兼容
- [x] 工作系统已实现：office_shift / extra_shift 工作指令
- [x] 委托系统已实现：派遣/推进/结算全流程
- [x] 港区开发系统已实现：3设施 + 效果整合整

**内容量**
- [x] 54个指令已接入 commands.toml
- [x] 企业、拉菲、标枪三个正式角色（各>=20事件、>=30对话）
- [x] L4 经济循环 14 天合并烟测已通过
- [x] ABC级别测试覆盖率 100%（326个unittest通过）

---

## 📈 本周复盘（每周五更新）

- **本周完成**：港区开发系统（3设施+FacilityService+效果整合）；关系成长公式调参（base_scale）；L4经济循环14天合并烟测
- **本周阻塞**：无
- **指标**：
	- 自动化测试通过率：326/326（100%）
	- 正式角色总数：3
	- 指令总数：54 + 2工作 + 3恢复
	- UI已覆盖：主界面(6区) + 能力显示(5tab)

---

## 📚 计划中的系统（L5 筹划中）

> 说明：人物内容补充先降级，待人物编辑器完善后再提级执行。

| 系统 | 优先级 | 估算 | 依赖 |
|------|--------|------|------|
| 道具系统最小骨架（Inventory + Gate） | P0 | 120m | 无 |
| 誓约层指令+事件+对话 | P1 | 120m | 道具系统最小骨架 |
| 商店最小闭环（含誓约戒指） | P1 | 90m | 道具系统最小骨架 |
| 调教系统骨架（三段式） | P1 | 150m | 命令门禁稳定 + settlement稳定 |
| 地图分层骨架（阵营/子区/建筑） | P1 | 120m | navigation 接口兼容层 |
| 贝尔法斯特角色包 | P2 | 120m | L3 exit + 编辑器完善 |
| 通用口上兜底（54指令） | P2 | 90m | L3 exit + 编辑器完善 |
| 天气与季节系统 | P1 | 120m | L5基础 |
| ASCII 地图渲染 UI | P2 | 120m | 地图分层骨架 |

---

## 📦 历史档案（已完成任务）

<details>
<summary>主线 L0：架构与质量基线</summary>

- [x] 统一 TODO 与指导书的里程碑、优先级、状态口径
- [x] 建立运行日志最小规范并接入关键链路
- [x] 增加"连续 3 天可玩"烟测

</details>

<details>
<summary>主线 L1：核心语义完整</summary>

- [x] 完成关系阶段命名统一（陌生→友好→喜欢→爱→誓约）
- [x] 让 embarrassed、angry、drunk 参与至少 3 条真实分支
- [x] 补齐 C/B 批命令测试覆盖
- [x] 充实企业/拉菲事件与对话
- [x] 端到端约会线 + 轻亲密线可玩测试
- [x] 连续 7 天可玩烟测
- [x] MARK 分支扩展至事件层
- [x] 为 5 个角色补齐阶段差分文本

</details>

<details>
<summary>主线 L2：语义可读层与流程精细化</summary>

- [x] 建立 ABL/TALENT/CFLAG 常用语义映射层
- [x] 将指令可用性判定拆分为多层 Gate
- [x] 增加约会后事件结算层（after_date_event）
- [x] 建立内容密度自动统计报告

</details>

<details>
<summary>主线 L3：体力系统与 Backlog</summary>

- [x] 完成体力/气力系统首轮平衡表（指令分档 + 恢复分档）
- [x] 修正恢复指令 key 冲突与命令清单一致性
- [x] 为 VitalGate / 晕倒推进 / 恢复链路补充端到端回归
- [x] 移除全部 starter 占位角色，新增标枪正式角色包
- [x] 修 ABL_INTIMACY_INDEX bug（12→9）+ 接入 ABL 升级管道到结算流程
- [x] 修复 Windows / Python 3.14 下角色包拆分初值测试的临时目录权限问题
- [x] 地点扩展到 8 到 12，并给每个地点补玩法标签
- [x] 约会四地点分支各至少 1 条（食堂/码头/宿舍/浴场）
- [x] 指令失败反馈标准化（地点/时段/关系/状态原因）
- [x] 清理测试文件 UTF-8 BOM 与行尾格式不一致问题

</details>

<details>
<summary>主线 L4：经济循环完整化</summary>

- [x] 资金系统设计文档审核与字段对齐
- [x] 扩展 WorldState + SaveService 支持双账户
- [x] 创建 WalletService 统一资金操作接口
- [x] 创建 LedgerService 流水记录
- [x] 工作系统规范与指令集已规划
- [x] 在 commands.toml 中加入工作类指令
- [x] 工作指令执行后资金记账流程集成
- [x] 委托系统规范与配置已完成
- [x] 扩展 CharacterState.is_on_commission 与 SaveService 持久化
- [x] 创建 CommissionService 协调委托派遣 + 时段推进 + 奖励结算
- [x] 委托派遣与结算 end-to-end 测试
- [x] 港区开发系统规范与首批设施配置
- [x] 扩展 WorldState.facility_levels + SaveService 持久化
- [x] 创建 FacilityService 协调升级检查 + 扣费 + 效果广播
- [x] 港区开发 end-to-end 测试
- [x] L4 经济循环 14 天可玩性烟测
- [x] UI 展示与交互起点

</details>

---

## 下一阶段快速参考

**即将开始**：L5 解耦底座三周包（T1-T9）  
**后续规划**：测试员恢复后推进数值平衡（T10）  
**长期计划**：交互升级（T11/T12）+ 天气系统 + 角色包扩容 + 地图渲染增强

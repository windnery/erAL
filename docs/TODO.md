# erAL TODO

> 约束：玩法语义优先继承 eraTW，工程实现参考 erArk 的长期迭代经验。

---

## 🚀 当前最优先（下次开发抓手）

选 1 个主任务（蓝框）+ 2 个次任务（绿框）

| # | 任务 | 里程碑 | 类型 | Est | 状态 |
|---|------|--------|------|-----|------|
| 1 | 誓约-商店垂直切片（买戒指 -> 誓约 -> 阶段写入） | L5 | gameplay | 180m | ✅ done |
| 2 | 商店骨架（catalog + shopfront + 购买结算） | L5 | core | 120m | ✅ done |
| 3 | 誓约内容闭环（成功/失败结果标签 + 对话分支） | L5 | content | 120m | ✅ done |
| 4 | 皮肤与外观底座（持有/切换/誓约奖励/口上条件） | L5 | architecture | 180m | ✅ done |
| 5 | 时间与日历底座（24 小时制 / 节日 / 排班 / 日历指令） | L5 | architecture | 240m | ✅ done |
| 6 | 季节与节日规则接入（皮肤上架 / 内容条件 / 活动标签） | L5 | content | 150m | 🟢 ready |
| 7 | commands.toml 校验器（重复 key + 非法字段） | L4 | tooling | 60m | 🟢 ready |
| 8 | 存档兼容回归包（旧档读取 + 字段降级） | L4 | test | 75m | 🟢 ready |
| 9 | 地图分层基础（大区/子区/地点/归属/分布入口） | L5 | architecture | 180m | ✅ done |
| 10 | 调教系统骨架（判定/执行/结算三段） | L5 | gameplay | 150m | 🟡 gated |
| 11 | 内容校验增强（角色包必填与引用完整性） | L4 | tooling | 60m | 🟢 ready |
| 12 | 动态地图分布规则第一版（饭点/夜间回流/阵营偏好/玩家位置修正） | L5 | architecture | 180m | ✅ done |
| 13 | 阵营生活区扩充到更多阵营（重樱 / 铁血 / 东煌 / 混合） | L5 | architecture | 120m | 🔴 next |
| 14 | 路径引擎（Dijkstra 最短路径 / 按边权耗时 / 分组目的地 UI） | L5 | architecture | 90m | ✅ done |
| 15 | 动态地图分布规则第二版（阵营分流 / 承载溢出 / 时段细化） | L5 | architecture | 150m | 📋 planned |

**执行顺序**：L5 当前先完成地图系统（路径引擎 ✅ → 阵营扩充 → 分布 v2 → ASCII 地图整理），再回头补季节/节日等内容驱动层，最后进入调教与更重的系统入口。

---

## 🧱 解耦优先规则

1. 任何跨系统功能必须先落地在 `gate + service + data` 三层，不允许把规则硬写进 UI。
2. 前提条件统一放在命令门禁与统一判定层，事件层只做触发和表现。
3. 道具系统已经落地为 `inventory + item catalog + required_items + resolution`，后续商店与礼物都只能复用它，不再新增平行背包。
4. 新系统开发顺序固定：`最小数据结构 -> 可执行门禁 -> 最小闭环玩法 -> 内容扩展`。
5. 商店入口可以后续做成地点、NPC 或菜单，但底层购买结算必须独立于入口形态。

---

## ⚙️ 执行规则

1. 本看板定义“做什么”，`docs/AI_LONG_TERM_VIBE_GUIDE.md` 定义“如何做”。
2. 优先级与里程碑定义见 AI_GUIDE 第 4 节，本文件不重复。
3. 任务卡字段规范见 AI_GUIDE 第 5 节，本文件不重复。
4. 每次开发会话只做 `1 个主任务 + 2 个次任务`，禁止并行开太多支线。
5. 每个任务必须是 25 到 90 分钟可完成的颗粒度。
6. 任务必须写清可验证结果，不写“继续优化”“补一补”这类模糊描述。

---

## 📊 里程碑进度一览表

| 里程碑 | 状态 | 完成度 | 关键指标 |
|--------|------|--------|---------|
| **L0** ✅ | 完成 | 100% | 架构与质量基线已建立 |
| **L1** ✅ | 完成 | 100% | 7 天可玩 + 2 条剧线 |
| **L2** ✅ | 完成 | 100% | 语义可读层已接入 |
| **L3** ✅ | 完成 | 100% | 调参 ✅ / 基础测试 ✅ / 全链路测试 ✅ |
| **L4** 🟡 | 部分完成 | 65% | 经济循环 ✅ / 稳定性工程 🔄 / 数值平衡 ⏸ |
| **L5** 🟡 | 推进中 | 92% | 背包 ✅ / 誓约底座 ✅ / 商店闭环 ✅ / 皮肤与外观底座 ✅ / 时间与日历底座 ✅ / 季节规则接入 📋 / 地图分层基础 ✅ / 动态地图分布 v1 ✅ / 路径引擎 ✅ / 阵营扩充 🔴 / 分布 v2 📋 / ASCII 地图整理 📋 |

*标注：✅完成 🔄进行中 🟡部分完成 📋筹划中 ⬜待启动*

---

## 🔴 当前活跃任务（主线 G：L5 地图系统推进）

> 路径引擎已落地：`PortConnection` 支持 `cost_minutes` 差异化边权；`PortMap` 内置 Dijkstra 最短路径与可达目的地查询；`NavigationService` 重构为 `plan_move` / `available_destinations` / `execute_move` 三层，返回 UI 无关的 `MovePlan` 结构化数据；CLI 移动菜单已改为按大区分组显示所有可达地点及耗时。下一步先扩充阵营生活区（重樱/铁血/东煌/混合），再做分布规则 v2（阵营分流/承载溢出/时段细化），最后推进 ASCII 地图整理。

### 本轮主任务（先做）

- [x] 誓约-商店垂直切片（买戒指 -> 誓约 -> 阶段写入）
	- type: gameplay
	- priority: P0
	- milestone: L5
	- est: 180m
	- DoD: 玩家可通过最小商店入口购买 `pledge_ring`；`oath` 成功/失败都能返回明确结果；成功后消耗戒指并进入 `誓约` 阶段
	- verify: `python -m unittest tests.test_cli_shop tests.test_shop_service tests.test_commands tests.test_events tests.test_dialogue tests.test_save_load -v`
	- owner: pair
	- status: done
	- updated: 2026-04-17

### 本轮次任务（并行）

- [x] 商店骨架（catalog + shopfront + 购买结算）
	- type: core
	- priority: P1
	- milestone: L5
	- est: 120m
	- DoD: 至少支持 1 个 `general_shop` 店面、按商品价格扣款、按商品分类过滤、按库存结果入账背包
	- verify: `python -m unittest tests.test_shop_service tests.test_commands -v`
	- owner: pair
	- status: done
	- updated: 2026-04-17

- [x] 誓约内容闭环（成功/失败结果标签 + 对话分支）
	- type: content
	- priority: P1
	- milestone: L5
	- est: 120m
	- DoD: `oath_success` / `oath_failure` 结果标签可命中；至少 1 名正式角色有成功与失败差分文本
	- verify: `python -m unittest tests.test_events tests.test_dialogue tests.test_commands -v`
	- owner: pair
	- status: done
	- updated: 2026-04-17

- [x] 皮肤与外观底座（持有/切换/誓约奖励/口上条件）
	- type: architecture
	- priority: P1
	- milestone: L5
	- est: 180m
	- DoD: 角色拥有 `owned_skins / equipped_skin_key / removed_slots`；CLI 可购买与切换皮肤；`oath_reward` 自动发放；事件/口上可按皮肤分支
	- verify: `python -m unittest tests.test_content_loading tests.test_bootstrap tests.test_cli_shop tests.test_commands tests.test_events tests.test_dialogue tests.test_save_load -v`
	- owner: pair
	- status: done
	- updated: 2026-04-17

- [x] 时间与日历底座（24 小时制 / 节日 / 排班 / 日历指令）
	- type: architecture
	- priority: P1
	- milestone: L5
	- est: 240m
	- DoD: 世界拥有真实日期与时钟；移动和指令可推进固定分钟；`calendar.toml` / `work_schedules.toml` 已接入；CLI 可查看相邻几天的节日与舰娘工作安排
	- verify: `python -m unittest tests.test_time_system tests.test_navigation tests.test_commands tests.test_content_loading tests.test_calendar_command tests.test_save_load -v`
	- owner: pair
	- status: done
	- updated: 2026-04-18

- [x] 地图分层基础（大区/子区/地点/归属/分布入口）
	- type: architecture
	- priority: P1
	- milestone: L5
	- est: 180m
	- DoD: `port_map` 支持大区/子区/地点/槽位；正式角色具备阵营与宿舍归属字段；初版地点在场舰娘分布服务可运行；CLI 已支持地点列表分页、自动选中与切换当前目标
	- verify: `python -m unittest tests.test_port_map tests.test_visibility tests.test_character_packs tests.test_distribution tests.test_cli_selection -v` + `python -m unittest discover -s tests -t .`
	- owner: pair
	- status: done
	- updated: 2026-04-18

- [x] 动态地图分布规则第一版（饭点/夜间回流/阵营偏好/玩家位置修正）
	- type: architecture
	- priority: P0
	- milestone: L5
	- est: 180m
	- DoD: 非强制状态角色可基于当前时间、真实工作排班、宿舍归属、活动标签和玩家位置得到稳定地点分布；饭点采用“基础饭点 + 角色级轻微偏移”以减少餐饮区拥挤；深夜优先回 `home_location_key`；委托/同行/约会仍保持最高优先级；地图 roster 与自动选中继续兼容；刷新频率保持在 bootstrap / 读档 / wait 等低频节点
	- verify: `python -m unittest tests.test_distribution tests.test_navigation tests.test_time_system tests.test_cli_selection tests.test_commands -v` + `python -m unittest discover -s tests -t .`
	- owner: pair
	- status: done
	- updated: 2026-04-18

- [x] 路径引擎（Dijkstra 最短路径 / 按边权耗时 / 分组目的地 UI）
		- type: architecture
		- priority: P0
		- milestone: L5
		- est: 90m
		- DoD: `PortConnection` 支持 `cost_minutes`；`PortMap` 内置 Dijkstra `shortest_path` 与 `reachable_destinations`；`NavigationService` 暴露 `MovePlan` 结构化数据（含路径/耗时/区域信息），CLI 按大区分组显示可达目的地及耗时；`move_player` 向后兼容委托给 `execute_move`；404 项全量回归通过
		- verify: `python -m unittest tests.test_navigation tests.test_port_map -v` + `python -m unittest discover -s tests -t .`
		- owner: pair
		- status: done
		- updated: 2026-04-18

- [x] `required_items` 在运行时生效
- [x] `pledge_ring` 可被 `oath` 指令校验与消费
- [x] `inventory` 可被旧存档平滑降级读取
- [x] 命令拒绝理由可区分：关系不足/地点不符/道具不足
- [x] 商店购买 -> 背包入账 -> 指令消费链路打通
- [x] 誓约成功/失败都能触发独立结果标签或对话分支
- [ ] 通用商店骨架能复用到 `general_shop` 与 `skin_shop`
- [x] 角色皮肤可被购买、切换并进入存档
- [x] `oath_reward` 皮肤可自动发放
- [x] 事件与口上可按当前皮肤分支
- [x] 世界已拥有真实日期与 24 小时时钟
- [x] 移动与指令可消耗固定分钟数
- [x] 日历指令可查看相邻几天的节日与舰娘工作安排
- [x] `port_map` 已支持大区/子区/地点/槽位的基础结构
- [x] 正式角色已具备 `faction_key / residence_area_key / dorm_group_key`
- [x] 初版地点在场舰娘分布服务与自动选中 helper 已存在
- [x] CLI 已接入地点分页、当前目标切换与“仅对当前目标出指令”流
- [x] 动态地图分布已支持真实工作排班、饭点错峰与深夜回流
- [x] 路径引擎已支持 Dijkstra 最短路径与按边权差异化耗时
- [x] CLI 移动菜单已改为按大区分组显示所有可达地点及耗时
- [x] `MovePlan` 结构化数据为后续 UI 替换预留接口

### 地图系统接下来的步骤

- [ ] 阵营生活区扩充到更多阵营（重樱 / 铁血 / 东煌 / 混合）
	- est: 120m
	- note: 先补 TOML 数据结构和角色归属字段，不急着填大量角色内容

- [ ] 动态地图分布规则第二版（阵营分流 / 承载溢出 / 时段细化）
	- est: 150m
	- note: 在 v1 基础上加入阵营归属分流、capacity_soft/overflow_targets 承载溢出、更细的时段权重

- [ ] ASCII 地图整理（确认文件格式 + 拆分区域 Map 文件）
	- est: 90m
	- note: 为后续可视化做准备，确定 Map 文件格式，拆分区域渲染数据

- [ ] 地点 roster / 地图 UI 深化（更明确的切页与当前位置信息）
	- est: 120m
	- note: 可后续与 ASCII 地图渲染一起推进

---

## 🟡 优先 Backlog（P0 未完成）

- [ ] 建立 commands.toml 重复 key 与非法字段 CI 检查
	- est: 45m
- [ ] 增加内容校验失败样例夹具（bad cases）
	- est: 40m
- [ ] 建立回归日志索引（按日期/测试名/失败点）
	- est: 35m
- [ ] 指令失败反馈文案一致性巡检（地点/时段/关系/状态/道具）
	- est: 50m

---

## 🗓 接下来三周任务包（详细版）

> 原则：每周固定 1 个主任务 + 2 个次任务。先打通垂直切片，再扩入口和内容；先保底层接口，再加 NPC 语义。

### Week 1（垂直切片周）

主任务：
- [x] T1 誓约-商店最小闭环
	- est: 180m
	- DoD: 至少存在 1 个可访问的日常店入口，可购买 `pledge_ring`，并完成一次成功誓约与一次失败誓约回归
	- verify: `python -m unittest tests.test_cli_shop tests.test_shop_service tests.test_commands tests.test_events tests.test_dialogue tests.test_save_load -v`

次任务：
- [x] T2 商店目录与购买结算服务
	- est: 120m
	- DoD: `ShopService` 支持按 `shopfront_key` 列货、校验余额、入账 `inventory`、记录失败原因
	- verify: `python -m unittest tests.test_shop_service -v`

- [x] T3 誓约成功/失败内容钩子
	- est: 120m
	- DoD: `oath_success` / `oath_failure` 可从命令结算结果进入内容层，至少 1 名角色有差分文本
	- verify: `python -m unittest tests.test_events tests.test_dialogue tests.test_commands -v`

### Week 2（商店扩展周）

主任务：
- [ ] T4 两类商店骨架成型
	- est: 120m
	- DoD: `general_shop` 与 `skin_shop` 共用同一套 catalog/shopfront 数据结构，暂时只要求日常店可购买、皮肤店可列货
	- verify: `python -m unittest tests.test_shop_service tests.test_content_loading -v`

次任务：
- [ ] T4.5 皮肤内容扩展（企业之外的角色皮肤 + 活动标签）
	- est: 120m
	- DoD: 至少再补 1 到 2 名正式角色的默认/活动或誓约皮肤；`summer` / `oath` 等标签有真实内容消费方
	- verify: `python -m unittest tests.test_content_loading tests.test_dialogue tests.test_events -v`

- [ ] T4.6 季节与节日规则接入
	- est: 150m
	- DoD: `season` / `festival_tags` 可被皮肤上架、事件与口上条件真实消费；至少 1 个节日标签和 1 个季节标签驱动实际内容差分
	- verify: `python -m unittest tests.test_calendar_command tests.test_dialogue tests.test_events tests.test_cli_shop -v`

- [ ] T5 商店入口语义预留
	- est: 60m
	- DoD: 商店入口可以被地点或角色调用，不把明石/不知火写死进购买逻辑
	- verify: `python -m unittest tests.test_shop_service tests.test_navigation -v`

- [ ] T6 指令统一判定接口扩展到接吻
	- est: 90m
	- DoD: `kiss` 可选择接入统一判定层，失败时给出与门禁不同的反馈
	- verify: `python -m unittest tests.test_commands tests.test_command_gates -v`

### Week 3（稳定性与后续底座周）

主任务：
- [ ] T7 commands.toml 校验器
	- est: 60m
	- DoD: validate_content 拦截重复 key、非法字段与常见结构错配；输出可定位问题路径
	- verify: `python -m eral.tools.validate_content --root .`

次任务：
- [ ] T8 内容校验增强（角色包必填与引用完整性）
	- est: 60m
	- DoD: character/events/dialogue 增加必填项与引用检查，错误信息带角色 key 与文件路径
	- verify: `python -m eral.tools.validate_content --root .`

- [ ] T9 地图分层骨架前置设计
	- est: 120m
	- DoD: 阵营区/子区/建筑三层数据结构与兼容层设计文档完成，确保后续可挂商店地点与 NPC 刷新
	- verify: design review

### 暂缓队列（明确后置）

- [ ] T10 明石 / 不知火商店入口
	- est: 120m
	- reason: 需要先有角色包和最小商店入口，再把她们作为入口语义接上

- [ ] T11 皮肤购买后的换装效果
	- est: 150m
	- reason: 需先明确皮肤数据格式与表现层，不应在商店骨架阶段提前绑定

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
- [x] `oath` 指令、统一判定入口与誓约阶段覆盖已落地

**经济与道具体系**
- [x] 资金系统已实现：双账户 + WalletService + 旧存档兼容
- [x] 工作系统已实现：`office_shift` / `extra_shift` 工作指令
- [x] 委托系统已实现：派遣/推进/结算全流程
- [x] 港区开发系统已实现：3 设施 + 效果整合
- [x] 玩家背包已实现：`inventory` + item catalog + 存档兼容
- [x] 命令已支持 `required_items` 与道具不足原因反馈
- [x] 最小商店入口已实现：CLI 可进入 `general_shop` 并购买 `pledge_ring`
- [x] `oath_success` / `oath_failure` 结果标签已接入内容选择
- [x] 皮肤与外观底座已实现：`skins.toml` / `appearances.toml` / `SkinService`
- [x] CLI 已支持 `skin_shop` 购买与衣柜切换
- [x] `oath_reward` 与皮肤分支内容已接入
- [x] 时间与日历底座已实现：真实日期 / 24 小时时钟 / `TimeService`
- [x] `calendar.toml` / `work_schedules.toml` 已接入
- [x] CLI 已支持日历指令

**内容量**
- [x] 54 个以上指令已接入 `commands.toml`
- [x] 企业、拉菲、标枪三个正式角色（各 >= 20 事件、>= 30 对话）
- [x] L4 经济循环 14 天合并烟测已通过
- [x] 自动化测试 404 项通过

---

## 📈 本周复盘（每周五更新）

- **本周完成**：L5 道具底座（`inventory` / `items.toml` / `required_items`）；`ShopService` + `shopfronts.toml`；CLI 最小商店入口；`oath_success` / `oath_failure` 结果标签与企业差分口上；皮肤与外观底座（内容定义 / 存档 / skin shop / 衣柜 / oath reward / 皮肤分支）；时间与日历底座（真实日期 / 24 小时时钟 / 固定分钟耗时 / 节日 / 排班 / 日历指令）；地图分层基础（大区 / 子区 / 槽位 / 角色归属 / 在场分布 / CLI 分页选中）；动态地图分布第一版（真实工作排班 / 饭点错峰 / 深夜回流 / 低频刷新）；路径引擎（Dijkstra 最短路径 / 按边权差异化耗时 / MovePlan 结构化移动 / CLI 分组目的地）；全量回归
- **本周阻塞**：无
- **指标**：
	- 自动化测试通过率：404/404（100%）
	- 正式角色总数：3
	- 指令总数：54+，含工作与恢复指令
	- 新增 L5 完成项：背包、誓约底座、最小道具门禁、皮肤与外观底座、时间与日历底座、地图分层基础、动态地图分布第一版、路径引擎

---

## 📚 计划中的系统（L5 持续推进）

> 说明：人物内容补充先降级，待人物编辑器完善后再提级执行。

| 系统 | 优先级 | 估算 | 依赖 |
|------|--------|------|------|
| 誓约-商店垂直切片（戒指购买 -> 誓约） | P0 | 180m | 已有 inventory + oath 底座 |
| 商店骨架（catalog + shopfront + purchase） | P1 | 120m | inventory + wallet |
| 誓约层事件与对话 | P1 | 120m | `oath` 指令与事件管线 |
| 两类商店共用数据结构（general / skin） | P1 | 60m | 商店骨架 |
| 皮肤与外观底座（持有/切换/誓约奖励/皮肤条件） | P1 | 180m | skin_shop + SceneContext 扩展 |
| 时间与日历底座（24 小时 / 节日 / 排班 / calendar） | P1 | 240m | WorldState / CLI / 内容规则底层 |
| 调教系统骨架（三段式） | P1 | 150m | 命令门禁稳定 + settlement 稳定 |
| 地图分层骨架（阵营/子区/建筑） | P1 | 120m | navigation 接口兼容层 |
| 贝尔法斯特角色包 | P2 | 120m | L5 闭环阶段稳定 |
| 通用口上兜底（54 指令） | P2 | 90m | 内容编辑器完善 |
| 天气与季节系统 | P1 | 120m | L5 基础 |
| 路径引擎（Dijkstra / 边权耗时 / 分组 UI） | P0 | 90m | 地图分层基础 ✅ |
| 动态地图分布 v2（阵营分流 / 承载溢出） | P1 | 150m | 路径引擎 + 阵营扩充 |
| ASCII 地图渲染 UI | P2 | 120m | 路径引擎 + 地图整理 |

---

## 📦 历史档案（已完成任务）

<details>
<summary>主线 L0：架构与质量基线</summary>

- [x] 统一 TODO 与指导书的里程碑、优先级、状态口径
- [x] 建立运行日志最小规范并接入关键链路
- [x] 增加“连续 3 天可玩”烟测

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

<details>
<summary>主线 L5：道具与誓约底座</summary>

- [x] 扩展 WorldState + SaveService 支持 `inventory`
- [x] 新增 `items.toml` 与最小物品加载器
- [x] 在命令门禁中接入 `required_items`
- [x] 新增 `oath` 指令与统一成功率判定入口
- [x] 成功誓约后以 `oath` mark 覆盖关系阶段
- [x] 全量回归通过（336 项 unittest）

</details>

---

## 下一阶段快速参考

**即将开始**：L5 阵营生活区扩充（重樱 / 铁血 / 东煌 / 混合）
**后续规划**：分布规则 v2 + ASCII 地图整理 + 季节与节日规则接入
**长期计划**：ASCII 地图可视化 + 商店 NPC 化（明石/不知火）+ 调教系统 + 交互升级

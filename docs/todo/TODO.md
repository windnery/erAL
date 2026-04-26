# erAL TODO（系统/代码侧）

更新时间：2026-04-26

> 当前 MVP 开发表请优先查看 [MVP.md](MVP.md)。本文件只保留系统/代码侧的执行任务，已完成底座不要重复列入待办。

---

## 当前进度总览

核心结算管线（SOURCE → SOURCE_EXTRA → SOURCE_CBVA → CUP → PALAM/CFLAG → JUEL → 刻印 → ABLUP）已全部打通。已统一到 `SettlementService.settle_actor()` 单入口。

- **结算主线**：✅ 6相位完整
- **测试**：160 通过
- **最大瓶颈**：结算层周围支撑系统大量缺失（装备槽、反击、高潮、体液、体位倍率）

---

# 一、结算层

核心计算管线，目前主线已通，缺以下分支模块。

## S1. SOURCE_POSE — 体位 SOURCE 倍率

- [ ] S1.1 在 `data/base/rules/` 下创建 `source_pose.toml`，定义体位→SOURCE倍率映射
- [ ] S1.2 在 `settlement.py` Phase -1 增加 `apply_source_pose(actor, position_key)` 调用
- [ ] S1.3 编写 `systems/source_pose.py` 应用逻辑

对应 eraTW: `SOURCE_POSE.ERB`

## S2. NPC 高潮判定（ORGASM）

- [ ] S2.1 在 `data/base/rules/` 下创建 `orgasm.toml`，定义高潮阈值（各快感PLV等级）
- [ ] S2.2 编写 `systems/orgasm.py`，settlement 后检查 PALAM 快感是否达到阈值
- [ ] S2.3 高潮时产生额外 SOURCE（射精后快感加成）和 CFLAG 写入
- [ ] S2.4 接入 ejaculation_service（玩家射精 + NPC高潮联动）

对应 eraTW: `TRACHECK_ORGASM.ERB`

## S3. 射精 SOURCE 处理

- [ ] S3.1 射精前 SOURCE 修正（绝顶感度压制等）
- [ ] S3.2 射精后 SOURCE 修正（贤者时间、余韵快感等）
- [ ] S3.3 接入 settlement Phase -1（射精后转 Phase 时触发）

对应 eraTW: `SOURCE_射精確定前/後処理.ERB`

## S4. STAIN — 体液染色系统

- [ ] S4.1 定义 STAIN 轴数据结构（8种体液 × 多部位）
- [ ] S4.2 编写 `systems/stain.py`，settlement 后根据 SOURCE 类型写入 STAIN
- [ ] S4.3 STAIN 值接入 SceneContext（供口上/事件使用）
- [ ] S4.4 STAIN 随时间衰减（PALAM decay 之后）

对应 eraTW: `STAIN.ERB`，8种体液：爱液、阴茎、精液、肠液、乳汁、黏液、处女血、巧克力

## S5. 完整反击系统（COUNTER）

- [ ] S5.1 在 `data/base/rules/` 下创建 `counter.toml`，定义反击触发条件
- [ ] S5.2 编写 `systems/counter.py`，训练中概率触发 NPC 反击
- [ ] S5.3 反击产生 SOURCE 写入 player_stats
- [ ] S5.4 反击脱衣、反击插入等子类型
- [ ] S5.5 反击结果接入 SceneContext（口上/事件变体）

对应 eraTW: `COUNTER\` 6个文件，`COUNTER_TYPE.ERB`, `COUNTER_SOURCE.ERB`, `COUNTER_SELECT.ERB`

## S6. 破处判定（LOST_VIRGIN）

- [ ] S6.1 在 settlement 后检查 PALAM:V経験 首次 >0，写入 CFLAG 破处标记
- [ ] S6.2 破处事件触发（出血 SOURCE、特殊口上）

对应 eraTW: `TRACHECK_LOST_VIRGIN.ERB`

## S7. 特殊状态处理

- [ ] S7.1 睡眠深度系统（睡眠中被触摸时的不同反应层级）
- [ ] S7.2 泥酔处理（醉酒状态对 SOURCE 的修正）

对应 eraTW: `睡眠深度処理.ERB`, `泥酔処理.ERB`

## S8. source_cbva.toml 补全

- [ ] S8.1 检查当前 identity 通行的 SOURCE 是否需要 CBVA 规则
- [ ] S8.2 ABL scale 参数审查（全部 0.1 是否符合 eraTW 标准）

---

# 二、指令层

## C1. 指令可用性判定 — 拒绝系统

- [ ] C1.1 扩展 `command_gates.py`，增加以下 gate：
  - 刻印等级判定（反发刻印≥3 拒绝 H 系指令）
  - TALENT 判定（感情缺乏降低指令可用性）
  - PALAM 等级判定（润滑不足拒绝 V 系指令）
  - 关系阶段判定（陌生人拒绝接吻）
- [ ] C1.2 拒绝理由分类返回（体力不足/关系不足/刻印拒绝/装备不满足）
- [ ] C1.3 拒绝理由接入口上系统（显示角色拒绝台词）
- [ ] C1.4 指令可用性缓存（同一帧内 conditions 不变时复用）

对应 eraTW: `COMABLE.ERB` + `COMABLE2.ERB` + 分类 COMABLE_*.ERB 共 8 个文件

## C2. 服装/装备槽系统

- [ ] C2.1 定义 EQUIP 轴数据结构，与 eraTW 32 槽位对齐
- [ ] C2.2 编写 `systems/equip.py`，装备穿脱、槽位互斥（如穿连衣裙时不能穿裤子）
- [ ] C2.3 脱衣逻辑：按槽位逐层脱，支持部分脱（只脱上衣/只脱下着）
- [ ] C2.4 装备状态接入指令可用性（调教系要求脱衣完成）
- [ ] C2.5 装备数值效果接入 SceneContext 和 SOURCE (如性感内衣提升情爱)

对应 eraTW: `OBJ/CLASS/` 20+ 服装类文件，`CLOTHES.ERB`, `衣服\` 6个文件

## C3. 日常系指令

- [ ] C3.1 talk 指令（对话，提升情爱 SOURCE）
- [ ] C3.2 greet 指令（打招呼，触发随机事件）
- [ ] C3.3 observe 指令（观察角色状态）
- [ ] C3.4 gift 指令（赠礼 — gift_service 已有，完善赠礼选择 UI 流）
- [ ] C3.5 touch/headpat 等轻度接触指令

对应 eraTW: `日常系\` 目录，`COMF` 日常部分

## C4. 外出系指令

- [ ] C4.1 邀请约会（invite_date — date_service 已有，完善前序事件）
- [ ] C4.2 邀请同行（start_follow — companion_service 已有）
- [ ] C4.3 外出就餐、外出购物等

对应 eraTW: `外出系\` 目录

---

# 三、系统层

## Y1. 天气效果接入 gameplay

- [ ] Y1.1 雨天对体力恢复的影响
- [ ] Y1.2 天气对角色心情（PALAM）的影响
- [ ] Y1.3 天气对遭遇率的影响
- [ ] Y1.4 天气接入 SceneContext 和事件条件

当前 weather.py 只有基础框架，效果未落地。

## Y2. 商店完善

- [ ] Y2.1 商品库存系统（有数量限制，定期刷新）
- [ ] Y2.2 购买后效果（道具使用接入指令效果系统）
- [ ] Y2.3 打折/涨价事件

当前 shop.py 有基础购买和库存管理。

## Y3. 委托系统完善

- [ ] Y3.1 委托条件判定（角色 ABL 等级需求）
- [ ] Y3.2 委托奖励结算（金钱 + 经验 + 好感）
- [ ] Y3.3 委托失败处理

当前 commissions.py 有派遣/计时/结算。

## Y4. 训练系统完善

 （training.py 已有 session 管理、counter 检测、高潮映射，以下为扩展）

- [ ] Y4.1 更多体位（当前只有 missionary/behind/standing，需补充 cowgirl/face/backseat 等）
- [ ] Y4.2 体位切换时的 SOURCE 连续性
- [ ] Y4.3 道具使用（道具对 SOURCE 的加成）

## Y5. 遭遇概率系统完善

- [ ] Y5.1 根据角色关系阶段调整遭遇概率
- [ ] Y5.2 根据地点类型调整遭遇概率（私室高，公共区域低）
- [ ] Y5.3 偷袭/潜伏模式下的遭遇处理

对应 eraTW: `遭遇判定.ERB` (382行)

## Y6. 来访者/跨区流动

- [ ] Y6.1 随机来访事件（不在当前位置的角色主动登门）
- [ ] Y6.2 来访触发对话/事件

当前 distribution.py 有基础分布，来访为 L8 设计方案。

## Y7. 低优先系统（β版可选）

- [ ] Y7.1 宴会系统
- [ ] Y7.2 潜伏/偷袭模式
- [ ] Y7.3 妊娠系统
- [ ] Y7.4 战斗系统

---

# 四、事件层

## E1. 事件条件表达式系统

- [ ] E1.1 条件类型扩展：TALENT 存在/值范围、ABL 等级、PALAM 等级、刻印等级、关系阶段
- [ ] E1.2 支持组合条件（AND/OR/NOT）
- [ ] E1.3 条件预编译（事件加载时解析为可执行对象，避免运行时 eval）

对应 eraTW: `EVENT` 函数开头的条件检查

## E2. 事件优先级与互斥

- [ ] E2.1 同一时机多事件触发时的优先级排序
- [ ] E2.2 互斥组定义（如 daily 事件一天只触发一个）

## E3. 事件连锁

- [ ] E3.1 事件触发后标记连锁事件（如"破处"后触发"初体验回忆"事件）
- [ ] E3.2 连锁事件不消耗额外时间 slot

## E4. Daily 随机事件

- [ ] E4.1 每日事件池（早上/中午/晚上各时段事件）
- [ ] E4.2 事件权重和稀有度
- [ ] E4.3 事件去重（同一天不重复触发同一事件）

当前 ambient_events.py 有基础 25% 触发，需要扩展。

## E5. 角色专属事件

- [ ] E5.1 每个角色可定义专属事件（通过 character/events.toml）
- [ ] E5.2 角色事件优先级高于全局事件

框架已有，需要配合事件条件系统完善。

---

# 五、口上层

## K1. 口上变体选择系统

- [ ] K1.1 口上选择优先级：事件专用 > 刻印等级 > PALAM 等级 > 关系阶段 > 动作默认
- [ ] K1.2 变体标记解析（`[反发3]`, `[欲情高]`, `[恋慕]` 等条件标签）
- [ ] K1.3 组合条件标记（`[反发3+欲情高]`）
- [ ] K1.4 同条件下多条台词随机池
- [ ] K1.5 同一场景已使用台词去重（短期记忆）

对应 eraTW: `KOJO_MESSAGE.ERB` + `COMMON_KOJO.ERB`

---

# 六、UI 层

## U1. Web UI 基础框架

当前有 `web_server.py` + `web_client.html` 存根。

- [ ] U1.1 确定技术栈（Web — 复用现有 Flask 存根 / 换 FastAPI / 用 Vue/React SPA）
- [ ] U1.2 游戏主循环：指令选择 → 结果展示 → 下一条指令
- [ ] U1.3 前后端数据协议（JSON API）

## U2. 角色状态面板

- [ ] U2.1 BASE 状态条（体力/气力/理性等，带颜色）
- [ ] U2.2 PALAM 状态条（欲情/恭顺/恐怖等）
- [ ] U2.3 刻印显示
- [ ] U2.4 ABL/TALENT 数值表
- [ ] U2.5 装备/服装状态

对应 eraTW: `PRINT_STATE.ERB`, `BAR.ERB`, `COLOR.ERB`

## U3. 指令选择界面

- [ ] U3.1 可用/不可用指令区分（灰色/红色标记）
- [ ] U3.2 不可用指令悬浮提示拒绝理由
- [ ] U3.3 指令分类 tab（日常/调教/道具/特殊）
- [ ] U3.4 指令快捷键

## U4. 对话/结果展示

- [ ] U4.1 口上/事件文本展示框（滚动历史）
- [ ] U4.2 数值变化提示（SOURCE +30, PALAM 欲情 ↑ 等）
- [ ] U4.3 角色立绘区域（至少静态图片）

## U5. HUD 系统

- [ ] U5.1 左上角时间/日期/时段显示
- [ ] U5.2 当前位置+天气显示
- [ ] U5.3 迷你地图（当前位置高亮）

## U6. 存档/设置

- [ ] U6.1 存档槽列表+截图
- [ ] U6.2 读档确认
- [ ] U6.3 游戏设置（音量、文字速度等）

---

# 七、基础层

## B1. 存档系统完善

- [ ] B1.1 多存档槽管理（当前仅 quicksave）
- [ ] B1.2 版本迁移框架（旧存档 → 新架构自动升级）
- [ ] B1.3 存档完整性校验

当前 save.py 311 行，框架可扩展。

## B2. 测试扩展

- [ ] B2.1 settlement 端到端测试（多相位组合验证）
- [ ] B2.2 指令拒绝逻辑测试
- [ ] B2.3 事件条件匹配测试
- [ ] B2.4 存档 round-trip 测试
- [ ] B2.5 刻印端到端测试（CUP → 刻印升级完整链路）
- [ ] B2.6 ABLUP 端到端测试（JUEL+EXP → 升级）

## B3. 性能优化

- [ ] B3.1 指令可用性缓存
- [ ] B3.2 事件/口上条件预编译
- [ ] B3.3 WorldState 快照优化（用于存档和事件回滚）

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

### 主线 E：L3 数值闭环与体力系统稳定化（当前）

> 目标：把已接入的体力/气力骨架、关系成长公式与新阈值体系跑成“可平衡、可回归、可继续扩内容”的稳定版本。

- [x] 完成体力/气力系统首轮平衡表（指令分档 + 恢复分档）
	- type: design
	- priority: P0
	- milestone: L3
	- est: 90m
	- DoD: 覆盖 daily/work/follow/date/recovery 五类动作，给出 downbase 分档与恢复目标区间；文档与 commands.toml 一致
	- verify: 对照 `docs/specs/体力与气力系统.md` + 抽样 20 条指令核对
	- owner: pair
	- status: done
	- updated: 2026-04-14

- [x] 修正恢复指令 key 冲突与命令清单一致性
	- type: code
	- priority: P0
	- milestone: L3
	- est: 45m
	- DoD: commands.toml 中不存在重复 key；恢复类指令命名和操作语义一致；旧 nap 改为 relax_together（一起放松），新增 recovery 类 nap（小憩）/sleep（就寝）/bathe（泡澡）
	- verify: `python -m eral.tools.validate_content --root .` + 全仓搜索确认无重复 key
	- owner: ai
	- status: done
	- updated: 2026-04-14

- [x] 为 VitalGate / 晕倒推进 / 恢复链路补充端到端回归
	- type: test
	- priority: P0
	- milestone: L3
	- est: 90m
	- DoD: 覆盖"气力归零禁用指令""体力归零晕倒并推进到次日 dawn""sleep/nap/bathe 恢复差异"三条主链；35 个 test_vitals 测试全通过
	- verify: `python -m unittest tests.test_vitals tests.test_commands tests.test_smoke_playable -v`
	- owner: ai
	- status: done
	- updated: 2026-04-14

- [ ] 修正恢复指令 key 冲突与命令清单一致性（nap 重名问题）
	- type: code
	- priority: P0
	- milestone: L3
	- est: 45m
	- DoD: commands.toml 中不存在重复 key；恢复类指令命名和操作语义一致
	- verify: `python -m eral.tools.validate_content --root .` + 全仓搜索 `key = "nap"`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [ ] 为 VitalGate / 晕倒推进 / 恢复链路补充端到端回归
	- type: test
	- priority: P0
	- milestone: L3
	- est: 90m
	- DoD: 覆盖“气力归零禁用指令”“体力归零晕倒并推进到次日 dawn”“sleep/nap/bathe 恢复差异”三条主链
	- verify: `python -m unittest tests.test_vitals tests.test_commands tests.test_smoke_playable -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14


- [ ] 关系成长公式与阶段门槛出一版可调参数说明
	- type: docs
	- priority: P1
	- milestone: L3
	- est: 60m
	- DoD: 明确 relationship_growth.toml 与 relationship_stages.toml 的调参规则、推荐区间、回归检查项
	- verify: 人工检查文档 + 对应测试可按参数变化快速调整
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [ ] L3 基础闸门：完成“连续 14 天可玩（基础版）”烟测
	- type: test
	- priority: P1
	- milestone: L3
	- est: 60m
	- DoD: 14 天循环覆盖移动-互动-结算-时间推进-恢复，流程无中断
	- verify: `python -m unittest tests.test_smoke_playable -v`
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [ ] L3 体验闸门：完成“连续 14 天可玩（全链路版）”烟测
	- type: test
	- priority: P1
	- milestone: L3
	- est: 90m
	- DoD: 14 天循环包含工作/同行/约会/恢复/晕倒恢复至少各 1 次，且关键状态迁移与事件触发无异常
	- verify: `python -m unittest tests.test_smoke_playable -v`
	- owner: pair
	- status: todo
	- updated: 2026-04-14

### L3 退出条件（阶段切换闸门）

- [ ] `commands.toml` 无重复 key，且字段通过校验
- [ ] Vital 主链回归通过（气力门控 / 体力晕倒推进 / sleep-nap-bathe 差异）
- [ ] 连续 14 天可玩（基础版）通过
- [ ] 连续 14 天可玩（全链路版）通过
- [ ] relationship_growth 与 relationship_stages 调参说明已落文档并通过人工核验

### 主线 F：L4 经济循环完整化（规划中）

> 目标：建立"资源产生→存储→消费→增益"的完整经济循环，统一工作、委托、港区开发三大系统，让玩家具备长期目标和可预期收益。

#### F1. 资金与账本系统（阶段 1）

- [x] 资金系统设计文档审核与字段对齐
	- type: docs
	- priority: P0
	- milestone: L4
	- est: 45m
	- DoD: [资金与账本系统](docs/specs/资金与账本系统.md) 已通过审核，WordState 扩展点已验证，与现有代码无冲突
	- verify: 文档交叉引用现有代码位置 + 全仓搜索 personal_funds / port_funds 确认无冲突
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [x] 扩展 WorldState + SaveService 支持双账户
	- type: code
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: CharacterState 无需改动；WorldState 新增 `personal_funds` 与 `port_funds`；SaveService._serialize_world 已扩展；LoadService._deserialize_world 已兼容旧存档（默认 0）；ExampleWorldMixin 初始值配置已落实
	- verify: `python -m unittest tests.test_save_load -v` + 存档序列化验证测试
	- owner: ai
	- est: 60m
	- status: todo
	- updated: 2026-04-14

- [x] 创建 WalletService 统一资金操作接口
	- type: code
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: WalletService 支持 add_personal_funds / add_port_funds / transfer_to_port，所有操作调用 LedgerService 记账，可查询余额；bootstrap 已集成；所有单元测试通过
	- verify: `python -m unittest tests.test_wallet_service -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [x] 创建 LedgerService 流水记录（第一版仅存余额，流水作为后续扩展）
	- type: code
	- priority: P1
	- milestone: L4
	- est: 30m
	- DoD: LedgerService 支持 record_transaction 写入账本，所有交易包含 day/time_slot/account/delta/reason/source_key
	- verify: `python -m unittest tests.test_ledger_service -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

#### F2. 工作系统（阶段 2）

- [x] 工作系统规范与指令集已规划
	- type: docs
	- priority: P0
	- milestone: L4
	- est: 30m
	- DoD: [工作系统](docs/specs/工作系统.md) 已细化，建议工作指令列表（office_shift / extra_shift）已定义，downbase 消耗与收益倍率已给出
	- verify: 文档审核 + 数值合理性抽查
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [x] 在 commands.toml 中加入工作类指令（category = "work"）
	- type: code
	- priority: P0
	- milestone: L4
	- est: 45m
	- DoD: office_shift / extra_shift 两条工作指令已加入，downbase、personal_income/port_income 已配置，指令可用性检查已应用
	- verify: `python -m eral.tools.validate_content --root .` + `python -m unittest tests.test_work_commands -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [x] 工作指令执行后资金记账流程集成
	- type: code
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: CommandService 执行后调用 WalletService 扣除/增加资金；ActionResult 包含资金变化提示文案；end-to-end 测试通过
	- verify: `python -m unittest tests.test_work_system_e2e -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

#### F3. 委托系统（阶段 3）

- [ ] 委托系统规范与配置已完成
	- type: docs/data
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: [委托系统](docs/specs/委托系统.md) 已细化；创建 data/base/commissions.toml，首批 3-5 个测试委托已定义（对应各种关系阶段与时长）
	- verify: `python -m eral.tools.validate_content --root .`
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [ ] 扩展 CharacterState.is_on_commission 与 SaveService 持久化
	- type: code
	- priority: P0
	- milestone: L4
	- est: 45m
	- DoD: CharacterState 新增 `is_on_commission` 布尔标志；在 ScheduleService 中检查该标志，派遣中的角色跳过日程刷新；SaveService 已扩展以支持序列化
	- verify: `python -m unittest tests.test_commission_state -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [ ] 创建 CommissionService 协调委托派遣 + 时段推进 + 奖励结算
	- type: code
	- priority: P0
	- milestone: L4
	- est: 90m
	- DoD: CommissionService 支持 dispatch / tick_slot / finalize，委托中角色不出现在活动场景，时段推进自动扣减 remaining_slots，归零时调用 WalletService 结算奖励，派遣中角色在场景中标记为"在委托"；GameLoopService 已集成 tick_slot 调用
	- verify: `python -m unittest tests.test_commission_service -v` + 场景可见性测试
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [ ] 委托派遣与结算 end-to-end 测试
	- type: test
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: 自动化测试覆盖派遣→推进→完成→收益记账全流程，且派遣中角色确不出现在当前场景
	- verify: `python -m unittest tests.test_commission_system_e2e -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

#### F4. 港区开发系统（阶段 4）

- [ ] 港区开发系统规范与首批设施配置
	- type: docs/data
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: [港区开发系统](docs/specs/港区开发系统.md) 已细化；创建 data/base/facilities.toml，首批 4 个设施已定义（官舎/食堂/约会点/医务室），各设施最大等级、升级费用、效果倍率已给出
	- verify: `python -m eral.tools.validate_content --root .`
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [ ] 扩展 WorldState.facility_levels + SaveService 持久化
	- type: code
	- priority: P0
	- milestone: L4
	- est: 45m
	- DoD: WorldState 新增 `facility_levels: dict[str, int]` 字典；SaveService 已扩展以支持序列化；LoadService 已兼容旧存档（默认所有设施 level 0）
	- verify: `python -m unittest tests.test_facility_state -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [ ] 创建 FacilityService 协调升级检查 + 扣费 + 效果广播
	- type: code
	- priority: P0
	- milestone: L4
	- est: 90m
	- DoD: FacilityService 支持 upgrade / get_recovery_multiplier / get_income_multiplier / get_relation_bonus；整合进 VitalService（恢复倍率）、CommissionService（工作收益）、SettlementService（关系增益）；bootstrap 已集成
	- verify: `python -m unittest tests.test_facility_service -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

- [ ] 港区开发 end-to-end 测试（升级→效果生效）
	- type: test
	- priority: P0
	- milestone: L4
	- est: 60m
	- DoD: 升级官舎后体力恢复倍率增加、升级食堂后工作收益倍率增加、升级约会点后关系增益增加，所有链路闭合测试通过
	- verify: `python -m unittest tests.test_facility_system_e2e -v`
	- owner: ai
	- status: todo
	- updated: 2026-04-14

#### F5. 系统集成与打磨（阶段 5）

- [ ] L4 经济循环 14 天可玩性烟测
	- type: test
	- priority: P0
	- milestone: L4
	- est: 90m
	- DoD: 自动化测试覆盖 14 天完整循环，包含工作→获得资金、派遣委托→自动收益、升级设施→效果生效、资金余额正确显示等全流程
	- verify: `python -m unittest tests.test_economy_system_e2e -v`
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [ ] 数值平衡与调参说明
	- type: docs
	- priority: P1
	- milestone: L4
	- est: 60m
	- DoD: 补充 data/base 下工作/委托/设施的数值平衡文档，给出调参目标（14 天内可完成第一个设施升级、工作与委托收益比例），确保后续平衡迭代有明确指引
	- verify: 人工核验数值是否符合游戏节奏预期
	- owner: pair
	- status: todo
	- updated: 2026-04-14

- [ ] UI 展示与交互起点
	- type: code
	- priority: P1
	- milestone: L4
	- est: 60m
	- DoD: CLI 主菜单已显示当前资金余额、港区设施状态；工作/委托派遣流程已有基础交互提示；后续 UI 升级可直接拓展
	- verify: 手工验证 CLI 输出信息完整度
	- owner: pair
	- status: todo
	- updated: 2026-04-14

### L4 退出条件（阶段切换闸门）

- [ ] 资金系统已稳定实现（WorldState + SaveService 验证）
- [ ] 工作系统已可玩（指令可用、消耗正确、收益入账）
- [ ] 委托系统已可玩（派遣、推进、收益结算无异常）
- [ ] 港区开发系统已可玩（升级、扣费、效果生效）
- [ ] 经济循环 14 天烟测通过
- [ ] 数值平衡文档已落实，至少 1 轮调参完成

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

- [x] 建立 ABL/TALENT/CFLAG 常用语义映射层
	- type: code
	- priority: P0
	- milestone: L2
	- est: 90m
	- DoD: 覆盖首批高频索引（>= 30 项）的英文 key + era 标签映射接口，领域/系统层关键调用点不再直接散落硬编码索引
	- verify: `python -m unittest tests.test_compat_semantics -v` + 替换 `world.py / companions.py / dates.py` 3 处以上业务调用
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 将指令可用性判定拆分为多层 Gate
	- type: code
	- priority: P0
	- milestone: L2
	- est: 90m
	- DoD: 可用性检查分离为分类门槛、全局模式门槛、指令专用门槛，失败原因保持可读，并保留原有对外行为顺序
	- verify: `python -m unittest tests.test_command_gates tests.test_commands -v`
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 增加约会后事件结算层（after_date_event）
	- type: code
	- priority: P1
	- milestone: L2
	- est: 90m
	- DoD: `end_date` 后可独立触发 `after_date_event` 后事件层，并与普通 `end_date` 事件分开结算
	- verify: `python -m unittest tests.test_after_date_events tests.test_dates tests.test_e2e_date_line -v`
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 建立内容密度自动统计报告
	- type: tooling
	- priority: P1
	- milestone: L2
	- est: 45m
	- DoD: `validate_content` 输出每角色事件/对话数量与缺口摘要，可直接用于周报
	- verify: `python -m eral.tools.validate_content --root .` 输出包含 `content density report:` 段
	- owner: ai
	- status: done
	- updated: 2026-04-12

## Backlog（按价值排序）

### P0（可靠性与一致性：测试、校验、文档口径、关键 BUG）

- [x] 移除全部 starter 占位角色，新增标枪正式角色包
	- type: code
	- priority: P0
	- milestone: L3
	- est: 60m
	- DoD: 无任何 starter_* 引用残留在代码/数据/测试中；3 个正式角色包（企业、拉菲、标枪）全部通过测试和内容校验
	- verify: `python -m unittest discover -s tests -t .` + `python -m eral.tools.validate_content --root .` + 全仓搜索 starter_*
	- owner: ai
	- status: done
	- updated: 2026-04-13

- [x] 修复 Windows / Python 3.14 下角色包拆分初值测试的临时目录权限问题
	- type: test
	- priority: P0
	- milestone: L2
	- est: 45m
	- DoD: `tests/test_character_pack_stat_files.py` 不再依赖 `tempfile.TemporaryDirectory(dir=.tmp-test-data)`，相关测试在当前环境可稳定通过
	- verify: python -m unittest tests.test_character_pack_stat_files -v
	- owner: ai
	- status: done
	- updated: 2026-04-12

- [x] 地点扩展到 8 到 12，并给每个地点补玩法标签
- [x] 约会四地点分支各至少 1 条（食堂/码头/宿舍/浴场）
- [x] 指令失败反馈标准化（地点/时段/关系/状态原因）
- [x] 清理测试文件 UTF-8 BOM 与行尾格式不一致问题（避免跨平台噪声 diff）
- [ ] 建立 `commands.toml` 重复 key 与非法字段 CI 检查

### P1（架构与工具能力：可观测性、自动化、内容管线）

- [x] 内容校验器增加"条目数量缺口"检查
- [x] 增加"多角色并行游玩"回归测试
- [x] 生活/工作 B 批 `relax_together / study / cook / eat_meal / invite_meal / nap` 已进入命令系统
- [x] `library / infirmary / garden` 已开始承载专属事件钩子与口上内容
- [x] 体力/气力系统已完整实现：VitalService、VitalGate、晕倒推进、疲劳、恢复指令、MAXBASE 上限
- [x] 修 ABL_INTIMACY_INDEX bug（12→9）+ 接入 ABL 升级管道到结算流程
		- type: code
		- priority: P1
		- milestone: L3
		- est: 60m
		- DoD: ABL_INTIMACY_INDEX=9 已修正；abl_upgrade.toml 全量定义完成；指令 source 含 abl_* 经验；SettlementService Phase 3.5 接入 ABL 升级（含持久 abl_exp 累加器）；255 测试全通过
		- verify: `python -m unittest tests.test_abl_upgrade -v`
		- owner: ai
		- status: done
		- updated: 2026-04-14
- [ ] 工作系统：舰娘行为状态（activity 字段）+ ActivityGate + help_work 要求舰娘在工作
- [ ] 将关系成长与体力恢复参数抽出“预设档位”（easy/normal/hard）
- [ ] 为内容密度报告增加“阶段覆盖率”指标（friendly/like/love/oath）

### P2（MVP 后或低优先级）

- [ ] 将指令迁移表改为体感收益优先队列（已完成命令迁移后转为平衡用途）
- [ ] 深层 H 相关系统（明确不进入当前迭代）
- [ ] UI 形态升级（CLI 以外）

## 当前事实（避免重复争论）

- [x] `create_application()` 已是装配入口。
- [x] `SOURCE -> settlement -> BASE/PALAM/CFLAG/TFLAG` 已跑通。
- [x] 角色包已支持 `BASE/PALAM/ABL/TALENT/CFLAG/MARK` 初始属性。
- [x] 角色初值已迁移到按数值族拆分的独立 TOML 文件（base.toml/palam.toml/abl.toml/talent.toml/cflag.toml/marks.toml）。
- [x] 企业、拉菲、标枪三个正式角色包已就位；starter 占位角色已全部移除。
- [x] 同行、约会、轻亲密起点与存档系统已存在。
- [x] runtime/logs 已有最小结构化日志链路。
- [x] `python -m unittest discover -s tests -t .` 已可作为统一回归入口。
- [x] 54 个指令已接入 commands.toml，迁移表中均已标记"完成"。
- [x] 企业和拉菲内容密度已达到当前主线目标（各 >= 20 事件、>= 30 对话）；标枪已达到（>= 20 事件、>= 30 对话）。
- [x] 端到端链路与 7 天烟测已通过（unittest 全量通过）。
- [x] compat 语义映射层、多层 Gate、after_date_event、内容密度统计报告已建立；starter 占位角色已完全移除，全部测试已迁移到正式角色包。
- [x] 体力/气力系统规格文档已建立并接入 specs 导航。
- [x] 命令层已支持 `downbase` 消耗与恢复类 operation（sleep/nap/bathe）管线。
- [x] `VitalService`、`VitalGate`、自然恢复与晕倒后推进到次日 dawn 已接入主流程。
- [x] 关系阶段阈值、`FAVOR_CALC/TRUST_CALC` 与测试辅助工厂已升级为可配置化。
- [x] 体力/气力完整链路已通过：DOWNBASE→疲劳计算、自然恢复/睡眠恢复/小憩/泡澡、气力归零禁用指令、体力归零晕倒推进到次日、MAXBASE 上限强制执行。
- [x] `fatigue` 字段已加入 CharacterState 并接入存档序列化。
- [x] 旧 `nap`（午睡）已改为 `relax_together`（一起放松），恢复类指令无 key 冲突。
- [x] 资金系统已实现：WorldState 双账户（personal_funds/port_funds），WalletService 统一操作接口，SaveService 旧存档兼容，ActionResult.funds_delta 记录资金变动。
- [x] 工作系统已实现：office_shift/extra_shift 工作指令，通过 personal_income 字段产出个人资金，CommandService 集成 WalletService 记账。
- [x] 经济分工已确认：工作指令 → 个人资金，委托系统 → 港区资金。
- [x] ABL 提升系统已完整接入：`abl_upgrade.toml` 全量定义、`content/abl_upgrade.py` 加载器、`systems/abl_upgrade.py` 升级逻辑（含持久 `abl_exp` 累加器）、SettlementService Phase 3.5、指令 `abl_*` 经验产出、存档序列化支持。`ABL_INTIMACY_INDEX=9` 已修正。

## 本周复盘区（每周五更新）

- 本周完成：L4 经济循环 F1-F2 完成（资金双账户 + WalletService + 工作指令 office_shift/extra_shift + 资金记账集成）；276 测试全通过
- 本周规划：L4 经济循环系统（资金→工作→委托→港区开发），分 5 阶段推进
- 本周阻塞：无
- 指标：
		- 新增指令数：2（office_shift / extra_shift）
		- 新增角色数：0
		- 移除角色数：0
		- 正式角色总数：3（企业、拉菲、标枪）
		- 自动化测试通过率：276/276（100%）
		- 手工可玩天数：7 天链路已被自动化烟测覆盖
- 下周主线：L4 第 3 阶段（委托系统实现）

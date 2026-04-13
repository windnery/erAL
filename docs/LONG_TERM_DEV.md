# erAL 长期开发规划

本文档为 erAL 项目提供从 MVP 到成熟产品的完整路线图。内容会根据开发进展持续更新。

---

## 1. 里程碑体系与当前坐标

### 1.1 里程碑层级

```
L0 架构基线 ────────────── 已完成 ✓
│  ├── Python 项目结构 (src/eral/ 六层架构)
│  ├── 数据加载管线 (TOML/JSON)
│  ├── 测试框架 (unittest)
│  └── 工具链 (validate/import)

L1 核心语义 ────────────── 已完成 ✓
│  ├── 54 条指令系统 (SOURCE -> settlement)
│  ├── 关系阶段与 MARK
│  ├── 同行/约会状态机
│  └── 事件匹配与对话选择

L2 语义层 ────────────── 已完成 ✓
│  ├── 角色包系统 (character/events/dialogue)
│  ├── 拆分数值初值 (BASE/PALAM/CFLAG/MARK)
│  ├── 多层 Gate (category/location/time/stage)
│  └── 回合推进与日程刷新

L3 MVP 打磨 ──────────── 进行中
│  ├── 誓约层内容 (指令+事件+对话)
│  ├── 通用口上兜底层
│  └── CLI 体感优化 (状态展示/日终反馈)

L4 内容规模化 ─────────── 规划中
│  ├── 角色量产 (6-12 新角色)
│  ├── 关系阶段深度扩展
│  ├── 地点玩法独立化
│  └── 地图区域化设计

L5 玩法系统扩展 ──────── 规划中
│  ├── 体力/精力消耗与恢复
│  ├── 天气/季节系统
│  ├── ABL 技能树
│  └── 深层亲密系统 (H)

L6 表现层 ────────────── 规划中
│  ├── UI 升级 (TUI/Web)
│  └── 音效/立绘系统
```

### 1.2 当前状态摘要

| 维度 | 状态 |
|------|------|
| 测试 | 199 通过 |
| 内容校验 | 通过 |
| 角色包 | 3 (企业/拉菲/标枪) |
| 指令数 | 54 |
| 地点数 | 10 |
| 关系阶段 | 5 (誓约层空) |
| 通用口上 | 仅 3 条 `_any` |

---

## 2. 地图与区域设计

### 2.1 当前问题

现有 10 个地点存在以下问题：

1. **数量不足** — MVP 要求 8-12，港区题材需要更多
2. **结构扁平** — 所有地点平铺，没有区域概念
3. **角色分布不均** — 800+ 角色集中在一起会导致某些地点过度拥挤
4. **缺乏功能分化** — 大多数地点只是背景，没有专属事件入口

### 2.2 区域化设计方案

> 以下只是初版地图，用于当前测试，最终版还需要大改

参考 eraTW 的地图组织方式，采用**区域 → 子区域 → 地点**三级结构：

```
港区 (Port)
│
├── 指挥区 (Command Area)
│   ├── 指挥室 (Command Office)
│   ├── 作战室 (Operations)
│   ├── 情报室 (Intelligence)
│   └── 会议室 (Conference Room)
│
├── 生活区 (Residential Area)
│   ├── 宿舍 A (Dormitory A) — 驱逐舰宿舍
│   ├── 宿舍 B (Dormitory B) — 巡洋舰宿舍
│   ├── 宿舍 C (Dormitory C) — 战列舰宿舍
│   └── 士官室 (Officer Quarters)
│
├── 训练区 (Training Area)
│   ├── 训练场 (Training Ground)
│   ├── 模拟室 (Simulation Room)
│   ├── 体能训练场 (Gym)
│   └── 靶场 (Firing Range)
│
├── 港区 (Harbor Area)
│   ├── 码头 (Dock)
│   ├── 船坞 (Shipyard)
│   ├── 栈桥 (Pier)
│   └── 海上演练区 (Sea Exercise)
│
├── 餐饮区 (Cafeteria Area)
│   ├── 食堂 (Cafeteria)
│   ├── 厨房 (Kitchen)
│   ├── 甜品店 (Dessert Shop)
│   └── 酒吧 (Bar)
│
├── 医疗区 (Medical Area)
│   ├── 医务室 (Infirmary)
│   └── 康复中心 (Recovery Center)
│
├── 娱乐区 (Entertainment Area)
│   ├── 花园 (Garden)
│   ├── 图书室 (Library)
│   ├── 娱乐室 (Lounge)
│   └── 电影院 (Theater)
│
├── 浴场 (Bathhouse Area)
│   ├── 大浴场 (Main Bath)
│   ├── 私汤 (Private Bath)
│   └── 甲板 (Deck)
│
├── 仓储区 (Storage Area)
│   ├── 仓库 (Warehouse)
│   └── 材料库 (Material Storage)
│
└── 特殊区 (Special Area)
    ├── 镇守府 (Admiral's Residence)
    ├── 祭拜所 (Shrine)
    └── 秘密基地 (Secret Base)
```

### 2.3 区域功能定位

| 区域 | 功能标签 | 典型事件 | 可解锁内容 |
|------|---------|----------|-----------|
| 指挥区 | work, official | 文书工作、情报汇报、新任务 | 官方剧情线 |
| 生活区 | rest, private, residential | 夜间拜访、照顾、休息 | 私密事件、床戏 |
| 训练区 | training, exercise | 共同训练、比试、受伤 | 技能成长、战斗事件 |
| 港区 | harbor, naval | 出海、钓鱼、演练 | 海上剧情、船只相关 |
| 餐饮区 | food, social | 一起吃饭、做饭、喝酒 | 饱食イベント、醉酒事件 |
| 医疗区 | medical, care | 受伤照顾、治疗、身体检查 | 身体接触、私密检查 |
| 娱乐区 | leisure, culture | 读书、赏花、游玩 | 文艺事件、知识提升 |
| 浴场 | bath, private | 沐浴相遇、帮忙搓背 | 浴室事件、湿地相逢 |
| 仓储区 | storage | 帮助整理、发现旧物 | 回忆事件、礼物 |
| 特殊区 | story, hidden | 节日活动、隐藏剧情 | 誓约仪式、TEBE |

### 2.4 地点扩展优先级

| 阶段 | 新增地点 | 理由 |
|------|---------|------|
| L3 末尾 | 花园扩展、图书室 | 已有事件但地点不足 |
| L4 前期 | 宿舍 A/B/C 三分区、训练场扩展 | 按阵营分化角色 |
| L4 中期 | 酒吧、甜品店、商店 | 约会场景丰富化 |
| L4 后期 | 医务室、船坞、模拟室 | 功能性地点 |
| L5 | 天气相关地点、祭拜所 | 系统联动 |

---

## 3. 角色与区域部署

### 3.1 角色分阵营部署策略

碧蓝航线 800+ 角色按阵营分配到不同区域，每个区域 30-50 名角色，形成自然的"找人"节奏：

```
阵营                 区域             初始角色数
───────────────────────────────────────────
皇家海军 (Royal Navy)    生活区+训练区       15-20
皇家空军 (Royal Navy CV)   港区+航空队      5-10
 Eagle Union       指挥区+港区       15-20
 Eagle Union CV   港区+航空队       5-10
重樱 (Sakura)      浴场+生活区       15-20
重樱 (Sakura) CV  港区+航空队       5-10
铁血 (Iron Blood)  训练区+仓储区     10-15
鸢尾 (Iris)       娱乐区+特殊区     8-12
自由鸢尾 (Iris Libre) 特殊区           5-8
北方联合 (Northern)  港区+食堂         5-8
皇家方舟系列       娱乐区+特殊区     5-8
其他阵营         视进度加入       —
```

### 3.2 角色优先级队列

新增角色的优先顺序：

| 优先级 | 角色阵营 | 理由 |
|--------|---------|------|
| P0 | 贝尔法斯特 | 皇家海军核心，人气高 |
| P0 | 俾斯麦 | 铁血代表 |
| P0 | 光辉 | 皇家空军代表 |
| P1 | 皇家方舟 | 剧情推进器，隐藏属性 |
| P1 | 赤城 | 重樱核心 |
| P1 | 独角兽 | 人气角色，功能性强 |
| P2 | 明石 | 工程船，功能性 |
| P2 | 圣地亚哥 | 快乐源 |
| P2 | 扎拉 | 铁血剧情线 |
| P3 | 其他阵营代表 | 扩展用 |

### 3.3 每个角色的内容密度要求

| 阶段 | 事件数 | 对话数 | 阶段差分 |
|------|-------|-------|---------|
| MVP 级 | ≥20 | ≥30 | ≥3 (friendly/like/love) |
| 完整线 | ≥30 | ≥50 | ≥5 (含誓约) |
| 高密度 | ≥40 | ≥80 | ≥8 (多 MARK 变体) |
| 角色模板 | ≥50 | ≥100 | 完整全阶段 |

---

## 4. 数值设计框架

> 本章节为占位符，待用户从 eraTW 拆解数值矩阵后填充。

### 4.1 SOURCE 产出标定（待填充）

| 指令类型 | affection | trust | joy | ... |
|---------|----------|-------|-----|-----|
| 日常闲聊 | 0-1 | 0-1 | 0-1 | ... |
| 专属互动 | 1-2 | 1-2 | 1 | ... |
| 约会 | 2-3 | 1-2 | 2-3 | ... |
| 亲密 | 2-4 | 1-2 | 1-2 | ... |

### 4.2 关系阶段门槛（当前设计，待调整）

```
stranger → friendly: affection≥1
friendly → like:    affection≥3, trust≥2
like → love:       affection≥6, trust≥4
love → oath:       affection≥10, trust≥6
```

### 4.3 体力/精力消耗（待实现）

### 4.4 角色性格修正倍率（待设计）

### 4.5 PALAM 时段衰减（待实现）

### 4.6 ABL 技能树（待实现）

---

## 5. 开发任务队列

### 5.1 L3 MVP 打磨（当前）

| 任务 | 类型 | 预估 | 依赖 | 状态 |
|------|------|------|------|------|
| SOURCE 产出重新标定 | 数值 | L3完成前 | 待办 |
| 誓约层指令 | 内容 + 代码 | 数值标定 | 待办 |
| 誓约层事件 | 内容 | 指令定义 | 待办 |
| 誓约层对话 | 内容 | 事件定义 | 待办 |
| 通用口上兜底 | 内容 | 54指令 | 待办 |
| CLI 状态面板升级 | 代码 | 无 | 待办 |
| 日终反馈摘要 | 代码 | 无 | 待办 |

### 5.2 L4 内容规模化

| 任务 | 类型 | 预估 | 依赖 | 状态 |
|------|------|------|------|------|
| 贝尔法斯特角色包 | 内容 | L3完成 | 待办 |
| 光辉角色包 | 内容 | L3完成 | 待办 |
| 俾斯麦角色包 | 内容 | L3完成 | 待办 |
| 皇家方舟角色包 | 内容 | L4前期 | 待办 |
| 独角兽角色包 | 内容 | L4中期 | 待办 |
| 地图区域化重构 | 架构 + 内容 | 无 | 待办 |
| 地点扩展 (15→30) | 内容 | 区域化 | 待办 |

### 5.3 L5 玩法系统扩展

| 任务 | 类型 | 预估 | 依赖 | 状态 |
|------|------|------|------|------|
| 体力/精力消耗系统 | 代码 | L3完成 | 待办 |
| 天气系统 (TFLAG) | 代码 | 无 | 待办 |
| ABL 技能树 | 代码 | 体力系统 | 待办 |
| PALAM 衰减 | 代码 | 体力系统 | 待办 |
| 深层亲密系统 | 内容 + 代码 | L4完成 | 待办 |

### 5.4 L6 表现层

| 任务 | 类型 | 预估 | 依赖 | 状态 |
|------|------|------|------|
| TUI 升级 | 代码 | L4完成 | 待办 |
| 音效系统 | 资产 | 无 | 待办 |
| 立绘系统 | 代码 + 资产 | L5中期 | 待办 |

---

## 6. 技术债务与架构预留

### 6.1 需要关注的技术债务

| 事项 | 当前状态 | 建议处理时机 |
|------|---------|-------------|
| `commands.toml` 规模 | 54 条已达 500 行 | L4 前期拆分为 `commands/` 目录 |
| 角色包加载性能 | 加载较慢 | L4 前期优化缓存 |
| 对话匹配算法 | O(n) 线性遍历 | L5 前考虑索引优化 |
| 日期推进效率 | 每次刷新全部角色 | L4 前期按需刷新 |

### 6.2 架构预留

未来需要但当前不实现的预留接口：

```python
# 6.2.1 技能系统预留
class AblSystem:
    """ABL axis with skill tree."""
    def get_skill_modifier(self, actor, skill_key) -> float: ...
    def apply_skill_effect(self, world, actor, command) -> dict: ...

# 6.2.2 天气系统预留
class WeatherSystem:
    """Global TFLAG weather with area modifiers."""
    def get_weather(self, world) -> str: ...
    def get_location_modifier(self, location, weather) -> float: ...

# 6.2.3 记忆系统预留
class MemorySystem:
    """Cross-event tracking for relationship history."""
    def record_event(self, actor, event_key): ...
    def check_unlocks(self, actor, event_key) -> list[str]: ...

# 6.2.4 A/B 测试预留
class FeatureFlags:
    """Feature flagging for A/B testing."""
    def is_enabled(self, flag_key) -> bool: ...
```

---

## 7. 术语对照表

| 术语 | 全称 | 说明 |
|------|------|------|
| SOURCE | 行动产出值 | 指令执行后产生的临时数值 |
| settlement | 统一结算 | SOURCE → 目标数值轴的转换过程 |
| BASE | 基础数值 |体力、精力、心情等基础状态 |
| PALAM | 欲望数值 | 好欲、服从等情感数值 |
| CFLAG | 角色标志 | 好感、信赖等角色专用标志 |
| TFLAG | 临时标志 | 天气、状态等世界级临时标记 |
| MARK | 烙印 | 角色身上的持久标记状态 |
| ABL | 能力值 | 技能等级等能力数值 |
| TALENT | 才能 | 隐藏能力数值 |
| Gate | 门控 | 指令执行的前提条件检查 |

---

## 8. eraTW 参考资料索引

以下资料从 eraTW 源码拆解而来，用于指导 erAL 数值层与系统层迁移。

| 文件 | 内容 | 用途 |
|------|------|------|
| `tw-numeric-layer-matrix.md` | 数值层总纲：变量轴、结算链、阈值、成长、关系增幅 | 迁移任何数值系统前先读此文档 |
| `tw-system-mapping.md` | eraTW→erAL 总体映射规则 | 决定"保留语义还是改实现" |
| `tw-callchain-rule-matrix.md` | 主流程调用链（开场、收尾、约会通用） | 迁移系统顺序 |
| `tw-comable-rule-matrix.md` | 指令可用性判定体系 | 做 command gate 规则 |
| `tw-command-numeric-catalog.md` | COMF 指令数值语句索引 | 查某条指令改了哪些 SOURCE/DOWNBASE |
| `tw-command-cost-summary.md` | 指令体力/气力消耗区间汇总 | 快速定消耗平衡 |
| `tw-scom-numeric-catalog.md` | SCOM 组合指令数值索引 | 查连携指令的具体数值 |
| `tw-command-migration-template.csv` | 指令迁移填写模板 | 把文档规则落到可执行配置 |
| `tw-state-index-tables.md` | CFLAG/TFLAG/FLAG 编号词典 | 查编号语义 |
| `tw-talent-index-table.md` | Talent 全量编号与原始说明 | 查每个 TALENT 的定义 |
| `tw-talent-effect-catalog.md` | TALENT 数值效果索引 | 看天赋在哪些公式生效 |
| `tw-kojo-migration-strategy.md` | 口上迁移策略 | 先做通用文本还是专属文本 |
| `tw-train-full-group-table.md` | Train 全量分组表 | 按指令区间分批迁移 |
| `character-pack-format.md` | 角色包数据格式定义 | 新增角色时先看此文档 |

## 9. 项目文档

- `PRD.md` — MVP 产品定义
- `TODO.md` — 短期任务追踪
- `COMMAND_MIGRATION.md` — 指令迁移进度
- `LONG_TERM_DEV.md` — 本文档：长期路线图
- `docs/archive/adoption-backlog.md` — 系统采用追踪
- `docs/specs/` — 各子系统规格文档

---

*本文档随项目开发持续更新。最后更新：2026-04-13*
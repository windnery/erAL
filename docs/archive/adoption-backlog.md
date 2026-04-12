# 借鉴采用清单

## 1. 文档目的

这份文档用于追踪：

- 哪些 `eraTW` / `erArk` 思路已经落地
- 哪些正在迁移
- 哪些计划迁移
- 哪些明确不采用

后续开发时，先更新这份文档，再继续大规模实现。

## 2. 已完成

### 架构与目录

- 已采用 `app / engine / domain / systems / content / ui / tools` 分层
- 已清理旧空骨架目录
- 已建立 `data/base / data/generated / mods / assets / runtime / tests`

### TW 数值语义

- 已迁移 `BASE / PALAM / SOURCE` 命名轴
- 已导入 `ABL / TALENT / FLAG / CFLAG / TFLAG` 完整兼容轴
- 已保留 `era_index`，便于后续继续抄 `eraTW`

对应文件：

- [`stat_axes.toml`](D:\project\myERA\erAL\data\base\stat_axes.toml)
- [`tw_axis_registry.json`](D:\project\myERA\erAL\data\generated\tw_axis_registry.json)

### TW 数值流

- 已建立 `SOURCE -> settlement -> BASE/PALAM/CFLAG/TFLAG`
- 已把规则外置到 TOML

对应文件：

- [`settlement_rules.toml`](D:\project\myERA\erAL\data\base\settlement_rules.toml)
- [`settlement.py`](D:\project\myERA\erAL\src\eral\systems\settlement.py)

### TW 地点核心变量思路

- 已建立可扩展小地图 schema
- 已建立相邻移动限制
- 已建立时段驱动的角色驻留刷新

对应文件：

- [`port_map.toml`](D:\project\myERA\erAL\data\base\port_map.toml)
- [`navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py)
- [`schedule.py`](D:\project\myERA\erAL\src\eral\systems\schedule.py)

### TW 事件与文本链

- 已建立场景上下文
- 已建立事件触发匹配
- 已建立按事件优先、按指令兜底的文本选择

对应文件：

- [`events.toml`](D:\project\myERA\erAL\data\base\events.toml)
- [`dialogue.toml`](D:\project\myERA\erAL\data\base\dialogue.toml)
- [`scene.py`](D:\project\myERA\erAL\src\eral\systems\scene.py)
- [`events.py`](D:\project\myERA\erAL\src\eral\systems\events.py)
- [`dialogue.py`](D:\project\myERA\erAL\src\eral\systems\dialogue.py)

### 关系阶段系统

- 已建立配置驱动的关系阶段阈值
- 已把关系阶段接入结算、场景上下文、指令前提和事件前提

对应文件：

- [`relationship_stages.toml`](D:\project\myERA\erAL\data\base\relationship_stages.toml)
- [`relationships.py`](D:\project\myERA\erAL\src\eral\systems\relationships.py)
- [`relationship.py`](D:\project\myERA\erAL\src\eral\domain\relationship.py)

### 同行与同室系统

- 已建立同行开始/解除
- 已建立同行状态下的跟随移动
- 已建立同行状态下跳过普通日程覆盖
- 已同步 `同室 / 同行 / 同行準備` 的兼容状态

对应文件：

- [`companions.py`](D:\project\myERA\erAL\src\eral\systems\companions.py)
- [`commands.toml`](D:\project\myERA\erAL\data\base\commands.toml)
- [`navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py)
- [`schedule.py`](D:\project\myERA\erAL\src\eral\systems\schedule.py)

### 邀约与约会系统

- 已建立邀约开始/结束的基础流程
- 已建立约会状态与同行状态的联动
- 已建立约会前后状态切换型事件匹配

对应文件：

- [`dates.py`](D:\project\myERA\erAL\src\eral\systems\dates.py)
- [`commands.toml`](D:\project\myERA\erAL\data\base\commands.toml)
- [`events.toml`](D:\project\myERA\erAL\data\base\characters\starter_secretary\events.toml)
- [`dialogue.toml`](D:\project\myERA\erAL\data\base\characters\starter_secretary\dialogue.toml)

### Ark 工程模式

- 已采用内容外置
- 已采用工具链独立
- 已采用分层运行时装配
- 已采用测试驱动迭代

### 阶段推进

- 阶段 1 的最小可玩循环已经基本闭合
- 已开始进入阶段 2 的角色内容管线
- 角色定义、事件、文本已支持从角色包目录扫描
- 已有角色包格式文档
- 已有内容校验器

对应文件：

- [`data/base/characters`](D:\project\myERA\erAL\data\base\characters)
- [`character_packs.py`](D:\project\myERA\erAL\src\eral\content\character_packs.py)
- [`character-pack-format.md`](D:\project\myERA\erAL\docs\reference\character-pack-format.md)
- [`validate_content.py`](D:\project\myERA\erAL\src\eral\tools\validate_content.py)

### 交互式 CLI

- 已替换 CLI stub 为完整交互式游戏循环
- 支持：查看状态、执行指令、移动、等待推进时段、退出
- 所有 display_name 已中文化（地点、指令、关系阶段、角色）
- 对话文本已全部替换为中文原创内容

对应文件：

- [`cli.py`](D:\project\myERA\erAL\src\eral\ui\cli.py)

### 代码卫生修复

- 删除了未使用的 `ContentRegistry` 空壳
- bootstrap 现在加载全局 `events.toml` 和 `dialogue.toml` 并合并到角色包内容
- `relationship_stages` 加载器增加了升序排列校验
- `affection/trust` 收敛为 `sync_derived_fields()` 从 CFLAG 单向同步

### 地点遭遇系统

- 移动到新地点时产生遭遇消息
- 遭遇状态通过 `encounter_location_key` 追踪，避免重复遭遇
- 日程刷新时角色换地点会清除遭遇状态（下次见面重新触发遭遇）
- 遭遇事件通过 EventBus 发布 `encounter` 主题
- 时段推进后检查并展示新遭遇

对应文件：

- [`navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py)
- [`schedule.py`](D:\project\myERA\erAL\src\eral\systems\schedule.py)
- [`world.py`](D:\project\myERA\erAL\src\eral\domain\world.py)

## 3. 进行中

### 角色状态显式化

当前状态：

- 已完成 `affection / trust / obedience` 从 CFLAG 兼容块抽取为显式字段
- 已建立 `sync_derived_fields()` 单向同步机制
- 已在各系统层（commands / events / dialogue / scene / ui）统一使用显式字段
- 已在 CLI 显示中增加 `服从` 字段

对应文件：

- [`world.py`](D:\project\myERA\erAL\src\eral\domain\world.py) — `CharacterState.obedience` 及 `sync_derived_fields()`
- [`scene.py`](D:\project\myERA\erAL\src\eral\domain\scene.py) — `SceneContext.obedience`
- [`commands.py`](D:\project\myERA\erAL\src\eral\content\commands.py) — `min_obedience`
- [`events.py`](D:\project\myERA\erAL\src\eral\content\events.py) — `min_obedience`
- [`dialogue.py`](D:\project\myERA\erAL\src\eral\content\dialogue.py) — `min_obedience`

### 角色包 stats/relationship 扩展

当前状态：

- 已支持 `character.toml` 中的 `[initial_stats]` 段
- 已支持 `base` 和 `cflag` 初始值覆盖
- 已在 bootstrap 中应用初始值后调用 `sync_derived_fields()`
- 关系阶段可从初始 CFLAG 值正确推导

对应文件：

- [`characters.py`](D:\project\myERA\erAL\src\eral\content\characters.py) — `InitialStatOverrides` / `_parse_initial_stats()`
- [`character_packs.py`](D:\project\myERA\erAL\src\eral\content\character_packs.py) — 包目录加载器已接入
- [`bootstrap.py`](D:\project\myERA\erAL\src\eral\app\bootstrap.py) — `_apply_initial_stats()` / `sync_derived_fields()`

### 私密场所可见性

当前状态：

- 已在 `PortMapLocation` 增加 `visibility` 字段（`public` / `private` / `hidden`）
- 已在 `port_map.toml` 中为宿舍和浴场设置 `visibility = "private"`
- 已在 `PortMap` 增加 `visible_neighbors()` 方法按可见性过滤
- 已在 `NavigationService` 增加 `can_see_private()` / `visible_destinations()`
- 同行或约会状态下可看到私密场所
- CLI 菜单已接入可见性过滤

对应文件：

- [`map.py`](D:\project\myERA\erAL\src\eral\domain\map.py) — `PortMapLocation.visibility` / `PortMap.visible_neighbors()`
- [`port_map.py`](D:\project\myERA\erAL\src\eral\content\port_map.py) — 加载 `visibility` 字段
- [`navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py) — `can_see_private()` / `visible_destinations()`
- [`cli.py`](D:\project\myERA\erAL\src\eral\ui\cli.py) — 菜单使用 `visible_destinations()`

### 小地图垂直切片

当前状态：

- 地图、移动、时段驻留刷新已建立
- 已做地点遭遇规则，移动和时段推进时产生遭遇
- 遭遇状态追踪避免重复遭遇
- 已实现私密场所可见性规则
- 同行/约会状态下可进入私密场所

目标：

- 让地点更深度参与事件和指令可用性

### 指令基础循环

当前状态：

- 已可执行基础指令并统一结算
- 已有基础前提系统
- 已有事件和文本结果

目标：

- 增加更细的场景前提
- 增加更多派生事件
- 把结果上下文开放给后续口上系统

## 4. 下一阶段优先项

### 第一优先级

1. 场景上下文扩展
2. 关系阶段与更多前提条件联动
3. 约会中的特殊分支和地点玩法
4. 地点更深度参与事件和指令可用性

### 第二优先级

1. `MARK` 系统（已完成）
2. 关系阶段系统（已完成）
3. 文本选择器的条件化（已完成）
4. 角色包中的 `stats/relationship` 扩展（已完成）

### 第三优先级

1. 角色包结构细化
2. 编辑器数据协议
3. 模组覆盖规则

## 5. 明确暂缓

这些内容先不做：

1. 全量港区大地图
2. 800+ 角色的全量静态接入
3. 大规模口上文本系统
4. 复杂 H 流程
5. 深层 AI 日程模拟

原因：

- 这些都依赖前面的基础循环稳定。

## 6. 明确不采用

### 不采用的 TW 实现习惯

- 匿名数组到处直读直写
- 依靠命名习惯和隐式入口维持系统
- 文本和规则强耦合

### 不采用的 Ark 风险点

- `domain` 与 `systems` 双核心混写
- `engine/core` 无限膨胀
- UI 反向污染规则层

## 7. 更新规则

后续每完成一个系统，都要在这份文档里更新：

1. 来源是 `eraTW`、`erArk` 还是 `erAL` 自主设计
2. 是“直接借鉴”“保留语义改实现”还是“只参考思路”
3. 当前实现落在哪些文件

这样后面做大规模内容和系统扩展时，不会丢掉设计依据。

## 8. 阶段判断

当前可以认为阶段 2 的基础目标已经完成：

1. 角色包目录已建立
2. 角色定义已拆包
3. 事件定义已拆包
4. 文本定义已拆包
5. 已有加载器
6. 已有校验器
7. 已有格式文档

后续开发可以从“继续搭管线”切换到“沿管线扩角色、扩事件、扩文本”。

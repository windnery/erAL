# eraTW 借鉴映射

## 1. 文档目的

这份文档只做一件事：

- 固定 `erAL` 对 `eraTW` 玩法语义的借鉴方式。

它不是 `eraTW` 全量说明书，也不是攻略文档。

它服务于后续开发，回答四个问题：

1. `eraTW` 的哪些概念直接保留。
2. 哪些概念保留语义但改实现。
3. 哪些概念当前暂不迁移。
4. 这些概念在 `erAL` 里落到哪里。

## 2. 总体原则

`erAL` 对 `eraTW` 的借鉴原则是：

- 尽量直接保留玩法语义。
- 尽量不保留裸数组和脚本式隐式耦合。
- 数值轴、状态轴、事件轴优先借鉴。
- 文本组织方式和角色内容拆包方式优先借鉴。
- 具体剧情、平衡数值、东方题材特化机制不直接搬。

一句话概括：

> 先抄语义，再做结构化；先抄成熟机制，再按碧蓝航线港区题材改造。

## 3. 目录层面的借鉴

从本地 `eraTW` 可以明确借鉴的组织方式：

- `CSV/`
  负责全局数值轴、枚举轴、指令轴、角色基础表。
- `CSV/Chara/`
  负责角色分文件内容组织。
- `ERB/MOVEMENTS`
  负责移动、位置、作息、日常调度。
- `ERB/ステータス計算関連`
  负责状态计算和自然变化。
- `ERB/コマンド関連`
  负责指令入口和执行逻辑。
- `ERB/イベント関連`
  负责事件触发和事件流程。
- `ERB/口上・メッセージ関連`
  负责文本、口上、个人内容扩展。

`erAL` 对应落点：

- `data/base/`
  承接原始静态数据和规则数据。
- `data/generated/`
  承接从 `eraTW` 导入或编译生成的数据。
- `src/eral/systems/`
  承接移动、指令、结算、事件等系统。
- `src/eral/content/`
  承接角色内容、地图内容、规则内容的加载器。
- `mods/`
  承接未来角色包和模组包。

## 4. 数值轴映射

### 4.1 当前已迁移

当前已经落地的 `eraTW` 数值轴：

- `BASE`
- `PALAM`
- `SOURCE`
- `ABL`
- `TALENT`
- `FLAG`
- `CFLAG`
- `TFLAG`

当前仓库中的对应文件：

- [`data/base/stat_axes.toml`](D:\project\myERA\erAL\data\base\stat_axes.toml)
  放 `BASE / PALAM / SOURCE` 的结构化命名轴。
- [`data/generated/tw_axis_registry.json`](D:\project\myERA\erAL\data\generated\tw_axis_registry.json)
  放从 `eraTW` CSV 直接生成的完整轴表。
- [`src/eral/content/stat_axes.py`](D:\project\myERA\erAL\src\eral\content\stat_axes.py)
  放命名轴加载器。
- [`src/eral/content/tw_axis_registry.py`](D:\project\myERA\erAL\src\eral\content\tw_axis_registry.py)
  放完整兼容轴加载器。
- [`src/eral/domain/stats.py`](D:\project\myERA\erAL\src\eral\domain\stats.py)
  放运行时数值模型。

### 4.2 迁移策略

#### `BASE`

保留用途：

- 基础状态
- 生理状态
- 情绪状态
- 身体尺寸
- 余韵类状态

实现策略：

- 改成具名键值块。
- 保留 `era_index` 便于回查和后续批量迁移。

#### `PALAM`

保留用途：

- 累积成长
- 心理变化
- 关系变化
- 负面反应

实现策略：

- 保持“累积值”定位。
- 不直接等同于最终阶段状态。
- 后续由事件和阶段系统消费。

#### `SOURCE`

保留用途：

- 单次行动产生的增量。

实现策略：

- 明确保留为“行动结果中间层”。
- 不允许指令直接绕过 `SOURCE` 修改大部分结果值。

这是 `erAL` 目前最重要的 `eraTW` 借鉴之一。

#### `ABL`

保留用途：

- 感觉
- 基础能力
- 中毒
- 技能
- 性技

实现策略：

- 当前先保留完整 `era_index` 兼容层。
- 后续再决定哪些转为具名模型、哪些继续走兼容块。

#### `TALENT`

保留用途：

- 性格
- 体质
- 性倾向
- 调教反应差异
- 条件修正因子

实现策略：

- 当前先保留完整原始索引。
- 后续分层拆成：
  - 可枚举标签
  - 可取值特质
  - 位运算型特质

#### `FLAG / CFLAG / TFLAG`

保留用途：

- `FLAG`：全局持久状态
- `CFLAG`：角色持久状态
- `TFLAG`：流程临时状态

实现策略：

- 当前先保留完整索引兼容。
- 后续只把高频、高重要度字段抽成显式字段。
- 其余保留兼容块，避免前期迁移成本过大。

## 5. 当前已经采用的 TW 规则

### 5.1 指令先产出 `SOURCE`

已实现：

- 指令定义写在 [`data/base/commands.toml`](D:\project\myERA\erAL\data\base\commands.toml)
- 指令执行在 [`src/eral/systems/commands.py`](D:\project\myERA\erAL\src\eral\systems\commands.py)

当前策略：

- 指令先写入 `SOURCE`
- 再统一走结算服务

这是对 `eraTW` “行动先产生产出，再统一结算”思路的直接借鉴。

### 5.2 统一结算管线

已实现：

- 结算规则在 [`data/base/settlement_rules.toml`](D:\project\myERA\erAL\data\base\settlement_rules.toml)
- 结算服务在 [`src/eral/systems/settlement.py`](D:\project\myERA\erAL\src\eral\systems\settlement.py)

当前结算方向：

- `SOURCE -> PALAM`
- `SOURCE -> BASE`
- `SOURCE -> CFLAG`
- `SOURCE -> TFLAG`

这一步是对 `eraTW` 数值流的核心借鉴。

### 5.3 地点与移动

已实现：

- 小地图定义在 [`data/base/port_map.toml`](D:\project\myERA\erAL\data\base\port_map.toml)
- 地图模型在 [`src/eral/domain/map.py`](D:\project\myERA\erAL\src\eral\domain\map.py)
- 移动服务在 [`src/eral/systems/navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py)

借鉴来源：

- `eraTW` 对位置、移动、角色所在场所的重视。

适配变化：

- 不直接按 `eraTW` 的东方地图照搬。
- 只保留“地点是玩法核心变量”这一思想。

### 5.4 同行、同室与位置状态

从本地 `eraTW` 已确认可直接借鉴的状态语义：

- `CFLAG:現在位置`
- `CFLAG:前ターン位置`
- `CFLAG:同室`
- `CFLAG:同行`
- `CFLAG:同行準備`
- `CFLAG:遭遇位置`

当前 `erAL` 的采用方式是：

- 用显式字段保存位置与同行状态。
- 用兼容块同步 `同室 / 同行 / 同行準備` 语义。
- 让“同行中角色不会被普通日程刷新拉走”。
- 让“玩家移动时同行角色跟随移动”。

当前落点：

- [`companions.py`](D:\project\myERA\erAL\src\eral\systems\companions.py)
- [`world.py`](D:\project\myERA\erAL\src\eral\domain\world.py)
- [`navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py)
- [`schedule.py`](D:\project\myERA\erAL\src\eral\systems\schedule.py)

这里是明确参考 `eraTW` 的成熟做法，而不是自行发明的新语义。

### 5.5 邀约与约会状态

从本地 `eraTW` 已确认可直接借鉴的语义：

- `CFLAG:约会中`
- 玩家与特定角色的外出会转化为约会状态
- 约会中的角色继续跟随玩家移动
- 约会状态会影响事件前提和文本分支

当前 `erAL` 的采用方式是：

- 约会建立在“同行”之上，而不是独立漂浮状态。
- 使用显式字段保存 `is_on_date` 和 `date_partner_key`。
- 同步 `CFLAG:约会中` 兼容语义。
- 事件匹配优先使用“状态切换前场景”，以兼容“开始约会/结束约会”这类过渡事件。

当前落点：

- [`dates.py`](D:\project\myERA\erAL\src\eral\systems\dates.py)
- [`commands.py`](D:\project\myERA\erAL\src\eral\systems\commands.py)
- [`world.py`](D:\project\myERA\erAL\src\eral\domain\world.py)
- [`events.py`](D:\project\myERA\erAL\src\eral\systems\events.py)

## 6. 当前不直接照搬的 TW 内容

这些内容现在不直接抄：

- 东方题材专属地图和事件。
- 原作角色关系结构。
- 过度依赖脚本全局变量的调用方式。
- 大量历史 patch 兼容层。
- 原有文本组织中的题材命名与剧情依赖。

原因很简单：

- 这些内容服务于 `eraTW` 自己，不服务于 `erAL`。

## 7. 未来优先借鉴项

下一阶段优先从 `eraTW` 借鉴的内容：

1. `MARK`
   作为阶段性烙印/状态系统参考。
2. 指令前提判定体系
   特别是与 `TFLAG / CFLAG / 才能 / 场景` 的联动。
3. 日程与位置刷新
   参考 `MOVEMENTS` 的职责拆分。
4. 角色个人内容拆包
   参考 `CSV/Chara` 和个人口上目录组织方式。
5. 事件触发与文本选择链
   参考 `事件相关 + 口上相关` 的稳定入口思路。

## 8. 明确不采用的实现习惯

这些是明确不采用的：

1. 大量匿名数组直接到处读写。
2. 大量通过脚本命名约定进行隐式跨文件调用。
3. 文本和规则逻辑强耦合地写在一起。
4. 通过“记住某个 index 的意义”维持系统可读性。

`erAL` 的目标是：

- 保留 `eraTW` 的成熟玩法语义。
- 不继承它的可维护性问题。

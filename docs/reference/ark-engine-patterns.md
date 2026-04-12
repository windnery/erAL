# erArk 工程借鉴

## 1. 文档目的

这份文档固定 `erAL` 对 `erArk` 的工程借鉴方式。

它不讨论题材，也不讨论玩法平衡，只讨论工程组织。

主要回答：

1. `erArk` 哪些分层值得直接学。
2. 哪些模式要照搬。
3. 哪些模式要谨慎使用。
4. 它们在 `erAL` 里的对应落点是什么。

参考仓库：

- `https://github.com/Godofcong-1/erArk`

## 2. 主要借鉴对象

`erArk` 最值得借鉴的不是某个单文件，而是整体分层方式：

- `Script/Config`
- `Script/Core`
- `Script/Design`
- `Script/StateMachine`
- `Script/System`
- `Script/UI`

这套分层说明它已经把下面这些事情分开了：

- 配置
- 基础设施
- 领域对象
- 流程控制
- 玩法系统
- 表现层

这对 `erAL` 非常重要，因为 `erAL` 未来也会面临：

- 大量静态数据
- 大量角色内容
- 大量事件流程
- 多前端或编辑器扩展

## 3. 已采纳的 Ark 思路

### 3.1 清晰的层级边界

`erAL` 当前已经采纳的对应分层：

- `src/eral/app`
- `src/eral/engine`
- `src/eral/domain`
- `src/eral/systems`
- `src/eral/content`
- `src/eral/ui`
- `src/eral/tools`

这一步借的是 `erArk` 的核心优点：

- 不把所有 Python 代码都塞进一个大目录。

### 3.2 配置与内容外置

当前已经采纳：

- 规则在 [`data/base/settlement_rules.toml`](D:\project\myERA\erAL\data\base\settlement_rules.toml)
- 指令在 [`data/base/commands.toml`](D:\project\myERA\erAL\data\base\commands.toml)
- 地图在 [`data/base/port_map.toml`](D:\project\myERA\erAL\data\base\port_map.toml)

这借的是 `erArk` 的工程思路：

- 尽量把静态内容放配置层，不直接写死在逻辑文件里。

### 3.3 工具链独立

当前已经采纳：

- `src/eral/tools/import_tw_axes.py`

这一步借的是 `erArk` 的工程化意识：

- 导入、生成、校验、编译都应该是独立工具，而不是散落在运行时代码里。

### 3.4 测试驱动的迭代方式

当前已经采纳：

- `tests/test_bootstrap.py`
- `tests/test_stat_axes.py`
- `tests/test_port_map.py`
- `tests/test_commands.py`
- `tests/test_navigation.py`

这不是照抄 `erArk` 某个具体测试文件，而是延续它“工程项目而不是脚本项目”的开发态度。

## 4. 谨慎借鉴的 Ark 思路

### 4.1 `Design` 和 `System` 的双核心风险

`erArk` 的 `Design` 与 `System` 都承载了不少玩法含义。

对 `erAL` 的处理策略：

- `domain` 只定义世界模型和状态结构。
- `systems` 只定义规则执行与流程编排。

也就是说：

- 不允许在 `domain` 里偷偷写一大堆结算逻辑。
- 不允许在 `systems` 里反过来发明一套新的状态模型。

### 4.2 `Core` 过胖风险

很多成熟 Python 项目容易把通用能力全塞进 `Core`。

对 `erAL` 的处理策略：

- `engine` 只放题材无关能力。
- 港区题材逻辑一律放 `domain` 或 `systems`。

例如：

- 事件总线可以放 `engine`
- 港区地点可见性不能放 `engine`

### 4.3 UI 反向污染系统层

`erArk` 有明显的 UI 分层，这点要学。

但 `erAL` 要更严格：

- `ui` 只消费结果，不直接写核心状态。
- 系统层产出 `ActionResult`、事件或视图数据。
- UI 不自己做规则判定。

## 5. 当前 `erAL` 中的 Ark 式落点

### `app`

对应借鉴：

- 启动、装配、资源注册、生命周期入口。

当前文件：

- [`bootstrap.py`](D:\project\myERA\erAL\src\eral\app\bootstrap.py)
- [`config.py`](D:\project\myERA\erAL\src\eral\app\config.py)

### `engine`

对应借鉴：

- 基础设施层。

当前文件：

- [`events.py`](D:\project\myERA\erAL\src\eral\engine\events.py)
- [`paths.py`](D:\project\myERA\erAL\src\eral\engine\paths.py)

### `domain`

对应借鉴：

- 领域模型层。

当前文件：

- [`world.py`](D:\project\myERA\erAL\src\eral\domain\world.py)
- [`stats.py`](D:\project\myERA\erAL\src\eral\domain\stats.py)
- [`map.py`](D:\project\myERA\erAL\src\eral\domain\map.py)
- [`actions.py`](D:\project\myERA\erAL\src\eral\domain\actions.py)

### `systems`

对应借鉴：

- 真正的玩法系统层。

当前文件：

- [`game_loop.py`](D:\project\myERA\erAL\src\eral\systems\game_loop.py)
- [`settlement.py`](D:\project\myERA\erAL\src\eral\systems\settlement.py)
- [`commands.py`](D:\project\myERA\erAL\src\eral\systems\commands.py)
- [`navigation.py`](D:\project\myERA\erAL\src\eral\systems\navigation.py)

### `content`

这是 `erAL` 相比 `erArk` 进一步强化的一层。

原因：

- 你这个项目后期角色包和口上包会非常重。

当前文件：

- [`stat_axes.py`](D:\project\myERA\erAL\src\eral\content\stat_axes.py)
- [`tw_axis_registry.py`](D:\project\myERA\erAL\src\eral\content\tw_axis_registry.py)
- [`port_map.py`](D:\project\myERA\erAL\src\eral\content\port_map.py)
- [`commands.py`](D:\project\myERA\erAL\src\eral\content\commands.py)
- [`settlement.py`](D:\project\myERA\erAL\src\eral\content\settlement.py)

## 6. 未来继续从 Ark 借的部分

后续建议继续从 `erArk` 借鉴：

1. 状态机式流程控制。
   特别适合事件、夜袭、约会、H 流程。
2. 编辑器友好的配置组织。
3. 系统级模块拆分。
   例如 `relationship / event / ai / schedule / h_scene`。
4. 多层工具链。
   导入器、校验器、编译器、迁移器分开。

## 7. 明确不照搬的部分

以下内容不直接照搬：

1. `erArk` 的题材逻辑。
2. `erArk` 中对具体玩法的命名方式。
3. 任何不适合港区后宫题材的角色/地图/系统设计。
4. 任何会导致 `domain` 和 `systems` 边界重新变糊的实现习惯。

## 8. 结论

`erAL` 对 `erArk` 的借鉴重点不是：

- “做得像 Ark”

而是：

- “用 Ark 证明过可行的 Python 工程组织方式，去承接 TW 风格的玩法复杂度”

这是工程层借鉴，不是题材层借鉴。


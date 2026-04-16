# L5 Inventory And Oath Foundation Design

## 背景

erAL 当前已经具备关系、约会、事件、对话、经济循环与存档主链，但 L5 的誓约、商店、礼物、皮肤等内容仍缺一个稳定的道具层。当前项目里已经存在：

- `relationship_stages.toml` 的 `requires_item` 配置
- UI 对 `requires_item` 的只读提示
- `confess` 等亲密指令

但运行时还没有：

- 玩家背包
- 道具持久化
- 基于道具的命令门禁
- 可复用的成功率判定入口

这导致誓约、商店、礼物、皮肤店都无法用统一接口接入，也会把后续改动压回 UI 或单个指令特例里。

## 目标

本轮先补齐一条低耦合底座，让 `pledge_ring` 成为第一件真实道具，并让“誓约”成为第一条真实消费链路。

本轮完成后应满足：

- `WorldState` 有最小可用的 `inventory`
- 存档可保存/读取 `inventory`，旧档无该字段时平滑降级
- 命令定义可声明 `required_items`
- 门禁层能给出“道具不足”的明确拒绝理由
- 新增独立 `oath` 指令，不复用 `confess`
- `oath` 至少要求关系阶段达到“喜欢”且拥有 `pledge_ring`
- `oath` 成功时消耗戒指并进入“誓约”阶段，失败时不消耗
- 成功率走统一判定接口，先给 `oath` 接入，后续可扩到 `kiss` 等其他指令

## 明确不做

本轮不做以下内容：

- 不实现具体商店地点、商店 UI、购买流程
- 不接入明石或不知火角色
- 不实现皮肤商店实例
- 不实现通用“使用道具”指令
- 不把“恋人”并入关系阶段
- 不让 `relationship_stages.toml` 的 `requires_item` 直接影响关系阶段解析

这里的取舍是有意的：先把“道具存在、能被校验、能被消费、能持久化”这条底层链路做稳，再让商店、礼物、皮肤、誓约内容挂上来。

## 关系与语义约束

关系阶段保持当前五段，不新增“恋人”阶段：

- 陌生
- 友好
- 喜欢
- 爱
- 誓约

“恋人”如果未来要表达，应作为独立长期状态处理，优先考虑放在 `TALENT` 或等价的长期标记层，而不是篡改阶段表。

语义上保持：

- `confess` 仍是告白/亲密推进指令
- `oath` 是独立的誓约指令，等价于“拿誓约之戒正式求婚”

这样后续即使要加入“告白成功但尚未誓约”“恋人状态已成立但未誓约”等更细语义，也不会破坏现有阶段表。

## 架构设计

本轮新增三层能力：

1. 最小背包层
2. 命令道具门禁层
3. 通用成功率判定层

它们都挂在现有主链上，不引入新的 UI 主流程。

### 1. 最小背包层

`WorldState` 新增：

```python
inventory: dict[str, int] = field(default_factory=dict)
```

设计约束：

- 键是 `item_key`
- 值是玩家持有数量
- 只表达“有多少”，不表达实例、品质、装备槽、耐久、来源
- 不绑定具体商店或角色

这是一个刻意保守的数据结构。它足以支撑：

- 誓约戒指校验与消耗
- 未来商店购买入账
- 未来礼物/消耗品系统

同时不会过早承诺更复杂的装备或实例化模型。

### 2. 物品静态定义层

新增一个最小物品定义文件与加载器。首轮只需支持：

```python
@dataclass(frozen=True, slots=True)
class ItemDefinition:
    key: str
    display_name: str
    category: str
    description: str
    price: int = 0
```

首轮至少存在一条数据：

- `pledge_ring`

`category` 先允许表达未来商店归属，但不立即实现商店系统：

- `general_shop`
- `skin_shop`

这里提前把“两类商店”的归属信息放在物品层，而不是商店层，原因是后续无论入口做成“地图地点”“商店菜单”还是“和明石/不知火对话进入”，底层商品池都可以复用这份数据。

### 3. 命令门禁层

`CommandDefinition` 新增：

```python
required_items: dict[str, int]
```

判定位置仍然放在 `CommandSpecificGate`，而不是 UI、事件或关系解析层。

规则：

- 缺少任一所需道具时，命令不可执行
- 门禁失败直接返回中文原因
- 第一版文案以可解释性优先，例如：
  - `缺少所需道具：誓约之戒 x1。`

这样做的收益：

- 和地点、时段、关系阶段门禁并列
- 失败原因统一从命令服务抛出
- 后续商店、礼物、任务钥匙都能直接复用

### 4. 通用成功率判定层

新增统一判定接口，而不是给 `oath` 单独写死概率逻辑。

建议抽象：

```python
@dataclass(frozen=True, slots=True)
class ResolutionResult:
    success: bool
    chance: float
    reasons: tuple[str, ...] = ()
```

命令定义新增可选字段，例如：

```python
resolution_key: str | None
```

命令执行流程在“门禁通过后、正式写结果前”调用判定层：

1. 先通过所有 gate
2. 再进入 resolution
3. 根据成功或失败走不同分支

第一轮只实现 `oath` 对应的判定器，但接口必须允许后续扩到：

- `kiss`
- 部分 `confess`
- 特殊事件分支
- 高风险调教或亲密指令

## Oath 指令设计

新增独立命令：

- key: `oath`
- display_name: `誓约`

### 硬门槛

`oath` 的执行前提：

- 关系阶段至少为 `like`
- 背包中有 `pledge_ring`
- 其他原有地点、时段、状态门禁按命令配置继续生效

这里明确不要求先达到 `love`。用户语义已经确定：誓约至少从“喜欢”开始尝试即可。

### 成功与失败

`oath` 走统一判定层：

- 判定失败：
  - 不消耗 `pledge_ring`
  - 不进入誓约阶段
  - 返回失败结果与对应文案
- 判定成功：
  - 消耗 `pledge_ring`
  - 写入誓约结果
  - 刷新关系阶段到 `oath`
  - 允许事件与对话命中誓约分支

### 首轮成功率输入

成功率接口先预留多因子输入，但第一轮只保证这些来源可接：

- affection
- trust
- 指定 `TALENT`
- 负面 `mark`
- 运行时 `condition`

公式首轮保持简单：

- 基础概率
- 若干正负修正
- 最终值做上下限夹取

实现重点不是立刻追求高精度，而是保证：

- 公式位置集中
- 输入项可扩展
- 指令主流程不需要为每个概率指令反复改代码

## 数据流

`oath` 的目标运行流程如下：

1. 玩家拥有 `pledge_ring`
2. 玩家选择 `oath`
3. `CommandService` 进入 gate 检查
4. `CommandSpecificGate` 检查关系阶段与 `required_items`
5. gate 通过后，统一判定层计算 `ResolutionResult`
6. 若失败：
   - 返回失败 action result
   - 不消耗戒指
   - 不写誓约状态
7. 若成功：
   - 先消费 `pledge_ring`
   - 再写入誓约结果
   - 刷新阶段与相关状态
   - 继续走事件/对话

这里把“消费戒指”放在成功分支里，是为了严格满足“失败不消耗”的需求。

## 错误处理与兼容策略

### 存档兼容

`SaveService` 增加 `inventory` 持久化。

读取旧档时：

- 如果没有 `inventory` 字段，按空背包 `{}` 处理
- 如果数量不是合法整数，按 `0` 或跳过该项处理
- 不因为背包字段缺失而让旧档报错

### 运行时一致性

消费道具时必须满足：

- 不能扣成负数
- 只在成功分支扣减
- 扣减后数量为 `0` 的道具可以直接移除键，保持存档整洁

### 失败反馈

本轮优先保证三类可解释失败：

- 关系阶段不足
- 道具不足
- 判定失败但可重试

其中“判定失败但可重试”必须和“门禁失败”区分开，避免玩家误以为是缺条件。

## 文件与职责拆分

建议新增或修改的职责边界如下：

- `src/eral/domain/world.py`
  - 为 `WorldState` 增加 `inventory`
- `src/eral/content/items.py`
  - 加载最小 `ItemDefinition`
- `data/base/items.toml`
  - 先定义 `pledge_ring`
- `src/eral/content/commands.py`
  - 支持 `required_items`、`resolution_key`
- `data/base/commands.toml`
  - 新增 `oath`
- `src/eral/systems/command_gates.py`
  - 检查 `required_items`
- `src/eral/systems/save.py`
  - 持久化 `inventory`
- `src/eral/systems/resolution.py`
  - 放统一成功率判定逻辑
- `src/eral/app/bootstrap.py`
  - 装配 item 定义与 resolution service
- `tests/test_commands.py`
  - 补 `required_items` 与 `oath` 相关测试
- `tests/test_save_load.py`
  - 补 `inventory` 持久化与旧档降级测试

如果实现时发现 `inventory` 读写逻辑开始扩张，可以后续再拆出 `InventoryService`；但本轮先不强制新增 service，避免为一个极简字典过度设计。

## 测试策略

本轮至少覆盖以下场景：

### 命令门禁

- 无 `pledge_ring` 时，`oath` 不可执行，错误理由包含道具不足
- 有 `pledge_ring` 但阶段不到 `like` 时，`oath` 不可执行，错误理由包含关系阶段不足

### 判定语义

- `oath` 判定失败时，不消耗 `pledge_ring`
- `oath` 判定成功时，消耗 `pledge_ring`
- `oath` 判定成功后，角色关系阶段刷新到 `oath`

### 存档兼容

- 存档能写出 `inventory`
- 读档能恢复 `inventory`
- 旧档缺少 `inventory` 字段时可正常读取

### 回归保护

确保新增字段不会破坏：

- 现有命令加载
- 现有 quicksave 读写
- 现有关系阶段刷新

## 后续扩展方向

本轮完成后，可以按以下顺序扩展：

1. 商店最小闭环
   - 先做“日常用品店”
   - 再做“皮肤店”
2. 明石/不知火入口语义
   - 作为商店的角色入口，而不是底层商品系统的一部分
3. 礼物与恢复品
4. 更多走统一判定层的亲密指令

其中“两个商店”的建议方向是：

- 日常用品店偏 eraTW 语义，出售 `general_shop` 物品
- 皮肤店偏碧蓝航线特色，出售 `skin_shop` 物品

但这两者都应该建立在同一份物品定义和同一个玩家背包之上。

## 结论

本轮最稳的做法不是先做商店，也不是先给誓约写特例，而是：

- 先补通用背包
- 再补命令道具门禁
- 再补统一成功率接口
- 最后用 `pledge_ring -> oath` 这条链验证整个设计

这样既能尽快让碧蓝航线的誓约语义落地，也能为后续两个商店、礼物、皮肤和更多概率指令留出稳定扩展口。

# L5 Oath Shop Vertical Slice Design

## 背景

L5 的道具与誓约底座已经落地，当前项目已经具备：

- `inventory` 背包与存档兼容
- `items.toml` 最小物品目录
- `required_items` 命令门禁
- `oath` 指令与统一判定入口
- 成功誓约后通过 `oath` mark 覆盖到誓约阶段

现在真正缺的不是再做一个新底座，而是把这些能力串成一条玩家可感知的闭环。用户希望后续商店可以带上碧蓝航线语义，例如日常用品店、皮肤店，以及最终由明石 / 不知火作为入口角色；但现阶段项目还不成熟，入口形态不应该过早写死。

因此下一阶段的目标不是“先把整个商店系统做满”，也不是“只补誓约文本”，而是先做一条最小可玩垂直切片：

- 玩家能买到 `pledge_ring`
- 玩家满足关系条件时能执行 `oath`
- 成功时消耗戒指并进入誓约阶段
- 失败时保留戒指并给出独立反馈

## 目标

本阶段完成后应满足：

- 存在一个最小可访问的日常商店入口
- 商店能按商品目录列出并购买商品
- 购买会校验金钱、扣款并把商品写入 `inventory`
- `pledge_ring` 可以通过商店获得，而不再只靠测试注入
- `oath` 可以消费商店买到的戒指完成完整链路
- `oath_success` 与 `oath_failure` 至少能命中事件或对话分支
- 商店底层能区分 `general_shop` 与 `skin_shop`，但本轮只要求日常店可购买

## 明确不做

本阶段不做以下内容：

- 不实装明石 / 不知火角色包
- 不把商店逻辑写死到任意单个 NPC 身上
- 不做完整皮肤购买与换装表现
- 不重做地图系统，只为商店强行上多层地图
- 不在本轮扩展完整礼物系统
- 不让所有高亲密指令都接入统一判定，只保留后续扩展口

## 方案对比

### 方案 A：先做完整商店，再回接誓约

优点：

- 商店系统会更完整
- 后续加日用品与皮肤商品时阻力更小

缺点：

- 玩家闭环反馈慢
- 很容易先把入口、UI 和 NPC 语义写死
- 在项目当前阶段投入过重

### 方案 B：只做誓约内容，不做购买链路

优点：

- 见效最快
- 角色内容产出最直接

缺点：

- 戒指只能靠测试或调试注入
- 商店与道具经济仍然悬空
- 很快又要返工补真实来源

### 方案 C：做“誓约-商店垂直切片”

优点：

- 以 `pledge_ring` 打通真实玩家链路
- 商店、钱包、背包、誓约四层能一次验证
- 入口形式保持松耦合，后续可改成地点或 NPC

缺点：

- 本轮商店功能不会很多
- 皮肤店只能先做数据骨架，不能一步到位

推荐采用方案 C。它最符合当前“项目刚起步、指令和入口后续还会改”的现实。

## 设计原则

1. 商店底层与商店入口分离。
2. 玩家购买链路必须依赖既有 `wallet + inventory`，禁止另建商品背包。
3. 誓约链路继续复用既有 `required_items + resolution`，不做特例捷径。
4. `general_shop` 和 `skin_shop` 必须共用一套商品目录与店面定义。
5. NPC、地点、系统菜单都只能作为“打开店面”的入口，不拥有购买规则本身。

## 架构设计

本阶段新增三块内容：

1. 商店目录与店面定义
2. 商店购买服务
3. 誓约结果内容分支

### 1. 商店目录与店面定义

`items.toml` 继续作为商品静态信息源，但需要补齐当前缺失的字段：

- `category`
- `description`
- `price`

同时新增最小 `shopfronts.toml`，表达“哪个店面卖哪些分类或哪些商品”。建议最小结构：

```toml
[[shopfronts]]
key = "general_shop"
display_name = "日常用品店"
item_categories = ["general_shop"]

[[shopfronts]]
key = "skin_shop"
display_name = "皮肤商店"
item_categories = ["skin_shop"]
```

这里故意不放 NPC 或地点字段。商店底层只负责“卖什么”，不负责“怎么被打开”。

### 2. 商店购买服务

新增 `ShopService`，负责：

- 读取 item catalog 与 shopfront 定义
- 根据 `shopfront_key` 列出可卖商品
- 校验玩家余额
- 扣减资金
- 向 `inventory` 入账
- 返回结构化失败原因

建议返回结果结构：

```python
@dataclass(frozen=True, slots=True)
class PurchaseResult:
    success: bool
    item_key: str
    count: int
    total_price: int
    reason: str | None = None
```

失败原因首轮至少区分：

- 店面不存在
- 商品不存在
- 商品不在该店面出售
- 余额不足
- 购买数量非法

### 3. 最小商店入口

本阶段需要一个能被玩家触发的入口，但不能把后续扩展锁死。最稳的做法是：

- 先提供一个临时系统入口或最小命令入口
- 入口只负责选择店面并调用 `ShopService`
- 不在入口里写任何商品价格或购买规则

入口形式可以后续替换成：

- 地点菜单
- 明石 / 不知火对话
- 顶层系统按钮

只要最终都调用同一个 `ShopService` 即可。

### 4. 誓约内容分支

当前 `oath` 的规则已经成立，但玩家层表现还不完整。下一阶段要补的不是新判定，而是结果内容：

- `oath_success`
- `oath_failure`

两者都应在 `CommandService` 结算完成后触发到事件 / 对话层。这样：

- 成功时可以写角色专属誓约文本
- 失败时可以给出“拒绝但保留戒指”的差分反馈

第一轮至少让 1 名正式角色具备成功与失败差分文本，其余角色可以先走通用兜底。

## 数据流

### 购买链路

1. 玩家打开某个店面
2. 店面列出可售商品
3. 玩家选择 `pledge_ring`
4. `ShopService` 校验店面、商品、余额与数量
5. 成功时扣减钱包并写入 `inventory`
6. 失败时返回明确原因

### 誓约链路

1. 玩家持有 `pledge_ring`
2. 玩家满足 `like` 及以上关系阶段
3. 玩家执行 `oath`
4. `required_items` 门禁通过
5. `resolution` 执行成功率判定
6. 失败时保留戒指并触发 `oath_failure`
7. 成功时消费戒指、写入 `oath` mark、触发 `oath_success`
8. `RelationshipService` 刷新到 `誓约` 阶段

## 文件边界

建议新增或修改以下职责：

- `data/base/items.toml`
  - 补齐已有商品字段，首轮至少保证 `pledge_ring` 完整
- `data/base/shopfronts.toml`
  - 定义 `general_shop` / `skin_shop`
- `src/eral/content/items.py`
  - 补齐完整 item 字段加载
- `src/eral/content/shops.py`
  - 加载 shopfront 定义
- `src/eral/systems/shop.py`
  - 商店列货与购买结算
- `src/eral/app/bootstrap.py`
  - 装配 `ShopService`
- `src/eral/systems/commands.py`
  - 在 `oath` 结果后发出 success / failure 内容钩子
- `data/base/events.toml` 或对应事件配置
  - 增加 `oath_success` / `oath_failure` 钩子
- `data/characters/...`
  - 至少给 1 名角色补誓约成功/失败差分文本
- `tests/test_shop_service.py`
  - 新增商店服务测试
- `tests/test_commands.py`
  - 补真实购买后誓约的链路测试
- `tests/test_dialogue_service.py`
  - 补誓约内容分支测试

## 测试策略

### 商店服务

- 日常店可以列出 `pledge_ring`
- 皮肤店当前不会卖 `pledge_ring`
- 金钱不足时购买失败且不入账
- 购买成功时扣款并写入 `inventory`

### 誓约闭环

- 使用商店买到的戒指可以执行 `oath`
- `oath` 失败时不消耗戒指
- `oath` 成功时消耗戒指并进入誓约阶段

### 内容分支

- 成功誓约能命中 `oath_success`
- 失败誓约能命中 `oath_failure`
- 无专属文本时仍能落到通用兜底

### 回归保护

- 旧存档读取不受商店系统影响
- 非商店指令不依赖任何店面状态
- 既有钱包与道具功能保持通过

## 后续扩展方向

本阶段完成后，再按这个顺序扩展：

1. 让商店入口挂到地点
2. 接入明石 / 不知火作为角色入口
3. 扩充日常用品商品
4. 启动皮肤店真实购买闭环
5. 让更多高亲密指令接入统一判定层

## 结论

下一阶段最合理的做法不是把商店或誓约拆开做，而是围绕 `pledge_ring` 做一条可玩的垂直切片：

- 先让商店成为真实来源
- 再让誓约成为真实消费
- 同时把皮肤店保留在同一套商店骨架里

这样可以最小成本验证 L5 的核心体验，又不会把后续的 NPC 商店入口、地图入口和皮肤店扩展提前锁死。

# erAL TODO（数据/内容侧 — 你填写）

更新时间：2026-04-26

> 当前 MVP 开发表请优先查看 [MVP.md](MVP.md)。本文件只保留数据/内容侧待填项，凡是不影响 MVP 主链闭环的内容先下沉到后续队列。

---

## 当前数据完成度总览

| 数据文件 | 完成度 | 说明 |
|----------|--------|------|
| `train.toml` | 100% | 165 条指令定义完整 |
| `command_effects.toml` — source | 100% | 165 条 SOURCE 值已填 |
| `command_effects.toml` — vitals | **0%** | 165 条体力/气力消耗全空 |
| `command_effects.toml` — experience | **0%** | 165 条经验值全空 |
| `cup_routing.toml` | ~80% | 29 条 routing 规则 |
| `source_cbva.toml` | ~70% | 少量 SOURCE 走 identity |
| `source_extra.toml` | ~50% | 45 条 modifier，常用天赋已覆盖 |
| `marks.toml` | ~60% | 5 条刻印定义 |
| `abl_upgrade.toml` | ~60% | JUEL 成本/EXP 需求待微调 |
| `palam_decay.toml` | 100% | 比例衰减已配置 |
| `palam_to_juel.toml` | 100% | 珠转换已配置 |
| `palamlv_curves.toml` | 100% | 阈值曲线已配置 |
| `relationship_growth.toml` | 100% | 公式框架已配置 |

**最大瓶颈**：vitals 和 experience 全空 → 体力/经验系统无法验证。

---

# 一、指令效果数据

## D1. vitals 填充 — 体力/气力消耗（🔴 最优先）

> 工作量：165 条 × 1~2 个值

**格式**：
```toml
[[effect]]
command_index = 0
vitals.target = {0 = 10, 1 = 5}   # 0=体力, 1=气力
```

**参考标准**：
| 指令类型 | 体力消耗 | 气力消耗 |
|----------|---------|---------|
| 轻度接触（爱抚、对话） | 5~10 | 0~5 |
| 中度（口交、V/A 插入） | 15~30 | 10~20 |
| 重度（SM、持续行为） | 30~50 | 20~40 |
| 被动方 | 低 | 低 |

- [ ] D1.1 日常系指令 vitals（talk/greet/observe 等，约 10 条）
- [ ] D1.2 轻度调教 vitals（爱抚/接吻/胸部爱抚/手淫 等，约 30 条）
- [ ] D1.3 中度调教 vitals（口交/V插入/A插入 各体位，约 50 条）
- [ ] D1.4 奉仕系 vitals（手奉仕/口奉仕/乳奉仕 等，约 15 条）
- [ ] D1.5 道具系 vitals（跳蛋/按摩器/鞭 等，约 25 条）
- [ ] D1.6 特殊行为 vitals（SM/野外/薬物/强迫 等，约 20 条）
- [ ] D1.7 受动系 vitals（被插入各体位，约 15 条）

**不想手填 165 条？** 告诉我 category → 默认 vitals 映射表，我批量生成后你审查修改。

---

## D2. experience 填充 — 经验值（🔴 最优先）

> 工作量：165 条 × 2~3 个值

**格式**：
```toml
[[effect]]
command_index = 0
experience.target = {0 = 1, 10 = 1}
```

**EXP 轴索引（须确认）**：
| 索引 | 经验名 | 获取方式 |
|------|--------|---------|
| 0 | Ｃ経験 | Ｃ刺激指令 |
| 1 | Ｖ経験 | Ｖ刺激指令 |
| 2 | Ａ経験 | Ａ刺激指令 |
| 3 | Ｂ経験 | 胸部刺激指令 |
| 4 | Ｍ経験 | 乳头刺激指令 |
| 10 | 亲密経験 | 接吻/拥抱 |
| 11 | 奉仕経験 | 手/口/胸奉仕 |
| 12 | 性交経験 | V/A 插入（区分插入方） |
| 13 | ＳＭ経験 | SM 系指令 |
| 14 | 露出経験 | 野外/摄影 |
| 15 | 自慰経験 | 自慰相关 |

- [ ] D2.1 先确认 EXP 轴定义（`data/base/axes/exp.toml` 的 index→key 映射是否正确）
- [ ] D2.2 日常系经验值
- [ ] D2.3 轻度调教经验值
- [ ] D2.4 中度调教经验值（插入位要保证性交経験+1）
- [ ] D2.5 奉仕系经验值
- [ ] D2.6 道具系经验值
- [ ] D2.7 特殊行为经验值

---

# 二、角色包数据

## D3. 现有角色补全

| 角色 | 状态 | 缺项 |
|------|------|------|
| laffey | ~80% | dialogue/events 内容少 |
| javeline | ~50% | marks/cloths/dialogue 骨骼态 |
| enterprise | ~50% | marks/cloths/dialogue 骨骼态 |
| shiranui | ~30% | abl/talent/cflag/marks/dialogue 全缺 |
| akashi | ~30% | abl/talent/cflag/marks/dialogue 全缺 |

- [ ] D3.1 给 shiranui 补 abl.toml + talent.toml + cflag.toml
- [ ] D3.2 给 akashi 补 abl.toml + talent.toml + cflag.toml
- [ ] D3.3 给 javeline/enterprise 补 marks.toml
- [ ] D3.4 各角色 dialogue.toml 补 10~20 条基础台词（打招呼/拒绝/日常）
- [ ] D3.5 各角色 events.toml 补 3~5 个基础事件

## D4. 新增角色（β 版目标：共 6~8 个）

- [ ] D4.1 创建角色目录 + character.toml（确定 key/tags/初始位置/日程）
- [ ] D4.2 填写初始 base/palam/abl/talent/cflag 值
- [ ] D4.3 填写 dialogue.toml（基础台词 20 条起）
- [ ] D4.4 填写 events.toml（角色专属事件 3~5 个）
- [ ] D4.5 创建角色目录（第 6 个角色）
- [ ] D4.6 创建角色目录（第 7 个角色）
- [ ] D4.7 创建角色目录（第 8 个角色）

---

# 三、结算规则数据

## D5. source_cbva.toml 补全

- [ ] D5.1 检查 SOURCE 14（恐惧）是否需要 CBVA 规则
- [ ] D5.2 检查 SOURCE 21（征服/优越）是否需要 CBVA 规则
- [ ] D5.3 检查 SOURCE 22 是否需要 CBVA 规则
- [ ] D5.4 检查 SOURCE 55（加虐）是否需要 CBVA 规则
- [ ] D5.5 审查 ABL scale 参数（当前全 0.1）

## D6. source_extra.toml 扩展

> 当前已覆盖：胆量/态度/回应/自尊心/娇俏/懒散/自制心/冷漠/感情缺乏/性的兴趣/开朗阴郁/底线/引人注目/无知/贞操/自己爱/抵抗/羞耻心/痛觉/弄湿难易/容易自慰/污臭耐性/献身的/快感应答/容易高潮/倒错/施虐/受虐/魅力/魅惑/谜之魅力/风骚/幼儿/酒耐性 共 33 种天赋

- [ ] D6.1 回复速度（talent 130）→ 影响体力/气力自然恢复速度（非 SOURCE，在 vital.py 已有基础）
- [ ] D6.2 检查 eraTW 中还有哪些常用天赋未覆盖 → 逐条确认是否加入

## D7. cup_routing.toml 审查

- [ ] D7.1 扫描所有 SOURCE 使用索引，与 routing 规则做 diff
- [ ] D7.2 补充缺失 routing
- [ ] D7.3 检查 scale 值是否合理
- [ ] D7.4 确认 5 个 CFLAG 写入是否需要增加

## D8. marks.toml 扩展

> 当前：苦痛/快乐/不埒/反发/成长 + 誓约（commanded）

- [ ] D8.1 β 版目标确认：当前 5+1 条是否足够？
- [ ] D8.2 (可选) 新增屈服刻印 / specialist 刻印

---

# 四、新增规则数据（配合代码侧新系统）

以下数据文件是代码侧新系统（S1~S7）需要的数据源，代码完成后你再填值。

## D9. 体位 SOURCE 倍率（配合 S1）

- [ ] D9.1 创建 `data/base/rules/source_pose.toml`
- [ ] D9.2 定义各体位 × 各 SOURCE 的倍率：
  - 正常位：V快感 ×1.0, A快感 ×0.8, B快感 ×0.5
  - 後背位：V快感 ×1.2, A快感 ×0.9, 恭顺 ×1.2
  - 騎乗位：V快感 ×1.3, 恭顺 ×0.7
  - 等等

## D10. 高潮阈值配置（配合 S2）

- [ ] D10.1 创建 `data/base/rules/orgasm.toml`
- [ ] D10.2 定义 PALAM 快感阈值 × 各快感类型（C/V/A/B/M）
- [ ] D10.3 定义高潮后 SOURCE 加成

## D11. 反击规则配置（配合 S5）

- [ ] D11.1 创建 `data/base/rules/counter.toml`
- [ ] D11.2 反击触发概率 × 关系阶段 × 刻印等级
- [ ] D11.3 反击类型及对应 SOURCE

## D12. STAIN 轴定义（配合 S4）

- [ ] D12.1 创建 `data/base/axes/stain.toml`，定义 8 种体液
- [ ] D12.2 定义各指令→STAIN 映射

## D13. EQUIP 轴定义（配合 C2）

- [ ] D13.1 创建 `data/base/axes/equip.toml`
- [ ] D13.2 定义装备槽位（与 eraTW 32 槽位对齐）
- [ ] D13.3 定义装备互斥关系

---

# 五、事件与口上内容

## D14. 基础事件补充（配合 E4）

- [ ] D14.1 早间随机事件 5~10 条
- [ ] D14.2 午间随机事件 5~10 条
- [ ] D14.3 晚间随机事件 5~10 条
- [ ] D14.4 天气相关事件 3~5 条

## D15. 口上变体内容（配合 K1）

- [ ] D15.1 先确认变体标记格式（与代码侧对齐）
- [ ] D15.2 为 laffey 核心指令（kiss/hug/爱抚系列）添加变体台词
- [ ] D15.3 为 laffey 添加刻印等级变体台词（快乐刻印 Lv2/Lv3 时不同台词）
- [ ] D15.4 为 laffey 添加关系阶段变体台词（陌生人/友好/恋慕 不同台词）

---

# 六、物品与商店数据

## D16. 物品扩展

- [ ] D16.1 现有 items.toml 审计：是否覆盖了基本游戏道具（恢复品/礼物/调教道具）
- [ ] D16.2 补充缺失的常用道具（体力药、气力药、礼物 5~10 种）
- [ ] D16.3 道具使用效果定义（回复量/SOURCE 加成）

## D17. 礼物偏好完善

- [ ] D17.1 为每个角色设定 gift_preferences（当前仅 laffey 有）

---

# 快速推进建议

如果你只有 1~2 小时：

1. **先 D1.1~D1.2**：填 40 条日常+轻度调教的 vitals 值
2. **再 D2.1**：确认 EXP 轴定义
3. **然后 D2.2~D2.4**：填对应 experience 值

只要你填了代表性的 40~50 条 vitals+experience，我就可以跑通完整的体力消耗→疲劳→ABLUP 验证。

不想手填？告诉我 category → 默认值映射表，我批量生成。

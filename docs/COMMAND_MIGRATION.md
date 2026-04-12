# Command Migration

> 用这份文档管理 `eraTW` 指令向 `erAL` 的迁移进度。原则是按“组别 -> 批次 -> 单指令状态”推进，不按全量指令平铺推进。

## 状态说明

- `未开始`：还没进入实现
- `已建模`：已有命令定义或迁移计划
- `已接命令`：已进入 `commands.toml`
- `已接事件/文本`：已有对应事件或对话
- `已测试`：有自动化测试覆盖
- `完成`：命令、事件/文本、测试都齐

## 日常互动

### A 批

- [x] `chat`
- [x] `praise`
- [x] `touch_head`
- [x] `share_snack`
- [x] `paperwork`
- [x] `scold`

### B 批

- [x] `hug`
- [x] `lap_pillow`
- [x] `tea`
- [x] `listen`
- [x] `clink`
- [x] `care`

### C 批

- [x] `apologize` 完成
- [x] `help_work` 完成
- [x] `pat_cheek` 完成
- [x] `poke_cheek` 完成
- [x] `read_aloud` 完成

## 同行

### A 批

- [x] `invite_follow`
- [x] `dismiss_follow`
- [x] `walk_together`

### B 批

- [x] `follow_rest` 完成
- [x] `escort_room` 完成
- [x] `follow_training` 完成
- [x] `follow_meal` 完成

## 约会

### A 批

- [x] `invite_date`
- [x] `end_date`
- [x] `hold_hands`
- [x] `date_stroll`
- [x] `date_meal`

### B 批

- [x] `date_watch_sea`
- [x] `gift`
- [x] `dessert_date`
- [x] `room_visit`
- [x] `enter_room`

### C 批

- [x] `buy_things` 完成
- [x] `flower_shop` 完成
- [x] `drink_together` 完成
- [x] `fishing_date` 完成
- [x] `takeout_bento` 完成

## 轻亲密

### A 批

- [x] `tease`
- [x] `date_tease`
- [x] `kiss`
- [x] `confess`

### B 批

- [x] `invite_dark_place` 完成
- [x] `sleep_together` 完成
- [x] `room_kiss` 完成
- [x] `night_visit` 完成

## 生活/工作

### A 批

- [x] `train_together`

### B 批

- [x] `rest`
- [x] `study`
- [x] `cook`
- [x] `eat_meal`
- [x] `invite_meal`
- [x] `nap`

## 深层 H 指令

- [ ] 整组暂缓到 MVP 后期

## 当前命令明细

| 指令 | 组别 | 批次 | 状态 |
| --- | --- | --- | --- |
| `chat` | 日常互动 | A | 完成 |
| `paperwork` | 日常互动 | A | 完成 |
| `share_snack` | 日常互动 | A | 完成 |
| `praise` | 日常互动 | A | 完成 |
| `touch_head` | 日常互动 | A | 完成 |
| `hug` | 日常互动 | B | 完成 |
| `scold` | 日常互动 | A | 完成 |
| `train_together` | 生活/工作 | A | 完成 |
| `rest` | 生活/工作 | B | 完成 |
| `study` | 生活/工作 | B | 完成 |
| `cook` | 生活/工作 | B | 完成 |
| `eat_meal` | 生活/工作 | B | 完成 |
| `invite_meal` | 生活/工作 | B | 完成 |
| `nap` | 生活/工作 | B | 完成 |
| `tease` | 轻亲密 | A | 完成 |
| `invite_follow` | 同行 | A | 完成 |
| `dismiss_follow` | 同行 | A | 完成 |
| `walk_together` | 同行 | A | 完成 |
| `lap_pillow` | 日常互动 | B | 完成 |
| `serve_tea` | 日常互动 | B | 完成 |
| `listen` | 日常互动 | B | 完成 |
| `clink_cups` | 日常互动 | B | 完成 |
| `care` | 日常互动 | B | 完成 |
| `kiss` | 轻亲密 | A | 完成 |
| `confess` | 轻亲密 | A | 完成 |
| `invite_date` | 约会 | A | 完成 |
| `end_date` | 约会 | A | 完成 |
| `hold_hands` | 约会 | A | 完成 |
| `date_stroll` | 约会 | A | 完成 |
| `date_meal` | 约会 | A | 完成 |
| `date_watch_sea` | 约会 | B | 完成 |
| `gift` | 约会 | B | 完成 |
| `dessert_date` | 约会 | B | 完成 |
| `room_visit` | 约会 | B | 完成 |
| `enter_room` | 约会 | B | 完成 |
| `date_tease` | 轻亲密 | A | 完成 |
| `apologize` | 日常互动 | C | 完成 |
| `help_work` | 日常互动 | C | 完成 |
| `pat_cheek` | 日常互动 | C | 完成 |
| `poke_cheek` | 日常互动 | C | 完成 |
| `read_aloud` | 日常互动 | C | 完成 |
| `follow_rest` | 同行 | B | 完成 |
| `escort_room` | 同行 | B | 完成 |
| `follow_training` | 同行 | B | 完成 |
| `follow_meal` | 同行 | B | 完成 |
| `buy_things` | 约会 | C | 完成 |
| `flower_shop` | 约会 | C | 完成 |
| `drink_together` | 约会 | C | 完成 |
| `fishing_date` | 约会 | C | 完成 |
| `takeout_bento` | 约会 | C | 完成 |
| `invite_dark_place` | 轻亲密 | B | 完成 |
| `sleep_together` | 轻亲密 | B | 完成 |
| `room_kiss` | 轻亲密 | B | 完成 |
| `night_visit` | 轻亲密 | B | 完成 |

## 下一推进顺序

1. 充实企业/拉菲事件与对话（目标各 20 事件 + 30 对话条目）
2. 端到端约会线 + 轻亲密线可玩测试
3. 为 5 角色补阶段差分文本
4. 连续 7 天可玩烟测

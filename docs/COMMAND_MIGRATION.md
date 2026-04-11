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

- [ ] `apologize`
- [ ] `help_work`
- [ ] `pat_cheek`
- [ ] `poke_cheek`
- [ ] `read_aloud`

## 同行

### A 批

- [x] `invite_follow`
- [x] `dismiss_follow`
- [x] `walk_together`

### B 批

- [ ] `follow_rest`
- [ ] `escort_room`
- [ ] `follow_training`
- [ ] `follow_meal`

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

- [ ] `buy_things`
- [ ] `flower_shop`
- [ ] `drink_together`
- [ ] `fishing_date`
- [ ] `takeout_bento`

## 轻亲密

### A 批

- [x] `tease`
- [x] `date_tease`
- [x] `kiss`
- [x] `confess`

### B 批

- [ ] `invite_dark_place`
- [ ] `sleep_together`
- [ ] `room_kiss`
- [ ] `night_visit`

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

## 下一推进顺序

1. 为 3 个角色补齐已完成指令批次的更多阶段差分文本
2. 继续接入第 4 个及之后的真实角色包
3. 开始规划更接近真实碧蓝航线角色的首批正式角色包
4. 梳理角色包条目数量缺口并接入校验器

# eraTW 调用链规则矩阵

## 1. 目的

这份文档把 `eraTW` 中与主循环最相关的几段 ERB 主干逻辑整理成“调用链规则矩阵”。

它回答的不是“变量是什么”，而是：

- 哪个入口在什么时候被调用
- 它读取哪些关键状态
- 它修改哪些关键状态
- 它会把流程送到哪里
- 对 `erAL` 来说哪些可以直接照搬语义

## 2. 当前覆盖

- [x] `BEFORETRAIN.ERB` 主循环前置处理骨架
- [x] `EVENTCOMEND.ERB` 行动后收尾骨架
- [x] `EVENTCOMEND2.ERB` 收尾重置与状态更新骨架
- [x] `DATE_CMN.ERB` 约会通用函数骨架
- [ ] `COMABLE` 详细分支矩阵
- [ ] `デート終了タイムアップ処理.ERB` 细节拆解

## 3. 总览

可以先把这几份文件理解成：

1. `BEFORETRAIN.ERB`
   每回合/每日开始前的大准备层
2. `COMABLE`
   当前指令能否执行的判定层
3. `EVENTCOMEND.ERB`
   指令或行为结束后的第一层收尾
4. `EVENTCOMEND2.ERB`
   收尾后的状态刷新、标记清理、前回指令记录
5. `DATE_CMN.ERB`
   约会名称、地点、剩余时间、约会后事件、告白等通用逻辑

## 4. BEFORETRAIN 规则矩阵

主入口：`@EVENTTRAIN`

### 4.1 主要职责

- 清空或刷新本回合临时状态
- 刷新天气、日期、月份
- 刷新角色移动与来访
- 重建起床/居住/同居/遭遇状态
- 派发早晨事件与每日事件

### 4.2 关键读写

读取：

- `FLAG:每日变更事件`
- `CFLAG:MASTER:初期位置`
- `CFLAG:*:生理周期`
- `CFLAG:*:神社在住`
- `CFLAG:*:現在位置`
- `CFLAG:*:陪睡中`
- `TALENT:*:恋慕`
- `FLAG:氣絶中断`

写入：

- `TFLAG:COMABLE管理 = 1`
- `CFLAG:*:初期位置`
- `CFLAG:*:前一次的位置`
- `CFLAG:*:遭遇位置`
- `CFLAG:MASTER:あなた前ターン位置`
- `TFLAG:你起床`
- `FLAG:祈願内容`
- `FLAG:精力強化回数`
- `FLAG:一時滞在`

### 4.3 直接调用到的重要流程

- `CALL M_TFLAG_CLEAR`
- `CALL PENIS_REFRESH`
- `CALL WEATHER_FORECAST_1TERM`
- `CALL WEATHER_FORECAST_1DAY`
- `CALL CHANGE_TIMEZONE`
- `CALL 来訪フラグ`
- `CALL 遭遇判定`
- `CALL CHARA_MOVEMENT`
- `CALL GOODMORNING`
- `CALL SYS_EVENT`
- `CALL IRAI_HAPPEN`
- `CALL IRAI_VANISH`

### 4.4 可直接迁移到 erAL 的语义

- 每日开始时需要统一清理临时标志
- 日程刷新、移动刷新、遭遇刷新是同一层流程，不该散落在 UI
- 起床、同居、陪睡、约会中断、来访等都属于“日开始或时段开始处理”
- `TFLAG:COMABLE管理` 这类值表明 `eraTW` 明确有一层“本回合指令可用性管理”

### 4.5 对 erAL 的实现建议

- 当前 `GameLoop.advance_time()` 过于轻量，后续应拆出 `before_time_advance` / `after_time_advance`
- 把“时段推进前置处理”和“遭遇刷新”明确做成系统层步骤
- 后续为 `同行 / 约会 / 宿舍停留 / 私密房间` 增加集中刷新逻辑

## 5. EVENTCOMEND 规则矩阵

主入口：`@EVENTCOMEND`

### 5.1 主要职责

- 行动后统一收尾
- 处理约会超时、睡眠、过夜、带回房间、疲劳中断
- 结束 `うふふ/诶嘿嘿`、同行、约会等状态
- 处理泡澡、疲劳、回家、时间停止善后

### 5.2 关键读写

读取：

- `FLAG:宴会開催フラグ`
- `TFLAG:102`
- `CFLAG:MASTER:現在位置`
- `CFLAG:MASTER:约会中`
- `FLAG:约会的对象`
- `TFLAG:约会前好感度`
- `CFLAG:*:同行`
- `CFLAG:*:诶嘿嘿`
- `BASE:*:体力`

写入：

- `FLAG:気絶中断`
- `CFLAG:MASTER:就寝時間`
- `CFLAG:MASTER:現在位置`
- `CFLAG:*:约会中 = MAIN_MAP`
- `CFLAG:*:同行 = 0`
- `FLAG:约会的对象 = 0`
- `TFLAG:约会前好感度 = 0`
- `TFLAG:106 = 0`

### 5.3 直接调用到的重要流程

- `CALL TURN_RESET`
- `CALL ENKAI_SINKOU`
- `CALL 约会終了タイムUP処理`
- `CALL AFTER_AFFAIR`
- `CALL ENDUFUFU_ALL`
- `CALL CLEAN_GROUP_DATES`
- `CALL SET_MAP_WEATHER_BGCOLOR`
- `CALL CHARA_SLEEP`
- `CALL KOJO_MESSAGE_SEND(...)`

### 5.4 可直接迁移到 erAL 的语义

- 约会不是一条简单布尔状态，结束时会统一清理多个变量
- 行动结束和日结束都可能触发“送回房间/回家/中断约会”
- 同行与约会在收尾时一起结算，不是完全独立系统
- 体力不足、地点切换、泡澡、时间停止等都可能打断亲密状态

### 5.5 对 erAL 的实现建议

- 需要单独的“行动后收尾系统”，不要全塞在 `CommandService.execute()`
- 约会结束应集中处理：清约会对象、清同行、重算地点、派发结束事件
- 后续疲劳、过夜、陪睡和房间访问都应走统一结算出口

## 6. EVENTCOMEND2 规则矩阵

主入口：`@TURN_RESET`

### 6.1 主要职责

- 把本回合指令相关临时变量归零
- 记录 `SELECTCOM`、前回结果、前回特殊 COM
- 更新前一位置、随机数、洗澡清洁、浴室逐出等状态
- 对被逆推、时间停止、服装还原等状态做善后

### 6.2 关键读写

读取：

- `SELECTCOM`
- `TFLAG:193` / `TFLAG:192` / `TFLAG:194`
- `CFLAG:*:既成事実`
- `CFLAG:*:現在位置`
- `FLAG:時間停止`
- `TFLAG:LastArea`
- `TFLAG:约会道中`

写入：

- `TALENT:*:1` 某些失贞/经验位
- `TFLAG:约会道中`
- `CFLAG:*:膣内射精` 等体液记录
- `CFLAG:*:勃起度２`
- `TFLAG:192 = 0`
- `TFLAG:193 = 0`
- `TFLAG:194 = 0`
- `PREVCOM = SELECTCOM`
- `TFLAG:151 = TFLAG:50`
- `TFLAG:103 = TARGET`
- `TFLAG:150 = ASSIPLAY`
- `TFLAG:移動不能メッセージ = 0`

### 6.3 直接调用到的重要流程

- `CALL ADD_TOUCH_INCREMENT`
- `CALL KOJO_CHECK(...)`
- `CALL KOJO_MESSAGE_SEND(...)`
- `CALL TIMESTOP_RESET`
- `CALL FISHER_YATES_SHAFFLE`
- `CALL 風呂から逐出`

### 6.4 可直接迁移到 erAL 的语义

- 行动后的“状态清理”和“记录前回指令”应独立于主要结算逻辑
- `SELECTCOM` 的前回保存是后续口上、事件和连续动作的重要基础
- 约会途中、移动途中、浴室、时间停止等都是临时状态，而不是长期状态

### 6.5 对 erAL 的实现建议

- 未来补一个 `TurnState` 或 `TransientState`，别把所有临时变量塞进 `WorldState` 顶层
- 把“前回指令 / 前回目标 / 当前途中状态”收口到单独结构

## 7. DATE_CMN 规则矩阵

主入口族：

- `@DATENAME_PLACE`
- `@DATENAME_SPOT`
- `@DATE_SPOT`
- `@DATE_REMAINTIME`
- `@DATE_PARTTIME`
- `@DATE_EVENT`
- `@DATE_EVENT_CHECKSUM`
- `@DATE_EVENT_CONFESSION`
- `@GIFT`
- `@CAN_MAKE_恋人`
- `@ADD_KISS`

### 7.1 主要职责

- 定义约会地点名称、地点编号、剩余时间
- 处理约会后事件
- 处理约会后接吻、告白、送礼和特殊礼物分支
- 处理“能否成为恋人”与“恋人槽位”逻辑

### 7.2 关键读写

读取：

- `CFLAG:MASTER:约会中`
- `TFLAG:约会道中`
- `CFLAG:ARG:デート後イベントフラグ`
- `CFLAG:ARG:合意判定`
- `TALENT:ARG:キス未経験`
- `TALENT:ARG:思慕`
- `TALENT:ARG:恋慕`
- `FLAG:追加恋人枠`
- `FLAG:告白禁止`
- `TFLAG:约会前好感度`

写入：

- `SETBIT CFLAG:ARG:约会後イベントフラグ`
- `SETBIT CFLAG:ARG:既成事実`
- `SETBIT CFLAG:MASTER:既成事実`
- `CHANGE_CFLAG(2, ARG, ...)`
- `CHANGE_CFLAG(4, ARG, ...)`

### 7.3 直接调用到的重要流程

- `CALL GIFT(ARG)`
- `CALL KOJO_MESSAGE_SEND("SP_EVENT", ...)`
- `CALL DATE_EVENT_CONFESSION(ARG)`
- `CALL GIFT_DATE_EVENT(ARG)`
- `CALL EGG_GIFT_DATE_EVENT(ARG)`
- `CALL ADD_KISS(ARG)`
- `CALL AddEXP(...)`

### 7.4 可直接迁移到 erAL 的语义

- 约会结束后有单独的后处理层，不应和普通行动混在一起
- 约会是推进“接吻 / 告白 / 恋人化”的主要载体
- 礼物与约会好感增量联动
- 约会对象和恋人槽位是全局系统，不只是角色局部状态

### 7.5 对 erAL 的实现建议

- 当前 `DateService` 只做状态切换，后续应补 `after_date_event` 层
- 告白、接吻、礼物、誓约都应挂在约会后事件中，而不是普通命令直接完成
- 约会后事件需要独立评分输入，例如地点、好感涨幅、是否送礼、当前阶段

## 8. 直接可用的迁移结论

### 8.1 对系统分层的启发

`eraTW` 的这几份 ERB 可以抽象成四层：

1. `before_turn` / `before_command`
2. `command_available`
3. `after_command`
4. `after_date`

### 8.2 对 erAL 的下一步建议

- [ ] 补 `COMABLE` 的详细规则矩阵
- [ ] 把 `erAL` 当前命令执行管线扩成 `before -> execute -> settle -> after`
- [ ] 给约会系统增加“约会结束后事件”层
- [ ] 让 `FLAG / CFLAG / TFLAG` 中高优先级变量进入结构化运行时模型

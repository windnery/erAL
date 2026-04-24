# erAL 系统规格索引

更新时间：2026-04-24

说明：`specs` 目录当前不是“全部权威真相”，而是“待逐步回写的子系统参考说明”。

## 1. 当前使用方式

1. 先看 [docs/README.md](D:\project\myERA\erAL\docs\README.md)
2. 再看 [docs/TODO.md](D:\project\myERA\erAL\docs\TODO.md)
3. 需要了解某个子系统历史设计和旧约束时，再进入 `specs/*`

## 2. 目前最值得参考的规格

1. `指令系统.md`
2. `结算系统.md`
3. `体力与气力系统.md`
4. `场景上下文系统.md`
5. `事件系统.md`
6. `同行与约会系统.md`

## 3. 当前限制

1. 多份 spec 仍然引用 `commands.toml`，这是旧口径。
2. 当前命令唯一来源已经变成 `data/base/commands/train.toml`。
3. 多份 spec 仍按旧执行模型描述 `CommandService`，不能直接照着改代码。
4. 这些文档可以帮助理解旧设计意图，但不能覆盖 `TODO` 和当前代码。

## 4. 回写顺序

等本轮重构完成以下节点后，再逐步回写 spec：

1. `train.toml` 字段边界冻结
2. `command_effects.toml` 字段边界冻结
3. `CommandService` 执行阶段收束
4. 指令覆盖矩阵建立

## 5. 维护规则

1. 如果某份 spec 仍引用旧字段名，先标记，不要直接拿来驱动实现。
2. 只有在它与当前代码重新对齐后，才把它重新视为受控规格。

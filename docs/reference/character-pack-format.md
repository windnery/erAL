# 角色包格式

## 1. 目的

这份文档定义 `erAL` 当前阶段使用的角色包基础格式。

当前目标不是最终格式，而是：

- 让单角色内容可以独立存放
- 让加载器和校验器有稳定入口
- 让后续继续扩展事件、文本、数值和图片时不返工

## 2. 目录结构

当前推荐结构：

```text
data/base/characters/<character_key>/
  character.toml
  events.toml
  dialogue.toml
```

示例：

```text
data/base/characters/starter_secretary/
  character.toml
  events.toml
  dialogue.toml
```

## 3. `character.toml`

必填字段：

- `key`
- `display_name`
- `initial_location`
- `schedule`

可选字段：

- `tags`

## 4. `events.toml`

当前支持字段：

- `key`
- `action_key`
- `actor_tags`
- `location_keys`
- `time_slots`
- `min_affection`
- `requires_private`

## 5. `dialogue.toml`

当前支持字段：

- `key`
- `actor_key`
- `lines`

规则：

- 事件命中时优先按事件 key 找文本
- 未命中事件时按动作 key 找兜底文本

## 6. 当前约束

1. `character.toml` 必须存在
2. `events.toml` 和 `dialogue.toml` 可以缺省
3. `dialogue.actor_key` 必须和角色包 key 一致
4. `events.action_key` 必须能在命令表里找到
5. `schedule` 和 `events.location_keys` 中引用的地点必须存在

这些规则会由内容校验器检查。

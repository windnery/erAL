# erAL

碧蓝航线主题 era 风格同人游戏，玩法参照 eraTW，使用 Python 实现。

## 运行

需要 Python >= 3.11，无外部依赖。

```bash
# 启动游戏
python -m eral

# 运行测试
python -m unittest discover -s tests -t .
```

## 项目结构

```
src/eral/
  app/        启动与装配
  engine/     通用运行时基础设施
  domain/     港区世界模型（状态、地图、关系）
  systems/    玩法系统（指令、结算、导航、约会、日程等）
  content/    TOML/JSON 静态数据加载
  ui/         表现层（CLI）
  tools/      开发工具（eraTW 轴导入、内容校验）
data/
  base/             手工维护的 TOML 数据（指令、地图、角色包等）
  generated/        从 eraTW CSV 导入的轴注册表
```

## 核心机制

指令产生 SOURCE → 结算系统将 SOURCE 按 scale 映射到 BASE/PALAM/CFLAG/TFLAG → 关系阶段更新。与 eraTW 的 SOURCE 结算模式一致。

## 致谢

- [eraTW](https://ja.wikipedia.org/wiki/Eramaker) — 玩法设计参考
- [erArk](https://github.com/NicsTrer/erArk) — Python 实现参考

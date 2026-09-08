from game_engine.models.activity import Activity

ACTIVITY_REGISTRY: dict[str, type[Activity]] = {}


def register_activity(cls_name: str):
    """注册活动类的装饰器"""
    def decorator(cls: type[Activity]):
        ACTIVITY_REGISTRY[cls_name] = cls
        return cls
    return decorator


# 放在最后执行，确保 register_activity 已定义，避免循环导入
import game_engine.activities  # 导入所有活动模块以确保它们被注册

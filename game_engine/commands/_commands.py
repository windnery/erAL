REGISTER_CMD = {}
REGISTER_CMD_NAME: dict[str, str] = {}
REGISTER_CAN = {}
REGISTER_CAT: dict[str, str] = {}
REGISTER_NEEDS_TARGET: dict[str, bool] = {}
REGISTER_FRONTEND: dict[str, bool] = {}

def register_cmd(key: str, name: str, cat: str, can=None, needs_target: bool = True, frontend: bool = False):
    '''装饰器：自动把指令注册到字典中
    frontend: 纯前端指令标记，前端直接调用本地回调，不走后端 do_cmd'''
    def decorator(func):
        REGISTER_CMD[key] = func
        REGISTER_CMD_NAME[key] = name
        REGISTER_CAT[key] = cat
        if can:
            REGISTER_CAN[key] = can
        REGISTER_NEEDS_TARGET[key] = needs_target
        if frontend:
            REGISTER_FRONTEND[key] = frontend
        return func
    return decorator

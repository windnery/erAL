REGISTER_CMD = {}
REGISTER_CMD_NAME: dict[str, str] = {}
REGISTER_CAN = {}
REGISTER_CAT: dict[str, str] = {}
REGISTER_NEEDS_TARGET: dict[str, bool] = {}

def register_cmd(key: str, name: str, cat: str, can=None, needs_target: bool = True):
    '''装饰器：自动把指令注册到字典中'''
    def decorator(func):
        REGISTER_CMD[key] = func
        REGISTER_CMD_NAME[key] = name
        REGISTER_CAT[key] = cat
        if can:
            REGISTER_CAN[key] = can
        REGISTER_NEEDS_TARGET[key] = needs_target
        return func
    return decorator

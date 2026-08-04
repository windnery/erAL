REGISTER_CMD = {}
REGISTER_CMD_NAME = {}
REGISTER_CAN = {}
REGISTER_CAT = {}

def register_cmd(key: str, name: str, cat: str, can=None):
    '''装饰器：自动把指令注册到字典中'''
    def decorator(func):
        REGISTER_CMD[key] = func
        REGISTER_CMD_NAME[key] = name
        REGISTER_CAT[key] = cat
        if can:
            REGISTER_CAN[key] = can
        return func
    return decorator

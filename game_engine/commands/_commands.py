REGISTER_CMD = {}
def register_cmd(name: str):
    '''装饰器：自动把指令注册到字典中'''
    def decorator(func):
        REGISTER_CMD[name] = func
        return func
    return decorator

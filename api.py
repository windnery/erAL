from game_engine.managers.AllManager import AllManager


class Api:
    def __init__(self):
        manager = AllManager()
        self.managers = {
            'manager': manager,
            'map_manager': manager.map_manager,
            'command_manager': manager.command_manager,
            'time_manager': manager.time_manager
        }

    def call(self, manager_name: str, func_name: str, *args, **kwargs):
        # 根据函数名调用对应的函数
        manager = self.managers.get(manager_name)

        if not manager:
            raise ValueError(f"'{manager_name}'未找到")
        func = getattr(manager, func_name, None)
        if not func:
            raise ValueError(f"'{func_name}'未找到")
        
        return func(*args, **kwargs)




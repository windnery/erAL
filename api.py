from world import World


class Api:
    def __init__(self):
        world = World()
        self.managers = {
            'world': world,
            'map_manager': world.map_manager,
            'command_manager': world.command_manager,
            'time_manager': world.time_manager,
            'save_manager': world.save_manager,
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




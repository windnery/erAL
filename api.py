from game_engine.logging_config import (
    clear_runtime_context,
    report_crash,
    report_frontend_error,
    set_runtime_context,
)
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
            'skin_manager': world.skin_manager,
            'item_manager': world.item_manager,
            'train_manager': world.train_manager,
            'event_manager': world.event_manager,
        }

    def call(self, manager_name: str, func_name: str, *args, **kwargs):
        """Dispatch a webview call and report backend failures before re-raising."""
        set_runtime_context(
            api_manager=manager_name,
            api_function=func_name,
            api_argument_count=len(args) + len(kwargs),
        )
        try:
            manager = self.managers.get(manager_name)
            if manager is None:
                raise ValueError(f'{manager_name!r} not found')

            func = getattr(manager, func_name, None)
            if func is None or not callable(func):
                raise ValueError(f'{func_name!r} not found on {manager_name!r}')

            return func(*args, **kwargs)
        except Exception as error:
            report_crash(error, source='api.call')
            raise
        finally:
            clear_runtime_context()

    def report_frontend_error(
        self,
        message,
        source='',
        line=None,
        column=None,
        stack='',
    ):
        """Receive an unhandled browser error from the pywebview frontend."""
        return report_frontend_error(
            message,
            source=source,
            line=line,
            column=column,
            stack=stack,
        )

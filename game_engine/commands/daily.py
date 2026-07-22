from game_engine.commands._commands import register_cmd
from data.time.time_data import daily_time_data

@register_cmd('nap')
def nap(manager, option=None):
    '''小睡'''
    # TODO: 实现小睡功能
    # 推进时间
    manager.time_manager.advance_time(daily_time_data['nap'])
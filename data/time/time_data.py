from data.data_loader import *

LEAVE_TIME_DATA: dict[str, dict[str, int]] = load_leave_time()  # 加载离开时间
COMMAND_TIME_DATA = load_command_time()  # 加载日常指令时间
COMMAND_COOLDOWN_DATA = load_command_cooldown()  # 加载日常指令冷却时间

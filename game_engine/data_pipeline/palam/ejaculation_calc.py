from config.palam_config import EJACULATION_THRESHOLD
from game_engine.models.player import Player


def ejaculation_check(player: Player) -> bool:
    """返回是否射精"""
    return any(player.palam.get(k, 0) >= EJACULATION_THRESHOLD for k in
               ['m_pleasure_palam', 'c_pleasure_palam', 'b_pleasure_palam', 'a_pleasure_palam', 'v_pleasure_palam'])

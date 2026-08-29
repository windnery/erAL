"""游戏设置模块：管理开局设置与各项系统配置"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game_engine.models.player import Player
    from world import World

# 初始数值常量与上下限范围
STAMINA_MIN: int = 1800
STAMINA_MAX: int = 2500
DEFAULT_STAMINA: int = 2000

ENERGY_MIN: int = 1800
ENERGY_MAX: int = 2500
DEFAULT_ENERGY: int = 2000

DEFAULT_PLAYER_NAME: str = "指挥官"


class SettingManager:
    """设置管理器：负责开局参数配置校验、属性应用及系统配置项管理"""

    def __init__(self, world: World | None = None):
        self.world = world

    def get_initial_setting_defs(self) -> dict[str, Any]:
        """获取开局可配置项的默认值及上下限范围"""
        return {
            'default_name': DEFAULT_PLAYER_NAME,
            'stamina_min': STAMINA_MIN,
            'stamina_max': STAMINA_MAX,
            'default_stamina': DEFAULT_STAMINA,
            'energy_min': ENERGY_MIN,
            'energy_max': ENERGY_MAX,
            'default_energy': DEFAULT_ENERGY,
        }

    def validate_and_apply_initial_settings(
        self,
        player: Player,
        name: str | None = None,
        max_stamina: int | None = None,
        max_energy: int | None = None,
    ) -> dict[str, Any]:
        """校验并应用玩家开局设置至指定的 Player 实例"""
        # 姓名校验与清洗
        if name is not None and str(name).strip():
            clean_name = str(name).strip()
        else:
            clean_name = DEFAULT_PLAYER_NAME

        # 体力上限校验与区间限制
        try:
            stamina_val = int(max_stamina) if max_stamina is not None else DEFAULT_STAMINA
        except (ValueError, TypeError):
            stamina_val = DEFAULT_STAMINA
        stamina_val = max(STAMINA_MIN, min(STAMINA_MAX, stamina_val))

        # 气力上限校验与区间限制
        try:
            energy_val = int(max_energy) if max_energy is not None else DEFAULT_ENERGY
        except (ValueError, TypeError):
            energy_val = DEFAULT_ENERGY
        energy_val = max(ENERGY_MIN, min(ENERGY_MAX, energy_val))

        # 应用至玩家属性
        player.name = clean_name
        player.base['max_stamina'] = stamina_val
        player.base['stamina'] = stamina_val
        player.base['max_energy'] = energy_val
        player.base['energy'] = energy_val

        return {
            'success': True,
            'name': player.name,
            'max_stamina': stamina_val,
            'max_energy': energy_val,
        }

    def apply_initial_settings(
        self,
        name: str | None = None,
        max_stamina: int | None = None,
        max_energy: int | None = None,
    ) -> dict[str, Any]:
        """通过 API 调用的开局设置入口，直接应用至当前世界的玩家"""
        if self.world is None or getattr(self.world, 'player', None) is None:
            raise ValueError('World 或 Player 尚未初始化，无法应用开局设置')
        return self.validate_and_apply_initial_settings(
            player=self.world.player,
            name=name,
            max_stamina=max_stamina,
            max_energy=max_energy,
        )

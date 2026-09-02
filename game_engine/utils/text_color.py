"""文本颜色格式化工具库 (Text Color Formatting Utility)

提供全局统一的语义化颜色包装函数，避免在业务代码中硬编码十六进制颜色字符串。
格式遵循前端解析协议：[[c:#RRGGBB]]内容[[/c]]
"""

from typing import Final


class Palette:
    """港区全局统一设计调色板 (HEX 颜色常量)"""
    # 素质 / 关系 / 绝顶高潮 (粉色系)
    SEX_TALENT: Final[str] = '#ff6fae'
    ORGASM: Final[str] = '#ff6fae'

    # 一般素质 / 能力提升 / 刻印获取 / 焦点地点 / 主导权 (橙黄/金色系)
    COMMON_TALENT: Final[str] = '#ffd400'
    ABL: Final[str] = '#ffd400'
    MARK: Final[str] = '#ffd400'
    LOCATION: Final[str] = '#ffd400'
    INITIATIVE: Final[str] = '#ffd400'

    # 成功 / 良好 / 负面清除 (翠绿色系)
    SUCCESS: Final[str] = '#50c878'
    RECOVER: Final[str] = '#50c878'

    # 提示
    NOTICE: Final[str] = '#ffd400'

    # 危险 / 严重惩罚 / 超标 (红色系)
    DANGER: Final[str] = '#ff0000'

    # 射精 / 纯白高亮 (纯白/亮白系)
    EJACULATION: Final[str] = '#f5f5f5'

    # 次要信息 / 数值消耗 (浅灰色系)
    MUTED: Final[str] = '#999999'


def color_text(text: str, hex_color: str) -> str:
    """底层颜色标签拼装函数：[[c:{hex_color}]]{text}[[/c]]"""
    return f"[[c:{hex_color}]]{text}[[/c]]"


def c_talent(text: str, talent_type: str = "sex") -> str:
    """素质 / 关系改变高亮（粉色）"""
    if talent_type == "sex":
        return color_text(text, Palette.SEX_TALENT)
    else:
        return color_text(text, Palette.COMMON_TALENT)


def c_orgasm(text: str) -> str:
    """绝顶 / 高潮相关文案（粉色）"""
    return color_text(text, Palette.ORGASM)


def c_abl(text: str) -> str:
    """ABL 能力升级高亮（橙黄色）"""
    return color_text(text, Palette.ABL)


def c_mark(text: str) -> str:
    """刻印获取高亮（橙黄色）"""
    return color_text(text, Palette.MARK)


def c_loc(text: str) -> str:
    """地点 / 地图节点高亮（橙黄色）"""
    return color_text(text, Palette.LOCATION)


def c_initiative(text: str) -> str:
    """主导权变动高亮（橙黄色）"""
    return color_text(text, Palette.INITIATIVE)


def c_success(text: str) -> str:
    """成功 / 良好 / 负面刻印清除高亮（翠绿色）"""
    return color_text(text, Palette.SUCCESS)


def c_notice(text: str) -> str:
    """提示高亮（橙黄色）"""
    return color_text(text, Palette.NOTICE)


def c_danger(text: str) -> str:
    """危险 / 严重惩罚 / 昏倒高亮（红色）"""
    return color_text(text, Palette.DANGER)


def c_ejaculation(text: str) -> str:
    """射精文案高亮（亮白色）"""
    return color_text(text, Palette.EJACULATION)


def c_muted(text: str) -> str:
    """次要信息 / 数值扣减（浅灰色）"""
    return color_text(text, Palette.MUTED)


def c_chara(text: str, chara_color: str) -> str:
    """角色专属台词 / 姓名高亮"""
    return color_text(text, chara_color)

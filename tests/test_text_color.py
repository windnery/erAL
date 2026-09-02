# -*- coding: utf-8 -*-
"""文本颜色格式化工具模块测试"""

from game_engine.utils.text_color import (
    Palette,
    color_text,
    c_talent,
    c_orgasm,
    c_abl,
    c_mark,
    c_loc,
    c_initiative,
    c_success,
    c_danger,
    c_notice,
    c_ejaculation,
    c_muted,
    c_chara,
)


class TestTextColor:
    def test_color_text_base(self):
        """基础颜色拼接格式符合前端规范"""
        assert color_text("测试", "#123456") == "[[c:#123456]]测试[[/c]]"

    def test_semantic_helpers(self):
        """语义化函数正确绑定对应调色板色号"""
        assert c_talent("[恋人]") == f"[[c:{Palette.SEX_TALENT}]][恋人][[/c]]"
        assert c_talent("[献身]", talent_type="common") == f"[[c:{Palette.COMMON_TALENT}]][献身][[/c]]"
        assert c_orgasm("强绝顶！") == f"[[c:{Palette.ORGASM}]]强绝顶！[[/c]]"
        assert c_abl("亲密提升到1") == f"[[c:{Palette.ABL}]]亲密提升到1[[/c]]"
        assert c_mark("获得苦痛刻印") == f"[[c:{Palette.MARK}]]获得苦痛刻印[[/c]]"
        assert c_loc("指挥室") == f"[[c:{Palette.LOCATION}]]指挥室[[/c]]"
        assert c_initiative("主导权+5") == f"[[c:{Palette.INITIATIVE}]]主导权+5[[/c]]"
        assert c_success("完全失去失望刻印") == f"[[c:{Palette.SUCCESS}]]完全失去失望刻印[[/c]]"
        assert c_notice("提示信息") == f"[[c:{Palette.NOTICE}]]提示信息[[/c]]"
        assert c_danger("会话疲劳超标") == f"[[c:{Palette.DANGER}]]会话疲劳超标[[/c]]"
        assert c_ejaculation("射精了") == f"[[c:{Palette.EJACULATION}]]射精了[[/c]]"
        assert c_muted("体力-20") == f"[[c:{Palette.MUTED}]]体力-20[[/c]]"
        assert c_chara("拉菲台词", "#ffffff") == "[[c:#ffffff]]拉菲台词[[/c]]"

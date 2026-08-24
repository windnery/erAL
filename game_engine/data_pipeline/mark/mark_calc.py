from __future__ import annotations

from typing import TYPE_CHECKING

from config.mark_config import MARK_PAIN, MARK_SUBMISSION, MARK_DISAPPOINTMENT
from game_engine.models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from game_engine.commands._context import CommandContext


def mark_calc(source: dict[str, int], chara: ShipGirl, ctx: CommandContext):
    """刻印获取
    苦痛、屈服、失望使用该函数计算"""
    # 苦痛
    if chara.mark['pain_mark'] < 3:
        pain_source = source['pain_source']
        for lv, threshold in MARK_PAIN.items():
            if pain_source >= threshold and chara.mark['pain_mark'] < lv:
                chara.mark['pain_mark'] = lv
                
                ctx.say_block('palam', f'[[c:#ffd400]]{chara.name}获得了苦痛刻印lv{lv}！[[/c]]')
    # 屈服
    if chara.mark['submission_mark'] < 3:
        submission_source = source['submission_source']
        obedience_source = source['obedience_source']
        src = submission_source + obedience_source
        for lv, threshold in MARK_SUBMISSION.items():
            if src >= threshold and chara.mark['submission_mark'] < lv:
                chara.mark['submission_mark'] = lv
                ctx.say_block('palam', f'[[c:#ffd400]]{chara.name}获得了屈服刻印lv{lv}！[[/c]]')
    # 失望
    if chara.mark['disappointment_mark'] < 3:
        disgust_source = source['disgust_source']
        fear_source = source['fear_source']
        depression_source = source['depression_source']
        src = disgust_source + fear_source + depression_source

        for lv, threshold in MARK_DISAPPOINTMENT.items():
            if src >= threshold and chara.mark['disappointment_mark'] < lv:
                chara.mark['disappointment_mark'] = lv
                ctx.say_block('palam', f'[[c:#ffd400]]{chara.name}获得了失望刻印lv{lv}！[[/c]]')

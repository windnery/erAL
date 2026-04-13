"""Semantic access layer for eraTW compat axes."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.stat_axes import AxisFamily
from eral.content.tw_axis_registry import TwAxisRegistry


class ABLKey:
    C_SENSE = "c_sense"
    V_SENSE = "v_sense"
    A_SENSE = "a_sense"
    B_SENSE = "b_sense"
    M_SENSE = "m_sense"
    INTIMACY = "intimacy"
    OBEDIENCE = "obedience"
    DESIRE = "desire"
    MASTURBATION_ADDICTION = "masturbation_addiction"
    SEMEN_ADDICTION = "semen_addiction"
    YURI_ADDICTION = "yuri_addiction"
    MALE_LOVE_ADDICTION = "male_love_addiction"
    VAGINAL_CUM_ADDICTION = "vaginal_cum_addiction"
    ANAL_CUM_ADDICTION = "anal_cum_addiction"
    CLEANING_SKILL = "cleaning_skill"
    TALK_SKILL = "talk_skill"
    COMBAT_ABILITY = "combat_ability"
    CULTURE = "culture"
    COOKING_SKILL = "cooking_skill"
    MUSIC_SKILL = "music_skill"


class TALENTKey:
    VIRGIN = "virgin"
    NON_VIRGIN = "non_virgin"
    SEX = "sex"
    IN_LOVE = "in_love"
    LEWD = "lewd"
    SUBMISSIVE = "submissive"
    KISS_INEXPERIENCED = "kiss_inexperienced"
    LOVER = "lover"
    ADMIRATION = "admiration"
    PREGNANCY_DESIRE = "pregnancy_desire"
    COURAGE = "courage"
    SELF_CONTROL = "self_control"
    INDIFFERENT = "indifferent"
    LOW_EMPATHY = "low_empathy"
    SEXUAL_INTEREST = "sexual_interest"
    CHEERFUL_OR_GLOOMY = "cheerful_or_gloomy"
    LINE_NOT_CROSSED = "line_not_crossed"
    EASY_MASTURBATION = "easy_masturbation"
    ODOR_RESISTANCE = "odor_resistance"
    DEVOTED = "devoted"
    PLEASURE_RESPONSE = "pleasure_response"
    ADDICTION_PRONE = "addiction_prone"
    EASY_ORGASM = "easy_orgasm"
    PERVERSE = "perverse"
    SEXUAL_PREFERENCE = "sexual_preference"
    SADIST = "sadist"
    MASOCHIST = "masochist"
    JEALOUS = "jealous"
    FOX = "fox"
    FOX_SPIRIT = "fox_spirit"
    CHARM = "charm"
    FASCINATION = "fascination"
    MYSTERIOUS_CHARM = "mysterious_charm"


class CFLAGKey:
    AFFECTION = "affection"
    TRUST = "trust"
    ATTITUDE = "attitude"
    OBEDIENCE = "obedience"
    ON_DATE = "on_date"
    SHRINE_RESIDENT = "shrine_resident"
    PREVIOUS_KOJO_STATE = "previous_kojo_state"
    CURRENT_LOCATION = "current_location"
    INITIAL_LOCATION = "initial_location"
    SAME_ROOM = "same_room"
    FOLLOWING = "following"
    FOLLOW_READY = "follow_ready"
    TIME_STOP_ACTION = "time_stop_action"
    HOME_LOCATION = "home_location"


@dataclass(frozen=True, slots=True)
class CompatSemanticEntry:
    family: AxisFamily
    key: str
    era_index: int
    label: str
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CompatSemanticSpec:
    family: AxisFamily
    key: str
    era_index: int
    fallback_label: str


class CompatSemantics:
    def __init__(self, entries: tuple[CompatSemanticEntry, ...]) -> None:
        self._entries = entries
        self._by_family_key = {(entry.family, entry.key): entry for entry in entries}
        by_family_index: dict[tuple[AxisFamily, int], CompatSemanticEntry] = {}
        for entry in entries:
            by_family_index.setdefault((entry.family, entry.era_index), entry)
        self._by_family_index = by_family_index

    def entry(self, family: AxisFamily, key: str) -> CompatSemanticEntry:
        return self._by_family_key[(family, key)]

    def entry_by_index(self, family: AxisFamily, era_index: int) -> CompatSemanticEntry:
        return self._by_family_index[(family, era_index)]

    def entries_for_family(self, family: AxisFamily) -> tuple[CompatSemanticEntry, ...]:
        return tuple(entry for entry in self._entries if entry.family == family)


_DEFAULT_SPECS: tuple[CompatSemanticSpec, ...] = (
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.C_SENSE, 0, "Ｃ感覚"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.V_SENSE, 1, "Ｖ感覚"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.A_SENSE, 2, "Ａ感覚"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.B_SENSE, 3, "Ｂ感覚"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.M_SENSE, 4, "Ｍ感覚"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.INTIMACY, 9, "親密"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.OBEDIENCE, 10, "従順"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.DESIRE, 11, "欲望"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.MASTURBATION_ADDICTION, 30, "自慰中毒"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.SEMEN_ADDICTION, 31, "精液中毒"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.YURI_ADDICTION, 32, "百合中毒"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.MALE_LOVE_ADDICTION, 33, "断袖中毒"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.VAGINAL_CUM_ADDICTION, 34, "膣射中毒"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.ANAL_CUM_ADDICTION, 35, "肛射中毒"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.CLEANING_SKILL, 40, "清掃技能"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.TALK_SKILL, 41, "話術技能"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.COMBAT_ABILITY, 42, "戦闘能力"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.CULTURE, 43, "教養"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.COOKING_SKILL, 44, "料理技能"),
    CompatSemanticSpec(AxisFamily.ABL, ABLKey.MUSIC_SKILL, 45, "音楽技能"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.VIRGIN, 0, "処女"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.NON_VIRGIN, 1, "非童貞"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.SEX, 2, "性別"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.IN_LOVE, 3, "恋慕"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.LEWD, 4, "淫乱"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.SUBMISSIVE, 5, "服従"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.KISS_INEXPERIENCED, 6, "キス未経験"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.LOVER, 7, "恋人"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.ADMIRATION, 8, "思慕"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.PREGNANCY_DESIRE, 9, "妊娠願望"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.COURAGE, 10, "胆量"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.SELF_CONTROL, 20, "自制心"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.INDIFFERENT, 21, "冷漠"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.LOW_EMPATHY, 22, "感情缺乏"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.SEXUAL_INTEREST, 23, "性的兴趣"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.CHEERFUL_OR_GLOOMY, 24, "开朗／阴郁"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.LINE_NOT_CROSSED, 25, "一線越えない"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.EASY_MASTURBATION, 60, "自慰しやすい"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.ODOR_RESISTANCE, 61, "汚臭耐性"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.DEVOTED, 62, "献身的"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.PLEASURE_RESPONSE, 70, "快感応答"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.ADDICTION_PRONE, 71, "容易中毒"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.EASY_ORGASM, 72, "容易高潮"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.PERVERSE, 80, "倒錯的"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.SEXUAL_PREFERENCE, 81, "性別嗜好"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.SADIST, 82, "施虐狂"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.MASOCHIST, 83, "受虐狂"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.JEALOUS, 84, "嫉妬"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.FOX, 90, "狐"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.FOX_SPIRIT, 91, "妖狐"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.CHARM, 92, "魅力"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.FASCINATION, 93, "魅惑"),
    CompatSemanticSpec(AxisFamily.TALENT, TALENTKey.MYSTERIOUS_CHARM, 94, "謎之魅力"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.AFFECTION, 2, "好感度"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.TRUST, 4, "信頼度"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.ATTITUDE, 6, "態度"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.OBEDIENCE, 6, "態度"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.ON_DATE, 12, "デート中"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.SHRINE_RESIDENT, 30, "神社在住"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.PREVIOUS_KOJO_STATE, 45, "前回の口上実装状況"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.CURRENT_LOCATION, 300, "現在位置"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.INITIAL_LOCATION, 311, "初期位置"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.SAME_ROOM, 319, "同室"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.FOLLOWING, 320, "同行"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.FOLLOW_READY, 329, "同行準備"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.TIME_STOP_ACTION, 344, "時間停止行動"),
    CompatSemanticSpec(AxisFamily.CFLAG, CFLAGKey.HOME_LOCATION, 358, "自宅位置"),
)


def build_default_compat_semantics(registry: TwAxisRegistry | None = None) -> CompatSemantics:
    entries: list[CompatSemanticEntry] = []
    for spec in _DEFAULT_SPECS:
        label = spec.fallback_label
        notes = None
        if registry is not None:
            raw_entry = registry.get_by_index(spec.family, spec.era_index)
            label = raw_entry.label
            notes = raw_entry.notes
        entries.append(
            CompatSemanticEntry(
                family=spec.family,
                key=spec.key,
                era_index=spec.era_index,
                label=label,
                notes=notes,
            )
        )
    return CompatSemantics(tuple(entries))


class ActorCompatAccessor:
    def __init__(self, family: AxisFamily, semantics: CompatSemantics) -> None:
        self.family = family
        self.semantics = semantics

    def entry(self, key: str) -> CompatSemanticEntry:
        return self.semantics.entry(self.family, key)

    def get(self, actor, key: str) -> int:
        entry = self.entry(key)
        return getattr(actor.stats.compat, self.family.value).get(entry.era_index)

    def set(self, actor, key: str, value: int) -> None:
        entry = self.entry(key)
        getattr(actor.stats.compat, self.family.value).set(entry.era_index, value)

    def add(self, actor, key: str, delta: int) -> int:
        entry = self.entry(key)
        return getattr(actor.stats.compat, self.family.value).add(entry.era_index, delta)


_default_semantics = build_default_compat_semantics()
actor_abl = ActorCompatAccessor(AxisFamily.ABL, _default_semantics)
actor_talent = ActorCompatAccessor(AxisFamily.TALENT, _default_semantics)
actor_cflag = ActorCompatAccessor(AxisFamily.CFLAG, _default_semantics)


__all__ = [
    "ABLKey",
    "ActorCompatAccessor",
    "CFLAGKey",
    "CompatSemanticEntry",
    "CompatSemantics",
    "TALENTKey",
    "actor_abl",
    "actor_cflag",
    "actor_talent",
    "build_default_compat_semantics",
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步与生成全部舰娘的皮肤定义文件 (data/skins/*.json)
严格对标 data/skins/拉菲.json 结构与碧蓝航线官方中文皮肤命名/价格标准
"""

import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PORTRAITS_DIR = os.path.join(PROJECT_ROOT, 'frontend', 'assets', 'portraits')
AVATARS_DIR = os.path.join(PROJECT_ROOT, 'frontend', 'assets', 'avatars')
SKINS_DIR = os.path.join(PROJECT_ROOT, 'data', 'skins')

# 碧蓝航线官方中文皮肤名称映射
OFFICIAL_SKIN_NAMES = {
    # 原始与改造
    'default': '原始皮肤',
    
    # Z23
    'Z23_default': '原始皮肤',
    'Z23_retrofit': 'Z23·改',
    'Z23_schwarze_hochzeit': '黑曜的嫁衣',
    'Z23_philosophy_sensei': '哲学讲师',
    "Z23_the_banquet's_honor_student": '宴会优等生',
    'Z23_breezy_doubles': '混双活力？',
    'Z23_cafe_trainee_new_base': '咖啡馆店员？',
    'Z23_inky_antics': '墨香砚彩',
    'Z23_keeper_of_the_comf-fort': '秘密的“基地”',
    'Z23_perfect_smile': '完美微笑',
    'Z23_serious_idol_acting_manager': '严肃偶像·兼职经纪人',
    'Z23_tanz_der_blumen': '丽华微醺',
    'Z23_the_eyecatch_in_the_rye': '麦田的目光抓捕者',
    'Z23_upgrade_failure': '强化失败？！',

    # 标枪
    'javelin_default': '原始皮肤',
    'javelin_retrofit': '标枪·改',
    'javelin_blissful_purity': '幸福纯白',
    'javelin_beach_picnic': '沙滩野餐会',
    'javelin_a_different_dance': '一起跳舞吧！',
    'javelin_a_legend_is_born': '传说诞生？！',
    'javelin_energetic_idol_120%_motivation': '元气偶像·120%起动',
    "javelin_let's_become_waitresses": '一起成为服务生！',
    'javelin_operation_pillow_fight': '枕头大战！',
    'javelin_slow_ahead': '微速前进！',

    # 绫波
    'ayanami_default': '原始皮肤',
    'ayanami_retrofit': '绫波·改',
    "ayanami_demon's_finest_dress": '鬼神之华裳',
    'ayanami_witch_in_ambush': '待机魔女',
    "ayanami_rock_'n'_demon": "Rock'n'Demon",
    'ayanami_pulse_of_the_new_year': '新年的愿望',
    'ayanami_off-duty_battles_station_gear': '战舰式下班装备',
    'ayanami_nightfall_raiment': '暗夜之华',
    'ayanami_lunar_demon': '黯然礼装',
    'ayanami_low-key_idol_confused': '微速偶像·困惑中',
    'ayanami_grade_a_sailor_uniform': '优等生水手服',
    'ayanami_dynasty_shipgirl': '华美之极',
    'ayanami_dynamic_kick': '跃动飞踢！',
    'ayanami_disarming_deep_blue': '冷冽的幻梦',
    'ayanami_covert_ops_cloak': '特别潜入装束',
    'ayanami_cola_fills_you_with_determination': '可乐能让人精神百倍！',

    # 拉菲
    'laffey_default': '原始皮肤',
    'laffey_retrofit': '拉菲·改',
    "laffey_white_rabbit's_oath": '拉菲·誓约',
    'laffey_snow_rabbit_and_candy_apple': '雪兔与苹果糖',
    'laffey_bunny_clerk': '兔兔店员？',
    'laffey_bunny_idol_unmotivated': '兔兔偶像·提不起劲',
    'laffey_lazy_days': '白日慵懒',
    'laffey_picnic_adventure': '野餐奇遇？',
    'laffey_sleep_to_clean_another_day': '大扫除的始末',
    'laffey_sleepageddon': '末日沉眠……',
    'laffey_sleepy_teriyaki_twister': '鸡肉卷，还有倦意……',
    'laffey_white_rabbit_welcomes_the_spring': '白兔迎春',

    # 明石
    'akashi_default': '原始皮肤',
    "akashi_akashi's_in_the_red": '明石在赤字中！',
    'akashi_the_black_cat_cometh': '黑猫来袭！',
    'akashi_welcome_to_azurcon': '欢迎来到AzurCon！',
    'akashi_welcome_to_sofmap': '欢迎光临Sofmap！',
    "akashi_white_cat's_repayment": '白猫的报恩',

    # 不知火
    'shiranui_default': '原始皮肤',
    'shiranui_retrofit': '不知火·改',
    'shiranui_mooncake_merchant': '月饼贩售中！',

    # 小天鹅
    'cygnet_default': '原始皮肤',
    'cygnet_retrofit': '小天鹅·改',
    'cygnet_an_offer_to_be_maid': '女仆体验周',
    "cygnet_holy_night's_hymn": '圣夜的赞美诗',
    'cygnet_royal_fanfare': '皇家应援曲',
    'cygnet_sea_star_on_shore': '滨海的星之梦',
    'cygnet_winter_date': '冬日约会',

    # 俄克拉荷马
    'oklahoma_default': '原始皮肤',
    'oklahoma_retrofit': '俄克拉荷马·改',
    'oklahoma_piratey_transformation': '变身！海盗女孩！',

    # 内华达
    'nevada_default': '原始皮肤',
    'navada_retrofit': '内华达·改',
    'nevada_a_magnificent_banquet': '华贵的宴会',

    # 卡辛
    'cassin_default': '原始皮肤',
    'cassin_retrofit': '卡辛·改',
    'cassin_shopping_carte_blanche': '购物随心所欲？',

    # 唐斯
    'downes_default': '原始皮肤',
    'downes_retrofit': '唐斯·改',
    'downes_part-time_bomber': '兼职轰炸机',
}

# 默认皮肤价格
SKIN_PRICES = {
    'Z23_breezy_doubles': 880,
    'Z23_tanz_der_blumen': 880,
    'Z23_the_banquet\'s_honor_student': 800,
    'Z23_philosophy_sensei': 780,
    'Z23_cafe_trainee_new_base': 700,
    'Z23_inky_antics': 780,
    'Z23_keeper_of_the_comf-fort': 800,
    'Z23_perfect_smile': 800,
    'Z23_serious_idol_acting_manager': 800,
    'Z23_the_eyecatch_in_the_rye': 800,

    'javelin_a_different_dance': 880,
    'javelin_a_legend_is_born': 880,
    'javelin_beach_picnic': 800,
    'javelin_energetic_idol_120%_motivation': 800,
    "javelin_let's_become_waitresses": 700,
    'javelin_operation_pillow_fight': 780,

    'ayanami_nightfall_raiment': 880,
    'ayanami_dynasty_shipgirl': 880,
    'ayanami_dynamic_kick': 880,
    'ayanami_witch_in_ambush': 780,
    "ayanami_rock_'n'_demon": 800,
    'ayanami_pulse_of_the_new_year': 800,
    'ayanami_off-duty_battles_station_gear': 800,
    'ayanami_lunar_demon': 800,
    'ayanami_low-key_idol_confused': 800,
    'ayanami_grade_a_sailor_uniform': 780,
    'ayanami_disarming_deep_blue': 800,
    'ayanami_covert_ops_cloak': 800,

    'laffey_snow_rabbit_and_candy_apple': 1000,
    'laffey_bunny_clerk': 700,
    'laffey_bunny_idol_unmotivated': 800,
    'laffey_lazy_days': 800,
    'laffey_sleep_to_clean_another_day': 800,
    'laffey_sleepageddon': 780,
    'laffey_sleepy_teriyaki_twister': 700,
    'laffey_white_rabbit_welcomes_the_spring': 1080,

    "akashi_akashi's_in_the_red": 800,
    'akashi_the_black_cat_cometh': 780,
    'akashi_welcome_to_azurcon': 800,
    'akashi_welcome_to_sofmap': 780,

    'shiranui_mooncake_merchant': 780,

    'cygnet_an_offer_to_be_maid': 780,
    "cygnet_holy_night's_hymn": 780,
    'cygnet_royal_fanfare': 800,
    'cygnet_sea_star_on_shore': 800,
    'cygnet_winter_date': 780,

    'oklahoma_piratey_transformation': 780,
    'nevada_a_magnificent_banquet': 800,
    'cassin_shopping_carte_blanche': 700,
    'downes_part-time_bomber': 700,
}

# 明确为非售卖/活动获取的皮肤列表
NON_SALE_SKINS = {
    'Z23_upgrade_failure',
    'javelin_slow_ahead',
    'ayanami_cola_fills_you_with_determination',
    'laffey_picnic_adventure'
}


def build_skin_entry(chara_name, skin_id):
    """构建单个皮肤对象的 JSON 数据字典"""
    avatar_rel = f"frontend/assets/avatars/{chara_name}/{skin_id}.webp"
    portrait_rel = f"frontend/assets/portraits/{chara_name}/{skin_id}.webp"

    # 1. 原始默认皮肤
    if skin_id.endswith('_default'):
        return {
            "default": True,
            "name": "原始皮肤",
            "avatar": avatar_rel,
            "portrait": portrait_rel
        }

    # 2. 改造皮肤
    if 'retrofit' in skin_id:
        name = OFFICIAL_SKIN_NAMES.get(skin_id, f"{chara_name}·改")
        return {
            "retrofit": True,
            "name": name,
            "avatar": avatar_rel,
            "portrait": portrait_rel
        }

    # 3. 誓约皮肤 (婚纱)
    if 'oath' in skin_id or 'hochzeit' in skin_id or 'purity' in skin_id or "demon's_finest_dress" in skin_id or "white_cat's_repayment" in skin_id:
        name = OFFICIAL_SKIN_NAMES.get(skin_id, f"{chara_name}·誓约")
        return {
            "oath": True,
            "name": name,
            "avatar": avatar_rel,
            "portrait": portrait_rel
        }

    # 4. 普通商城在售/活动皮肤
    name = OFFICIAL_SKIN_NAMES.get(skin_id, skin_id)
    is_sale = skin_id not in NON_SALE_SKINS
    price = SKIN_PRICES.get(skin_id, 800)

    if is_sale:
        return {
            "is_sale": True,
            "price": price,
            "name": name,
            "avatar": avatar_rel,
            "portrait": portrait_rel
        }
    else:
        return {
            "is_sale": False,
            "name": name,
            "avatar": avatar_rel,
            "portrait": portrait_rel
        }


def sync_all_skins():
    os.makedirs(SKINS_DIR, exist_ok=True)
    
    char_dirs = sorted(os.listdir(PORTRAITS_DIR))
    total_chars = 0
    total_skins = 0

    print("=" * 65)
    print(" 开始全量同步所有角色的皮肤定义文件 (data/skins/*.json)")
    print("=" * 65)

    for chara in char_dirs:
        p_char_dir = os.path.join(PORTRAITS_DIR, chara)
        if not os.path.isdir(p_char_dir):
            continue

        skin_files = sorted([f for f in os.listdir(p_char_dir) if f.endswith('.webp')])
        if not skin_files:
            continue

        chara_skins_data = {}

        # 排序：确保 default 在最前，retrofit 第二，随后按普通皮肤/誓约排布
        def skin_sort_key(f):
            base = os.path.splitext(f)[0]
            if base.endswith('_default'):
                return (0, base)
            if 'retrofit' in base:
                return (1, base)
            if 'oath' in base or 'hochzeit' in base or 'purity' in base or 'repayment' in base:
                return (3, base)
            return (2, base)

        for f in sorted(skin_files, key=skin_sort_key):
            skin_id = os.path.splitext(f)[0]
            chara_skins_data[skin_id] = build_skin_entry(chara, skin_id)
            total_skins += 1

        json_path = os.path.join(SKINS_DIR, f"{chara}.json")
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(chara_skins_data, jf, ensure_ascii=False, indent=2)

        print(f" [+] [写入] {chara:<6} ({len(skin_files):>2} 套皮肤) -> data/skins/{chara}.json")
        total_chars += 1

    print("=" * 65)
    print(f" 同步完成！共生成/更新 {total_chars} 个角色的皮肤定义文件，涵盖 {total_skins} 套皮肤。")
    print("=" * 65)


if __name__ == '__main__':
    sync_all_skins()

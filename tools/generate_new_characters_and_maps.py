#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
erAL 80位新舰娘角色数据与配套宿舍地图自动化生成与更新脚本
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARACTERS_DIR = PROJECT_ROOT / 'data' / 'characters'
MAPS_DIR = PROJECT_ROOT / 'data' / 'maps'
CONFIG_DIR = PROJECT_ROOT / 'config'
TIME_DIR = PROJECT_ROOT / 'data' / 'time'

# 80位新舰娘的角色完整数据定义表
NEW_CHARACTERS_DATA = [
    # ==================== 白鹰 (Eagle Union, alignment="0") ====================
    {
        "id": "enterprise", "name": "企业", "color": "#7B90A7", "region": "eagle_union_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "self_control": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1", "charm": "1"}
    },
    {
        "id": "cleveland", "name": "克利夫兰", "color": "#FFB800", "region": "eagle_union_dorm",
        "stamina": 1800, "energy": 1750, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0", "charm": "1"}
    },
    {
        "id": "saratoga", "name": "萨拉托加", "color": "#FF99CC", "region": "eagle_union_dorm",
        "stamina": 1900, "energy": 1850, "ship_type": "4", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "innocent": "1", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-1", "charm": "1"}
    },
    {
        "id": "lexington", "name": "列克星敦", "color": "#B0C4DE", "region": "eagle_union_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "0", "charm": "1"}
    },
    {
        "id": "yorktown", "name": "约克城", "color": "#708090", "region": "eagle_union_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "morose": "1", "devoted": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0", "charm": "1"}
    },
    {
        "id": "hornet", "name": "大黄蜂", "color": "#FFA500", "region": "eagle_union_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1", "charm": "1"}
    },
    {
        "id": "san_diego", "name": "圣地亚哥", "color": "#FF6347", "region": "eagle_union_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "innocent": "1", "bright": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0", "charm": "2"}
    },
    {
        "id": "helena", "name": "海伦娜", "color": "#87CEEB", "region": "eagle_union_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "devoted": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0", "charm": "1"}
    },
    {
        "id": "eldridge", "name": "埃尔德里奇", "color": "#9370DB", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "emotional_deficiency": "1", "female_body": "-1", "bra_size": "-2", "hip_size": "-2", "wine_tolerance": "-2"}
    },
    {
        "id": "hammann", "name": "哈曼", "color": "#F08080", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "tsundere": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "arizona", "name": "亚利桑那", "color": "#D8BFD8", "region": "eagle_union_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "0",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "morose": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "pennsylvania", "name": "宾夕法尼亚", "color": "#4682B4", "region": "eagle_union_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1"}
    },
    {
        "id": "south_dakota", "name": "南达科他", "color": "#8B4513", "region": "eagle_union_dorm",
        "stamina": 2150, "energy": 1800, "ship_type": "3", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "1"}
    },
    {
        "id": "california", "name": "加利福尼亚", "color": "#E6E6FA", "region": "eagle_union_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "tennessee", "name": "田纳西", "color": "#696969", "region": "eagle_union_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "0",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1"}
    },
    {
        "id": "portland", "name": "波特兰", "color": "#BA55D3", "region": "eagle_union_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "indianapolis", "name": "印第安纳波利斯", "color": "#4169E1", "region": "eagle_union_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "0",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "emotional_deficiency": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "-1"}
    },
    {
        "id": "chicago", "name": "芝加哥", "color": "#DC143C", "region": "eagle_union_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "sexual_interest": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "1", "charm": "1"}
    },
    {
        "id": "houston", "name": "休斯敦", "color": "#FF7F50", "region": "eagle_union_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "wichita", "name": "威奇塔", "color": "#B22222", "region": "eagle_union_dorm",
        "stamina": 1900, "energy": 1750, "ship_type": "2", "alignment": "0",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1"}
    },
    {
        "id": "northampton", "name": "北安普敦", "color": "#483D8B", "region": "eagle_union_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "brooklyn", "name": "布鲁克林", "color": "#5F9EA0", "region": "eagle_union_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "atlanta", "name": "亚特兰大", "color": "#20B2AA", "region": "eagle_union_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "juneau", "name": "朱诺", "color": "#B0E0E6", "region": "eagle_union_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "morose": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "-1"}
    },
    {
        "id": "phoenix", "name": "菲尼克斯", "color": "#FF4500", "region": "eagle_union_dorm",
        "stamina": 1800, "energy": 1700, "ship_type": "1", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "vestal", "name": "女灶神", "color": "#3CB371", "region": "eagle_union_dorm",
        "stamina": 1650, "energy": 1700, "ship_type": "6", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "fletcher", "name": "弗莱彻", "color": "#8FBC8F", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "-1"}
    },
    {
        "id": "thatcher", "name": "撒切尔", "color": "#FFD700", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "charles_ausburne", "name": "查尔斯·奥斯本", "color": "#FF8C00", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "gridley", "name": "格里德利", "color": "#DAA520", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "maury", "name": "莫里", "color": "#00CED1", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "sims", "name": "西姆斯", "color": "#FF69B4", "region": "eagle_union_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "0",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "long_island", "name": "长岛", "color": "#DDA0DD", "region": "eagle_union_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "8", "alignment": "0",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },

    # ==================== 皇家 (Royal Navy, alignment="6") ====================
    {
        "id": "queen_elizabeth", "name": "伊丽莎白女王", "color": "#FFD700", "region": "royal_dorm",
        "stamina": 2050, "energy": 1800, "ship_type": "3", "alignment": "6",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "tsundere": "1", "female_body": "-1", "bra_size": "-2", "hip_size": "-1", "wine_tolerance": "-1", "charm": "1"}
    },
    {
        "id": "warspite", "name": "厌战", "color": "#4682B4", "region": "royal_dorm",
        "stamina": 2150, "energy": 1800, "ship_type": "3", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "0", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "1", "charm": "1"}
    },
    {
        "id": "hood", "name": "胡德", "color": "#DAA520", "region": "royal_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "11", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "self_control": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1", "charm": "2"}
    },
    {
        "id": "illustrious", "name": "光辉", "color": "#FFFFFF", "region": "royal_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "0", "charm": "2"}
    },
    {
        "id": "unicorn", "name": "独角兽", "color": "#E6E6FA", "region": "royal_dorm",
        "stamina": 1700, "energy": 1650, "ship_type": "8", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "sense_of_shame": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "ark_royal", "name": "皇家方舟", "color": "#8B0000", "region": "royal_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1"}
    },
    {
        "id": "nelson", "name": "纳尔逊", "color": "#B22222", "region": "royal_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "6",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "tsundere": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "rodney", "name": "罗德尼", "color": "#FFC0CB", "region": "royal_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "0", "charm": "1"}
    },
    {
        "id": "renown", "name": "声望", "color": "#C0C0C0", "region": "royal_dorm",
        "stamina": 2050, "energy": 1800, "ship_type": "11", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "repulse", "name": "反击", "color": "#ADD8E6", "region": "royal_dorm",
        "stamina": 2050, "energy": 1800, "ship_type": "11", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "york", "name": "约克", "color": "#9400D3", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "1", "self_respect": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "exeter", "name": "埃克塞特", "color": "#4169E1", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "self_control": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "london", "name": "伦敦", "color": "#778899", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "learning_ability": "1", "devoted": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "suffolk", "name": "萨福克", "color": "#FFB6C1", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "female_body": "0", "bra_size": "2", "hip_size": "1", "wine_tolerance": "-1"}
    },
    {
        "id": "norfolk", "name": "诺福克", "color": "#B0C4DE", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "sense_of_shame": "1", "female_body": "0", "bra_size": "1", "hip_size": "0", "wine_tolerance": "-1"}
    },
    {
        "id": "kent", "name": "肯特", "color": "#FF8C00", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "shropshire", "name": "什罗普郡", "color": "#FFA07A", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "dorsetshire", "name": "多塞特郡", "color": "#483D8B", "region": "royal_dorm",
        "stamina": 1850, "energy": 1750, "ship_type": "2", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "galatea", "name": "加拉蒂亚", "color": "#98FB98", "region": "royal_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "arethusa", "name": "阿瑞托莎", "color": "#87CEFA", "region": "royal_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "6",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "tsundere": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "ajax", "name": "阿贾克斯", "color": "#FF1493", "region": "royal_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "6",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "sadism": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "1", "charm": "1"}
    },
    {
        "id": "achilles", "name": "阿基里斯", "color": "#32CD32", "region": "royal_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "amazon", "name": "女将", "color": "#FF4500", "region": "royal_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "6",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "tsundere": "1", "female_body": "-1", "bra_size": "-2", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "juno", "name": "天后", "color": "#F5DEB3", "region": "royal_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "fortune", "name": "命运女神", "color": "#E0FFFF", "region": "royal_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "sense_of_shame": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "glowworm", "name": "萤火虫", "color": "#ADFF2F", "region": "royal_dorm",
        "stamina": 1650, "energy": 1550, "ship_type": "0", "alignment": "6",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "bright": "1", "female_body": "-1", "bra_size": "-2", "hip_size": "-2", "wine_tolerance": "-2"}
    },
    {
        "id": "erebus", "name": "黑暗界", "color": "#4B0082", "region": "royal_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "10", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "morose": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "terror", "name": "恐怖", "color": "#2F4F4F", "region": "royal_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "10", "alignment": "6",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "morose": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },

    # ==================== 重樱 (Sakura Empire, alignment="1") ====================
    {
        "id": "akagi", "name": "赤城", "color": "#8B0000", "region": "sakura_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "1",
        "talents": {"courage": "1", "attitude": "1", "response": "1", "self_respect": "1", "sexual_interest": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "1", "charm": "2"}
    },
    {
        "id": "kaga", "name": "加贺", "color": "#191970", "region": "sakura_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "self_control": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "1", "charm": "1"}
    },
    {
        "id": "souryuu", "name": "苍龙", "color": "#4682B4", "region": "sakura_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "self_control": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "hiryuu", "name": "飞龙", "color": "#2E8B57", "region": "sakura_dorm",
        "stamina": 1950, "energy": 1850, "ship_type": "4", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "0"}
    },
    {
        "id": "houshou", "name": "凤翔", "color": "#DEB887", "region": "sakura_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "8", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "1"}
    },
    {
        "id": "shouhou", "name": "祥凤", "color": "#FF6347", "region": "sakura_dorm",
        "stamina": 1700, "energy": 1650, "ship_type": "8", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "takao", "name": "高雄", "color": "#000080", "region": "sakura_dorm",
        "stamina": 1900, "energy": 1750, "ship_type": "2", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "self_control": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "0", "charm": "1"}
    },
    {
        "id": "fusou", "name": "扶桑", "color": "#8B4513", "region": "sakura_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "1",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "0"}
    },
    {
        "id": "yamashiro", "name": "山城", "color": "#D2691E", "region": "sakura_dorm",
        "stamina": 2100, "energy": 1800, "ship_type": "3", "alignment": "1",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "-1"}
    },
    {
        "id": "yuudachi", "name": "夕立", "color": "#DC143C", "region": "sakura_dorm",
        "stamina": 1650, "energy": 1550, "ship_type": "0", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "shigure", "name": "时雨", "color": "#3CB371", "region": "sakura_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "shiratsuyu", "name": "白露", "color": "#20B2AA", "region": "sakura_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },
    {
        "id": "kagerou", "name": "阳炎", "color": "#FF4500", "region": "sakura_dorm",
        "stamina": 1600, "energy": 1550, "ship_type": "0", "alignment": "1",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "bright": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-2"}
    },

    # ==================== 铁血 (Iron Blood, alignment="2") ====================
    {
        "id": "prinz_eugen", "name": "欧根亲王", "color": "#C0C0C0", "region": "ironblood_dorm",
        "stamina": 1900, "energy": 1800, "ship_type": "2", "alignment": "2",
        "talents": {"courage": "1", "attitude": "-1", "response": "1", "self_respect": "1", "sexual_interest": "1", "female_body": "1", "bra_size": "2", "hip_size": "1", "wine_tolerance": "2", "charm": "2"}
    },
    {
        "id": "z1", "name": "Z1", "color": "#708090", "region": "ironblood_dorm",
        "stamina": 1650, "energy": 1550, "ship_type": "0", "alignment": "2",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "bright": "1", "female_body": "0", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "0"}
    },
    {
        "id": "leipzig", "name": "莱比锡", "color": "#D8BFD8", "region": "ironblood_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "2",
        "talents": {"courage": "-1", "attitude": "-1", "response": "-1", "self_respect": "0", "sense_of_shame": "1", "female_body": "0", "bra_size": "0", "hip_size": "0", "wine_tolerance": "-1"}
    },

    # ==================== 东煌 (Dragon Empery, alignment="7") ====================
    {
        "id": "ning_hai", "name": "宁海", "color": "#FF0000", "region": "dragon_empiry_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "7",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "0"}
    },
    {
        "id": "ping_hai", "name": "平海", "color": "#FF6347", "region": "dragon_empiry_dorm",
        "stamina": 1750, "energy": 1700, "ship_type": "1", "alignment": "7",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "0", "innocent": "1", "female_body": "-1", "bra_size": "-1", "hip_size": "-1", "wine_tolerance": "-1"}
    },

    # ==================== 北方联合 (Northern Parliament, alignment="8") ====================
    {
        "id": "avrora", "name": "阿芙乐尔", "color": "#B0E0E6", "region": "northern_parliament_dorm",
        "stamina": 1800, "energy": 1750, "ship_type": "1", "alignment": "8",
        "talents": {"courage": "1", "attitude": "-1", "response": "-1", "self_respect": "1", "devoted": "1", "female_body": "1", "bra_size": "1", "hip_size": "1", "wine_tolerance": "3", "charm": "1"}
    }
]


def generate_character_files():
    """生成所有 80 位新舰娘的 data/characters/*.json 文件"""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    for char_def in NEW_CHARACTERS_DATA:
        cid = char_def["id"]
        cname = char_def["name"]
        color = char_def["color"]
        region = char_def["region"]
        node = f"{cid}_room"
        stamina = char_def["stamina"]
        energy = char_def["energy"]
        ship_type = char_def["ship_type"]
        alignment = char_def["alignment"]

        # 基础 talent 字典
        talent = {
            "alignment": alignment,
            "ship_type": ship_type,
            "virgin": "1",
            "no_kiss_exp": "1",
            "sex": "0",
            "relationship": "0"
        }
        talent.update(char_def["talents"])

        chara_json = {
            "id": cid,
            "name": cname,
            "color": color,
            "location": {
                "region": region,
                "node": node
            },
            "base": {
                "max_stamina": stamina,
                "max_energy": energy,
                "stamina": stamina,
                "energy": energy
            },
            "talent": talent,
            "schedule": {
                "sleep": {
                    "start": [23, 0],
                    "end": [7, 0]
                },
                "works": []
            }
        }

        target_file = CHARACTERS_DIR / f"{cname}.json"
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(chara_json, f, ensure_ascii=False, indent=2)
        count += 1

    print(f"[√] 成功生成 {count} 个新舰娘角色数据文件！")


def update_maps_and_configs():
    """更新所有地图与宿舍节点配置文件"""
    # 1. 扩充四大阵营及两个新阵营的房间
    rooms_by_region = {
        "eagle_union_dorm": {},
        "royal_dorm": {},
        "sakura_dorm": {},
        "ironblood_dorm": {},
        "dragon_empiry_dorm": {},
        "northern_parliament_dorm": {}
    }

    for char_def in NEW_CHARACTERS_DATA:
        region = char_def["region"]
        node = f"{char_def['id']}_room"
        room_name = f"{char_def['name']}的房间"
        rooms_by_region[region][node] = {"name": room_name, "actions": {}}

    # 读取并更新现有宿舍文件
    for region, new_rooms in rooms_by_region.items():
        map_file = MAPS_DIR / f"{region}.json"
        if map_file.exists():
            data = json.loads(map_file.read_text(encoding="utf-8"))
        else:
            corridor_name = {
                "dragon_empiry_dorm": "东煌宿舍走廊",
                "northern_parliament_dorm": "北方联合宿舍走廊"
            }.get(region, "宿舍走廊")
            data = {"corridor": {"name": corridor_name, "actions": {}}}

        data.update(new_rooms)
        with open(map_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f" [+] 更新地图文件: {region}.json (包含 {len(data)} 个节点)")

    # 2. 更新 data/maps/_regions.json
    regions_file = MAPS_DIR / "_regions.json"
    regions_data = json.loads(regions_file.read_text(encoding="utf-8"))
    regions_data["dragon_empiry_dorm"] = {
        "name": "东煌宿舍区",
        "micro_map": "dragon_empiry_dorm.json",
        "entry_node": "corridor"
    }
    regions_data["northern_parliament_dorm"] = {
        "name": "北方联合宿舍区",
        "micro_map": "northern_parliament_dorm.json",
        "entry_node": "corridor"
    }
    with open(regions_file, "w", encoding="utf-8") as f:
        json.dump(regions_data, f, ensure_ascii=False, indent=2)
    print(" [+] 更新 _regions.json (注册东煌与北方联合宿舍区)")

    # 3. 收集所有房间 node 列表
    all_rooms_by_region = {}
    for r in ["eagle_union_dorm", "royal_dorm", "sakura_dorm", "ironblood_dorm", "dragon_empiry_dorm", "northern_parliament_dorm"]:
        mf = MAPS_DIR / f"{r}.json"
        if mf.exists():
            d = json.loads(mf.read_text(encoding="utf-8"))
            all_rooms_by_region[r] = [k for k in d.keys() if k != "corridor"]

    # 4. 更新 config/map_config.py
    map_config_content = f'''# -*- coding: utf-8 -*-
NAP_LOC: dict[str, list[str]] = {{
    'home': ['living_room', 'bedroom'],
}}

SLEEP_LOC: dict[str, list[str]] = {{
    'home': ['bedroom'],
}}

WORK_LOC: dict[str, list[str]] = {{
    'office': ['desk'],
}}

CAN_SIT_LOC: dict[str, list[str]] = {{
    'home': ['living_room', 'bedroom', 'kitchen'],
    'office': ['desk'],
    'canteen': ['hall', 'private_room'],
    'eagle_union_dorm': {json.dumps(all_rooms_by_region.get('eagle_union_dorm', []))},
    'ironblood_dorm': {json.dumps(all_rooms_by_region.get('ironblood_dorm', []))},
    'royal_dorm': {json.dumps(all_rooms_by_region.get('royal_dorm', []))},
    'sakura_dorm': {json.dumps(all_rooms_by_region.get('sakura_dorm', []))},
    'dragon_empiry_dorm': {json.dumps(all_rooms_by_region.get('dragon_empiry_dorm', []))},
    'northern_parliament_dorm': {json.dumps(all_rooms_by_region.get('northern_parliament_dorm', []))},
    'shop_street': ['shop'],
}}

HAVE_BED_LOC: dict[str, list[str]] = {{
    'home': ['living_room', 'bedroom'],
    'eagle_union_dorm': {json.dumps(all_rooms_by_region.get('eagle_union_dorm', []))},
    'ironblood_dorm': {json.dumps(all_rooms_by_region.get('ironblood_dorm', []))},
    'royal_dorm': {json.dumps(all_rooms_by_region.get('royal_dorm', []))},
    'sakura_dorm': {json.dumps(all_rooms_by_region.get('sakura_dorm', []))},
    'dragon_empiry_dorm': {json.dumps(all_rooms_by_region.get('dragon_empiry_dorm', []))},
    'northern_parliament_dorm': {json.dumps(all_rooms_by_region.get('northern_parliament_dorm', []))},
}}
'''
    (CONFIG_DIR / 'map_config.py').write_text(map_config_content, encoding='utf-8')
    print(" [+] 更新 config/map_config.py")

    # 5. 更新 data/time/move_time.json
    move_time_file = TIME_DIR / "move_time.json"
    move_time_data = json.loads(move_time_file.read_text(encoding="utf-8"))
    corridor_moves = move_time_data.setdefault("corridor", {})
    
    for r, rooms in all_rooms_by_region.items():
        for room in rooms:
            corridor_moves[room] = 1
            move_time_data[room] = {"corridor": 1}

    with open(move_time_file, "w", encoding="utf-8") as f:
        json.dump(move_time_data, f, ensure_ascii=False, indent=2)
    print(" [+] 更新 data/time/move_time.json")

    # 6. 更新 data/time/leave_time.json
    leave_time_file = TIME_DIR / "leave_time.json"
    leave_time_data = json.loads(leave_time_file.read_text(encoding="utf-8"))
    
    all_regions = list(regions_data.keys())
    for r1 in all_regions:
        r1_dict = leave_time_data.setdefault(r1, {})
        for r2 in all_regions:
            if r1 != r2 and r2 not in r1_dict:
                # 默认区域间移动时间 5 分钟
                r1_dict[r2] = 5

    with open(leave_time_file, "w", encoding="utf-8") as f:
        json.dump(leave_time_data, f, ensure_ascii=False, indent=2)
    print(" [+] 更新 data/time/leave_time.json")


if __name__ == '__main__':
    generate_character_files()
    update_maps_and_configs()

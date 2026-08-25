NAP_LOC: dict[str, list[str]] = {
    'home': ['living_room', 'bedroom'],
}

SLEEP_LOC: dict[str, list[str]] = {
    'home': ['bedroom'],
}

WORK_LOC: dict[str, list[str]] = {
    'office': ['desk'],
}

CAN_SIT_LOC: dict[str, list[str]] = {
    'home': ['living_room', 'bedroom', 'kitchen'],
    'office': ['desk'],
    'canteen': ['hall', 'private_room'],
    'eagle_union_dorm': ['laffey_room'],
    'ironblood_dorm': ['z23_room'],
    'royal_dorm': ['javelin_room'],
    'sakura_dorm': ['ayanami_room', 'shiranui_room', 'akashi_room'],
    'shop_street': ['shop'],
}

HAVE_BED_LOC: dict[str, list[str]] = {
    'home': ['living_room', 'bedroom'],
    'eagle_union_dorm': ['laffey_room'],
    'ironblood_dorm': ['z23_room'],
    'royal_dorm': ['javelin_room'],
    'sakura_dorm': ['ayanami_room', 'shiranui_room', 'akashi_room'],
}
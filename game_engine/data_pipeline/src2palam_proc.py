from data.data_loader import load_attr_defs
from game_engine.models.character import Character
from .src2palam_map import src2palam_map

def src2palam_proc(src: dict[str, int], source: Character, target: Character):
    '''将source转成palam'''
    mes_source: list[str] = [f'{source.name}']
    mes_target: list[str] = [f'{target.name}']
    attr_defs = load_attr_defs()

    for src_k, src_v in src.items():
        palam_map = src2palam_map[src_k]
        for palam, info in palam_map.items():
            chara = source if info['chara'] == 'source' else target
            chara.palam[palam] += int(info['value'] * src_v)
            if chara == source:
                mes_source.append(f'{attr_defs['palam'][palam]["name"]} {chara.palam[palam]} + {int(info['value'] * src_v)} = {chara.palam[palam] + int(info['value'] * src_v)}')
            else:
                mes_target.append(f'{attr_defs['palam'][palam]["name"]} {chara.palam[palam]} + {int(info['value'] * src_v)} = {chara.palam[palam] + int(info['value'] * src_v)}')

    return mes_source, mes_target
            
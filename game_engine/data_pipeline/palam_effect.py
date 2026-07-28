def palam2favor(palam: dict[str, int]):
    '''palam对好感的修正'''
    bonus = 0
    
    # 好意
    kindness = palam['kindness_palam']
    if kindness < 100:
        pass
    elif kindness < 500:
        bonus += 1
    elif kindness < 3000:
        bonus += 2
    elif kindness < 10000:
        bonus += 4
    else:
        bonus += 5

    return bonus
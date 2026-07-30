from config.mood_enum import Mood


def mood2favor(mood: Mood) -> int:
    '''心情对好感的修正'''
    if mood == Mood.ANGRY:
        return -2
    elif mood == Mood.UNHAPPY:
        return -1
    elif mood == Mood.NEUTRAL:
        return 0
    elif mood == Mood.HAPPY:
        return 1
    elif mood == Mood.DELIGHTED:
        return 2
    else:
        return 3


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

def mood2source(mood: Mood):
    '''心情对source的修正'''
    if mood == Mood.HAPPY:
        positive_mood_multi = 1.1
        negative_mood_multi = 0.9
    elif mood == Mood.DELIGHTED:
        positive_mood_multi = 1.3
        negative_mood_multi = 0.7
    elif mood == Mood.BLISS:
        positive_mood_multi = 1.5
        negative_mood_multi = 0.5
    elif mood == Mood.UNHAPPY:
        positive_mood_multi = 0.9
        negative_mood_multi = 1.1
    elif mood == Mood.ANGRY:
        positive_mood_multi = 0.7
        negative_mood_multi = 1.3
    else:
        positive_mood_multi = 1.0
        negative_mood_multi = 1.0

    return positive_mood_multi, negative_mood_multi
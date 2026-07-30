from config.mood_enum import Mood


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
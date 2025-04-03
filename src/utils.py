from datetime import datetime
from typing import Optional


def get_age(birthday: Optional[str]) -> Optional[int]:
    """Returns person's age given their birthday.

    Args:
        birthday: (optional) Birthday in "DD.MM.YYYY" format
            (or "DD.MM", or None).

    Returns:
        Age (in whole years) or None if birthday is not specified.

    """
    if birthday and birthday.count('.') == 2:
        if dt := datetime.strptime(birthday, '%d.%m.%Y'):
            # @see https://stackoverflow.com/a/9754466/5111076
            today = datetime.today()
            return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))

def get_gender(code: Optional[int]) -> Optional[str]:
    """Returns person's gender given sex code

    Args:
        code: (optional) Sex code (0, 1 or 2).

    Returns:
        Gender label or None.

    """
    if code:
        return 'мужской' if code == 2 else 'женский'
    return 'не указано'

def get_relation(code: Optional[int]) -> Optional[str]:
    """Returns relation label given its code

    Args:
        code: (optional) Relation code (from 0 to 8).

    Returns:
        Relation label.

    """
    match code:
        case 1:
            return 'не женат/не замужем'
        case 2:
            return 'есть друг/есть подруга'
        case 3:
            return 'помолвлен/помолвлена'
        case 4:
            return 'женат/замужем'
        case 5:
            return 'всё сложно'
        case 6:
            return 'в активном поиске'
        case 7:
            return 'влюблён/влюблена'
        case 8:
            return 'в гражданском браке'
        case _:
            return 'не указано'

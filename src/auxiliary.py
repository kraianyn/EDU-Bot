from datetime import datetime
from typing import Union
from collections import namedtuple
from sqlite3 import connect

from src.config import LANGUAGES, DATABASE
import src.loggers as l

ChatRecord = namedtuple(
    'ChatRecord',
    ('id', 'type', 'username', 'language', 'group_id', 'role', 'familiarity', 'feedback', 'registered')
)
Familiarity = namedtuple(  # familiarity with the bot's interactions
    'Familiarity',
    ('commands', 'trust', 'distrust', 'new', 'cancel', 'event_answer', 'save', 'delete', 'clear', 'tell', 'ask',
     'answer', 'resign', 'feedback', 'leave')
)


def get_chat_record(chat_id: int) -> Union[ChatRecord, None]:
    """
    Args:
        chat_id (int): id of the chat that record will be returned of.

    Returns (src.auxiliary.ChatRecord or None): record of the chat with the given id. None if the chat is not
        registered.
    """
    connection = connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM chats WHERE id = ?',
        (chat_id,)
    )
    record = cursor.fetchone()

    try:
        record = ChatRecord(*record)
    except TypeError:
        record = None

    cursor.close()
    connection.close()

    return record


def str_sort_key(string: str) -> int:
    """
    This function serves as a key for sorting strings in Ukrainian, English and Russian. It only considers alphabetical
    letters of these languages. It is needed because Unicode order is sometimes different from the alphabetical one.

    Args:
        string (str): element of the sorted sequence.
    """
    letters = 'abcdefghijklmnopqrstuvwxyzабвгґдеєёжзиіїйклмнопрстуфхцчшщъыьэюя'

    for ch in string:
        if (ch_l := ch.lower()) in letters:
            return letters.index(ch_l)

    return 0


def update_group_chat_language(group_id: int):
    """
    This function sets language of the group's group chat to the most popular among its students.

    Args:
        group_id (int): id of the group that group chat's language will be updated of.
    """
    connection = connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute(
        'SELECT language, COUNT(language) AS spoken_by '
        'FROM chats WHERE group_id = ? AND type = 0 '
        'GROUP BY language '
        'ORDER BY spoken_by DESC',
        (group_id,)
    )
    common_language, spoken_by = cursor.fetchone()
    cursor.execute(
        'UPDATE chats SET language = ? '
        'WHERE group_id = ? AND type <> 0',
        (common_language, group_id,)
    )
    connection.commit()
    cursor.close()
    connection.close()
    l.cl.info(l.GROUP_LANGUAGE_UPDATED.format(group_id, LANGUAGES[common_language], spoken_by))


def str_to_datetime(event: str) -> datetime:
    """
    Args:
        event (str): string that begins with date in one of the two formats that date is stored in the database in:
            '%u %d.%m' or '%u %d.%m, %H:%M' (actually, (%u - 1) instead of %u, Monday to Sunday = 0 to 6).

    Returns (datetime.datetime): datetime.datetime of the date that the given string begins with.
    """
    weekday_index, day, month, hour, minute = int(event[0]), int(event[2:4]), int(event[5:7]), 23, 59
    if event[7] == ',':  # if the event contains time
        hour, minute = int(event[9:11]), int(event[12:14])

    now = datetime.now()
    date_this_year = datetime(now.year, month, day, hour, minute)
    weekday_index_this_year = int(date_this_year.strftime('%u')) - 1

    if weekday_index > weekday_index_this_year or (weekday_index == 0 and weekday_index_this_year == 6):
        return datetime(now.year + 1, month, day, hour, minute)

    if weekday_index < weekday_index_this_year or (weekday_index == 6 and weekday_index_this_year == 0):
        return datetime(now.year - 1, month, day, hour, minute)

    return date_this_year


def cut(string: str):
    max_length = 40
    return (string if len(string) <= max_length else f'{string[:max_length - 1]}…').replace('\n', ' ')

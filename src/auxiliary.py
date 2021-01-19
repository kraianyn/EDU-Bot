from datetime import datetime
from typing import Union
from collections import namedtuple
from sqlite3 import connect

from src.config import DATABASE


ChatRecord = namedtuple(
    'ChatRecord',
    ('id', 'type', 'username', 'language', 'group_id', 'role', 'familiarity', 'registered')
)
Familiarity = namedtuple(
    'Familiarity',
    ('commands', 'trust', 'distrust', 'new', 'cancel', 'answer_to_notify', 'save', 'delete', 'clear', 'tell', 'ask',
     'resign', 'leave')
)


def get_chat_record(chat_id: int) -> Union[ChatRecord, None]:
    """
    This function looks for record of the chat with the given id in the database.

    Args:
        chat_id (int): id of the chat that record will be returned of.

    Returns (src.auxiliary.ChatRecord or None): record of the chat with the given id. None if the record is not found.
    """
    connection = connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT * FROM chats WHERE id = ?',
        (chat_id,)
    )
    record = cursor.fetchone()

    try:
        record = ChatRecord(*record[:6], Familiarity(*record[6]), record[7])
    except TypeError:
        record = None

    cursor.close()
    connection.close()

    return record


def string_sort_key(string: str) -> int:
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


def str_to_datetime(string: str) -> datetime:
    """
    This function converts string that contains date in the beginning to datetime.datetime of the date. The date's
    format is one of the two that date is stored in the database in: '%u %d.%m' or '%u %d.%m, %H:%M' (actually, (%u - 1)
    instead of %u, but the first 2 characters of the string do not matter anyway).

    Args:
        string (str): string containing date in the format according to src.config.DATE_PATTERN.
    """
    day, month, hour, minute = int(string[2:4]), int(string[5:7]), 0, 0
    if string[7] == ',':  # if the event contains time
        hour, minute = int(string[9:11]), int(string[12:14])

    now = datetime.now()
    date_this_year = datetime(now.year, month, day, hour, minute)

    return date_this_year if date_this_year > now else datetime(now.year + 1, month, day, hour, minute)

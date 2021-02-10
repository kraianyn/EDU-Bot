from datetime import datetime
from collections import namedtuple
from sqlite3 import connect

from telegram import ParseMode

from src.interactions import bot
import src.auxiliary as a
from src.text import WEEKDAYS, TODAY, TOMORROW, DAYS_LEFT
from src.config import LANGUAGES, DATABASE
import src.loggers as l

# ----------------------------------------------------------------------------------------------- reminding about events

Event = namedtuple('Event', ('translated', 'reminded'))


def remind_about_events():
    l.nl.info(l.REMINDING_STARTS)

    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0, 0)

    connection = connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute('SELECT id, events FROM groups')
    for group_id, events_str in cursor.fetchall():
        students, events = set[str](), dict[int, list[Event]]()

        for event in events_str.split('\n'):
            event, _, reminded = event.rpartition('|')

            days_left = (a.str_to_datetime(event) - today).days
            translated_event = tuple(f'{WEEKDAYS[int(event[0])][index]} {event[2:]}' for index in range(len(LANGUAGES)))
            reminded = reminded.split()

            if not reminded:  # if no one has agreed to be reminded about the event
                continue

            if days_left not in events:
                events[days_left] = [Event(translated_event, reminded)]
            else:
                events[days_left].append(Event(translated_event, reminded))

            students.update(reminded)

        cursor.execute(
            'SELECT id, language FROM chats WHERE group_id = ? AND type = 0',
            (group_id,)
        )
        students = tuple(r for r in cursor.fetchall() if str(r[0]) in students)

        for user_id, language in students:
            user_events = {
                days_left: tuple(
                    event.translated[language] for event in days_left_events if str(user_id) in event.reminded
                )
                for days_left, days_left_events in events.items()
            }  # events that the student has agreed to be reminded about by the number of full days left

            days_left_events = list[str]()

            if 0 in user_events:  # if there are events that are today
                days_left_events.append(TODAY[language].format('\n'.join(user_events[0])))
                del user_events[0]

            if 1 in user_events:  # if there are events that are tomorrow
                days_left_events.append(TOMORROW[language].format('\n'.join(user_events[1])))
                del user_events[1]

            for days_left, days_left_user_events in user_events.items():
                days_left_events.append(DAYS_LEFT[language].format(days_left, '\n'.join(user_events[days_left])))

            bot.send_message(user_id, '\n\n'.join(days_left_events), parse_mode=ParseMode.HTML)

        num_events = sum(tuple(len(days_left_events) for days_left_events in events.values()))
        l.nl.info(l.GROUP_REMINDED.format(len(students), group_id, num_events))

    cursor.close()
    connection.close()

    l.nl.info(l.REMINDING_FINISHES)

from datetime import datetime
from collections import namedtuple
from sqlite3 import connect

from telegram import ParseMode

from interactions import bot, EventAnswering, current
from auxiliary import str_to_datetime
import text as t
from config import LANGUAGES, DATABASE
import log

# ----------------------------------------------------------------------------------------------- reminding about events

Event = namedtuple('Event', ('translated', 'reminded'))


def remind_about_events():
    log.nl.info(log.REMINDING_STARTS)

    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0, 0)

    connection = connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute('SELECT id, events FROM groups')
    for group_id, events_str in cursor.fetchall():
        try:
            events_str = events_str.split('\n')
        except AttributeError:  # if the group has no events
            continue

        cursor.execute(  # the group's students
            'SELECT id, language FROM chats WHERE group_id = ? AND type = 0',
            (group_id,)
        )
        student_records: list[tuple[int, int]] = cursor.fetchall()

        event_answering = None
        for user_id, language in student_records:
            if user_id in current and isinstance(current[user_id], EventAnswering):
                event_answering = current[user_id]
                break

        events, reminded = inspect_events(events_str, today, event_answering)

        reminded_records = tuple(r for r in student_records if str(r[0]) in reminded)
        send_reminders(events, reminded_records)

        if events_str:  # if there are events that have not passed
            cursor.execute(  # updating the group's events, excluding ones that have passed
                'UPDATE groups SET events = ? WHERE id = ?',
                ('\n'.join(events_str), group_id)
            )
        else:  # if all of the group's events have passed
            cursor.execute(
                'UPDATE groups SET events = NULL WHERE id = ?',
                (group_id,)
            )
        connection.commit()

        num_events = sum(tuple(len(days_left_events) for days_left_events in events.values()))
        log.nl.info(log.GROUP_REMINDED.format(len(reminded_records), group_id, num_events))

    cursor.close()
    connection.close()

    log.nl.info(log.REMINDING_FINISHES)


def inspect_events(events_str: list[str], today: datetime, event_answering: EventAnswering) \
        -> tuple[dict[int, list[Event]], set[str]]:
    events, reminded = dict[int, list[Event]](), set[str]()

    for event_str in events_str:  # for each of the group's events
        event_str, _, event_reminded = event_str.rpartition('|')
        event, event_reminded = str_to_datetime(event_str), event_reminded.split()

        if not event_reminded:  # if no one has agreed to be reminded about the event
            continue

        if event < today:  # if the event has passed
            del events_str[0]
            if event_answering:
                event_answering.cancel_question(event_str)
            continue

        translated_event = tuple(
            f'{t.WEEKDAYS[int(event_str[0])][index]} {event_str[2:]}' for index in range(len(LANGUAGES))
        )

        if (days_left := (event - today).days) not in events:
            events[days_left] = [Event(translated_event, event_reminded)]
        else:
            events[days_left].append(Event(translated_event, event_reminded))

        reminded.update(event_reminded)

    return events, reminded


def send_reminders(events: dict[int, list[Event]], reminded_records: tuple[tuple[int, int]]):
    for user_id, language in reminded_records:  # for each student that has agreed to be reminded about at least 1 event
        # events that the student has agreed to be reminded about by the number of full days left
        user_events = dict[int, list[str]]()
        for days_left, days_left_events in events.items():
            days_left_user_events = tuple(
                event.translated[language] for event in days_left_events if str(user_id) in event.reminded
            )

            # if the student has agreed to be reminded about at least 1 event that is days_left days
            if days_left_user_events:
                user_events[days_left] = days_left_user_events

        bot.send_message(user_id, t.report_on_events(user_events, language), parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------------- notification about e-campus changes

def check_ecampus_updates():  # todo
    log.nl.info(log.ECAMPUS_NOTIFICATION_STARTS)

    log.nl.info(log.ECAMPUS_NOTIFICATION_FINISHES)

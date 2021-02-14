from datetime import datetime
from collections import namedtuple
from itertools import cycle
from threading import Thread
from sqlite3 import connect

from telegram import ParseMode
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from interactions import bot, EventAnswering, current
from auxiliary import str_to_datetime
import text as t
import config as c
import log

# ----------------------------------------------------------------------------------------------- reminding about events

Event = namedtuple('Event', ('translated', 'reminded'))
EventsDict = dict[int, list[Event]]


def remind_about_events():
    log.nl.info(log.REMINDING_STARTS)

    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0, 0)

    connection = connect(c.DATABASE)
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

        reminded_records = [r for r in student_records if str(r[0]) in reminded]
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

        num_events = sum([len(days_left_events) for days_left_events in events.values()])
        log.nl.info(log.GROUP_REMINDED.format(len(reminded_records), group_id, num_events))

    cursor.close()
    connection.close()

    log.nl.info(log.REMINDING_FINISHES)


def inspect_events(events_str: list[str], today: datetime, event_answering: EventAnswering) \
        -> tuple[dict[int, list[Event]], set[str]]:
    events: EventsDict = {}
    reminded = set[str]()

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

        translated_event = [
            f'{t.WEEKDAYS[int(event_str[0])][index]} {event_str[2:]}' for index in range(len(c.LANGUAGES))
        ]

        if (days_left := (event - today).days) not in events:
            events[days_left] = [Event(translated_event, event_reminded)]
        else:
            events[days_left].append(Event(translated_event, event_reminded))

        reminded.update(event_reminded)

    return events, reminded


def send_reminders(events: EventsDict, reminded_records: tuple[tuple[int, int]]):
    for user_id, language in reminded_records:  # for each student that has agreed to be reminded about at least 1 event
        # events that the student has agreed to be reminded about by the number of full days left
        user_events: dict[int, list[str]] = {}
        for days_left, days_left_events in events.items():
            days_left_user_events = [
                event.translated[language] for event in days_left_events if str(user_id) in event.reminded
            ]

            # if the student has agreed to be reminded about at least 1 event that is days_left days
            if days_left_user_events:
                user_events[days_left] = days_left_user_events

        bot.send_message(user_id, t.report_on_events(user_events, language), ParseMode.HTML)


# ---------------------------------------------------------------------------------- notification about e-campus changes

ECampusRecord = tuple[int, int, str, str, str]
ECampusUpdate = tuple[int, list[str], list[str], list[float], list[str]]
ECampusUpdatesDict = dict[int, ECampusUpdate]


def check_ecampus_updates():
    log.nl.info(log.ECAMPUS_NOTIFICATION_STARTS)

    now = datetime.now()
    options = -4, -1 - (now.month >= c.THRESHOLD_DATE[0] and now.day >= c.THRESHOLD_DATE[1])

    connection = connect(c.DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        'SELECT ecampus.id, language, login, password, points FROM ecampus, chats '
        'GROUP BY ecampus.id'
    )
    ecampus_records: list[ECampusRecord] = cursor.fetchall()

    range_threads = range(c.ECAMPUS_THREADS)
    groups = [[] for _ in range_threads]
    for i in cycle(range_threads):
        try:
            groups[i].append(ecampus_records.pop(0))
        except IndexError:
            break

    updates = ECampusUpdatesDict()

    group_threads: list[Thread] = []
    for group in filter(None, groups):
        thread = Thread(target=get_group_updates, args=(group, options, updates))
        group_threads.append(thread)
        thread.start()

    for thread in group_threads:
        thread.join()

    for user_id, (language, subjects, points, changes, new) in updates.items():
        updated_points = '\n'.join([f'{s} {p}' for s, p in zip(subjects + new, points)])
        cursor.execute(  # updating the student's points
            'UPDATE ecampus SET points = ? WHERE id = ?',
            (updated_points, user_id)
        )

        text = t.report_on_updates(subjects, points, changes, new, language)
        bot.send_message(user_id, text, ParseMode.HTML)

    connection.commit()
    cursor.close()
    connection.close()

    log.nl.info(log.ECAMPUS_NOTIFICATION_FINISHES)


def get_group_updates(group: list[ECampusRecord], options: tuple[int, int], updates: ECampusUpdatesDict):
    for user_id, language, login, password, points_str in group:
        subjects: list[str] = []
        points: list[str] = []

        try:
            subjects_points = points_str.split('\n')
        except AttributeError:  # if the student's account has never been checked
            pass
        else:  # if the student's account has been checked at least once
            for subject_points in subjects_points:
                s, _, p = subject_points.partition(' ')
                subjects.append(s)
                points.append(p)

        try:
            updates[user_id] = (language, subjects, *check_account_updates(login, password, options, points))
        except TimeoutException:
            bot.send_message(user_id, t.ECAMPUS_DOWN[language], ParseMode.HTML)


def check_account_updates(user_login: str, user_password: str, options: tuple[int, int],
                          current_points: list[str]) -> tuple[list[str], list[float], list[str]]:
    """
    Args:
        user_login (str): login of the student's account.
        user_password (str): password to the student's account.
        options (tuple[int, int]): ids of options (year and term) that will be selected to filter out irrelevant
            subjects.
        current_points (tuple[str]): the student's yesterday points according to the order of subjects in their account.

    Returns (tuple[list[str], list[float], list[str]]): the student's current points, difference between each subject's
        current points and yesterday ones, abbreviated subjects that have just been added to E-Campus.
    """
    driver = webdriver.Chrome(f'../../res/chromedriver.exe')
    driver.get(c.ECAMPUS_URL)  # opening the login form

    login, password = driver.find_elements(By.CLASS_NAME, 'form-control')
    login.send_keys(user_login)  # entering the login
    password.send_keys(user_password)  # entering the password
    password.send_keys(Keys.RETURN)  # logging in

    wait(driver, (By.CLASS_NAME, 'nav-link'))
    current_ecampus = driver.find_elements(By.CLASS_NAME, 'nav-link')[2]
    current_ecampus.click()  # opening the current version of E-Campus

    subjects = wait(driver, (By.LINK_TEXT, 'Поточний контроль'))
    subjects.click()  # displaying the subject table

    available_options = driver.find_elements(By.TAG_NAME, 'option')
    year_option = available_options[options[0]]
    year_option.click()  # selecting the current year's (2 terms) subjects
    term_option = available_options[options[1]]
    term_option.click()  # selecting the current term's subjects

    num_subjects = 0
    for subject in driver.find_element(By.CLASS_NAME, 'ListBox').find_elements(By.TAG_NAME, 'a')[::-1]:
        if subject.is_displayed():  # if the subject is relevant
            subject.send_keys(Keys.CONTROL + Keys.RETURN)  # opening the subject in a new tab
            num_subjects += 1
        else:  # if the subject is irrelevant
            break  # all relevant subjects have been opened in a new tab

    range_subjects = range(num_subjects)
    points, changes, new = [], [], []

    for index in range_subjects:
        driver.close()  # closing the current tab
        driver.switch_to.window(driver.window_handles[0])  # switching to the last relevant subject's tab

        subject_points = driver.find_element(By.ID, 'tabs-0').find_element(By.TAG_NAME, 'b').text
        points.append(subject_points)

        try:
            changes.append(float(subject_points) - float(current_points[index]))
        except IndexError:  # if the event has just been added
            new.append(abbreviate(driver.find_element(By.CLASS_NAME, 'head').find_elements(By.TAG_NAME, 'b')[1].text))

    driver.quit()
    return points, changes, new


def wait(driver, until: tuple[str, str]) -> WebElement:
    try:
        return WebDriverWait(driver, c.ECAMPUS_WAIT).until(expected_conditions.presence_of_element_located(until))
    except TimeoutException:
        driver.quit()
        raise TimeoutException


def abbreviate(subject: str) -> str:
    name = subject.partition('.')[0] if '.' in subject else subject.partition(',')[0]

    ignored = ('та', 'і', 'й', 'до', 'за')
    abbreviation = ''.join(word[0] for word in name.replace('-', ' ').split() if word not in ignored).upper()

    return abbreviation

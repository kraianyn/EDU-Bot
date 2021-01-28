from typing import Union

from config import MIN_GROUPMATES_FOR_LC

# -------------------------------------------------------------------------------------------------------------- casual

WEEKDAYS = (
    ('Пн', 'Mon', 'Пн'),
    ('Вт', 'Tue', 'Вт'),
    ('Ср', 'Wed', 'Ср'),
    ('Чт', 'Thu', 'Чт'),
    ('Пт', 'Fri', 'Пт'),
    ('Сб', 'Sat', 'Сб'),
    ('Нд', 'Sun', 'Вс')
)
PRIVATE_INTERACTION = (
    '',
    'PRIVATE_INTERACTION',
    ''
)
YES, NO = ('так', 'yes', 'да'), ('ні', 'no', 'нет')
REGISTRATION_NEEDED = (
    '',
    'REGISTRATION_NEEDED',
    ''
)

# -------------------------------------------------------------------------------------------------------- registration

ASK_LANGUAGE = 'мова / language / язык:'
ASK_CITY = (
    (  # for groups
        '',
        "[g] Hi! Which city does this group study in?",
        ''
    ),
    (  # for students
        '',
        "[s] Hi! Which city do you study in?",
        ''
    )
)
ASK_EDU = (
    '',
    "Now, what about the EDU?..",
    ''
)
ASK_DEPARTMENT = (
    '',
    "...and the department?",
    ''
)
ASK_GROUP_NAME = (
    (  # for groups
        '',
        "[g] We're almost done. What is your group's name?",
        ''
    ),
    (  # for students
        '',
        "[s] Ok, the last step. I need you to enter your group's name.",
        ''
    )
)
INTRODUCTION = (
    (  # for groups
        '',
        '[g] INTRODUCTION',
        ''
    ),
    (  # for students
        '',
        '[s] INTRODUCTION',
        ''
    )
)
NEW_GROUPMATE = (
    ('', ''),
    ("{} has just registered", '{} told me they are your groupmate', 'Now I know that {} is from your group'),
    ('', '')
)

# ------------------------------------------------------------------------------ registration (report on related chats)

GROUPMATES_FOUND = (
    'До речі, {}{}{}',
    'By the way, {} already registered{}{}',
    ''
)
GROUPMATES_ = (
    (
        '{} з твоїх одногрупників вже зареєструвалися',
        '{} of your groupmates have',
        ''
    ),
    (
        'один з твоїх одногрупників вже зареєструвався',
        'one of your groupmates has',
        ''
    )
)
GROUP_CHATS_ALSO_FOUND_ = (
    ', і група зареєструвала {}',
    ', and {} also been registered',
    ''
)
GROUP_CHATS_ = (
    (
        'ваш груповий чат',
        'your group chat has',
        ''
    ),
    (
        'кілька групових чатів',
        '{} group chats have',
        ''
    )
)
LC_AVAILABLE_ = (
    (
        ", і цього достатньо, щоб з'ясувати, хто з вас є старостою. Бракує лише групового чата, просто напишіть "
        "/start там. Потім, якщо староста ти, скористайся командою /claim.",
        ", and that's just enough to figure out who your leader is. The only thing that's missing is your group chat, "
        "just use /start there. Then, if you are the group's leader, use /claim.",
        ''
    ),
    (
        '. Тепер, якщо ти староста, скористайся командою /claim.',
        ". Now, if you are the group's leader, use /claim.",
        ''
    )
)
LC_NOW_AVAILABLE = (
    '{}-ий студент з вашої групи щойно зареєструвався{}',
    'The {}th student from your group has just registered{}',
    ''
)
GROUP_CHATS_FOUND = (
    "До речі, ви вже зарестрували {}, але ти перший студент. Скажи своїм одногрупникам зареєструватися теж, щоб ми "
    "могли з'ясувати, хто з вас староста, і почати використовувати мої можливості)",
    'By the way, {} already been registered by your group, but you are the first student to register. Tell your '
    'groupmates to do it as well so that we can figure out who your leader is and start having some fun)',
    ''
)
NONE_FOUND = (
    '',
    "By the way, you are the first student from your group I know of. For me to know that students are from the same "
    "group, they need to enter the same group name (the case doesn't matter), which is {} for your group.",
    ''
)
STUDENTS_FOUND = (
    '',
    'By the way, here are students that have already registered:\n\n{}',
    ''
)
NO_STUDENTS_FOUND = (
    '',
    'By the way, none of you have registered so far. Everyone, just send me /start privately so that we can figure out '
    'who your leader is and start having some fun)',
    ''
)


def report_on_related_chats(num_groupmates: int, num_group_chats: int, language: int) \
        -> tuple[str, Union[None, tuple[tuple[str]]]]:
    """
    This function generates a text message containing information about how many of the student's groupmates have
    registered and how many group chats their group has registered (most groups only have 1). It also determines whether
    the student has made the number of registered students from the group big enough for leader confirmation (LC).

    Args:
        num_groupmates (int): number of the student's registered groupmates.
        num_group_chats (int): number of group chats that the student's group has registered.
        language (int): index of the student's language, according to src.config.LANGUAGES.

    Returns (tuple[str, None or tuple[tuple[str]]]): text message containing information described above, and tuple of
        strings describing actions to start LC (None if the student has not made the number of registered students from
        the group big enough for LC).
    """
    def group_chats(num_group_chats: int, language: int) -> str:
        return GROUP_CHATS_[0][language] if num_group_chats == 1 else GROUP_CHATS_[1][language].format(num_group_chats)

    if num_groupmates:
        groupmates_ = GROUPMATES_[0][language].format(num_groupmates) if num_groupmates != 1 \
            else GROUPMATES_[1][language]

        group_chats_registered = bool(num_group_chats)
        group_chats_ = GROUP_CHATS_ALSO_FOUND_[language].format(group_chats(num_group_chats, language)) \
            if group_chats_registered else ''

        lc_now_available = num_groupmates == MIN_GROUPMATES_FOR_LC
        if lc_now_available:
            lc_available_msg = LC_AVAILABLE_[group_chats_registered]
            lc_available_ = lc_available_msg[language]
        else:
            lc_available_, lc_available_msg = '', None

        report_on_related_chats = GROUPMATES_FOUND[language].format(groupmates_, group_chats_, lc_available_)
        return report_on_related_chats, lc_available_msg

    else:
        report_on_related_chats = GROUP_CHATS_FOUND[language].format(group_chats(num_group_chats, language))
        return report_on_related_chats, None


# ------------------------------------------------------------------------------------------- registration (exceptions)

ALREADY_REGISTERED = (
    (  # for groups
        '',
        "[g] ALREADY_REGISTERED",
        ''
    ),
    (  # for students
        '',
        "[s] ALREADY_REGISTERED",
        ''
    )
)
ONGOING_REGISTRATION = (
    '',
    "[s] ONGOING_REGISTRATION",
    ''
)
ALREADY_REGISTRATION = (
    '',
    "ALREADY_REGISTRATION",
    ''
)
INVALID_GROUP_NAME = (
    '',
    'INVALID_GROUP_NAME',
    ''
)
TOO_LONG_GROUP_NAME = (
    '',
    "Can you make it just {} characters shorter?",
    ''
)

# ------------------------------------------------------------------------------------------------- leader confirmation

CONFIRMATION_POLL_SENT = (
    '',
    "My creator has coded me to be incredulous, so I'm gonna ask your groupmates just to make sure",
    ''
)
LC_QUESTION = (
    '',
    '{} LEADER_CONFIRMATION_QUESTION',
    ''
)
YOU_CONFIRMED = (
    '',
    'YOU_CONFIRMED. Here are commands that are now available for you:{}',
    ''
)
LEADER_CONFIRMED = (
    '',
    "{} is confirmed to be your group's leader",
    ''
)
ASK_EDU_YEAR = (
    '',
    'ASK_EDU_YEAR',
    ''
)
GRADUATION_YEAR_SAVED = (
    '',
    'Ok, so you graduate in {}',
    ''
)

# ------------------------------------------------------------------------------------ leader confirmation (exceptions)

ALREADY_LEADER = (
    '',
    'ALREADY_LEADER',
    ''
)
ALREADY_LEADER_IN_GROUP = (
    '',
    'ALREADY_LEADER_IN_GROUP',
    ''
)
GROUP_CHAT_NEEDED = (
    '',
    'GROUP_CHAT_NEEDED',
    ''
)
NOT_ENOUGH_FOR_LC = (
    '',
    '{} groupmate(s) found, {} more needed',
    ''
)
ONGOING_LC = (
    '',
    'ONGOING_LEADER_CONFIRMATION {}',
    ''
)
ALREADY_LC = (
    '',
    'ALREADY_LEADER_CONFIRMATION',
    ''
)
CHEATING_IN_LC = (
    '',
    "{} CHEATING_IN_LEADER_CONFIRMATION",
    ''
)
LEADER_NOT_CONFIRMED = (
    '',
    "{} is confirmed not to be your group's leader. Oh what a shame to lie!",
    ''
)
YOU_NOT_CONFIRMED = (
    '',
    'YOU_NOT_CONFIRMED',
    ''
)
CANDIDATE_NOT_CONFIRMED = (
    '',
    "{} was confirmed not to be your group's leader, so you can use /claim again",
    ''
)
ONGOING_ENTERING_YEARS = (
    '',
    'ONGOING_ENTERING_YEARS',
    ''
)
INVALID_EDU_YEAR = (
    '',
    'INVALID_YEAR',
    ''
)
MULTIPLE_EDU_YEARS = (
    '',
    'MULTIPLE_YEARS',
    ''
)
INVALID_CURRENT_EDU_YEAR = (
    '',
    'If it was true, you would have already graduated) What are the years again?',
    ''
)
INVALID_ALL_EDU_YEARS = (
    '',
    "As far as I'm concerned, there's no way you'll study in the same group for {} years",
    ''
)

# ------------------------------------------------------------------------------------------------- displaying commands

COMMANDS = (  # these string are meant to be formatted to include non-ordinary commands
    '',

    'Commands that are available for you:\n\n'
    '/events — see your upcoming events\n'
    '/info — see info your group has saved'
    '{}'  # possible /ecampus
    '{}'  # possible non-ordinary commands
    '\n\n/feedback — make me better with feedback to my creator\n'
    '/leave — make us strangers again'
    '{}',  # possible message for displaying commands for the first time

    ''
)
FT_COMMANDS = (
    '',
    '\n\nBy the way, when you use a command for the first time, I explain how it works as we go',
    ''
)
ADMIN_COMMANDS = (
    '',

    '\n\n/new — add an upcoming event\n'
    '/cancel — cancel an upcoming event\n'
    '/save — save some info\n'
    '/delete — delete some info your group has saved\n'
    '/clear — delete all the info your group has saved',

    ''
)
LEADER_COMMANDS = (
    '',

    '\n\n/trust — add an admin\n'
    '/distrust — remove an admin\n'
    '/tell — send a message to all of your groupmates\n'
    '/ask — ask all of your groupmates a question\n'
    '/resign — give away your authorities',

    ''
)
KPI_CAMPUS_COMMAND = (
    '',

    '\n/ecampus !— let me let you know when changes happen in your e-campus account',

    ''
)

# -------------------------------------------------------------------------------------------------------- adding admin

FT_ASK_NEW_ADMIN = (
    '',
    'FT_ASK_NEW_ADMIN',
    ''
)
ASK_NEW_ADMIN = (
    '',
    'ASK_NEW_ADMIN',
    ''
)
YOU_NOW_ADMIN = (
    '',
    'YOU_NOW_ADMIN. New commands:{}',
    ''
)
NOW_ADMIN = (
    '',
    '{} is now an admin. Gonna let him know.',
    ''
)

# ------------------------------------------------------------------------------------------- adding admin (exceptions)

UNAVAILABLE_ADDING_ADMIN = (
    '',
    'UNAVAILABLE_ADDING_ADMIN',
    ''
)
ADMIN_LIMIT_REACHED = (
    '',
    'ADMIN_LIMIT_REACHED',
    ''
)
NO_GROUPMATES_TO_TRUST = (
    '',
    'NO_GROUPMATES_TO_TRUST',
    ''
)
ONGOING_ADDING_ADMIN = (
    '',
    'ONGOING_ADDING_ADMIN',
    ''
)
ALREADY_ADDING_ADMIN = (
    '',
    'ALREADY_ADDING_ADMIN',
    ''
)

# ------------------------------------------------------------------------------------------------------ removing admin

FT_ASK_ADMIN = (
    '',
    'FT_ASK_ADMIN',
    ''
)
ASK_ADMIN = (
    '',
    'ASK_ADMIN',
    ''
)
FT_ASK_TO_NOTIFY_FORMER = (
    '',
    "{} is not an admin anymore. Should I let them know? "
    "If you agree, I'll tell them they can no longer use the admin commands.",
    ''
)
ASK_TO_NOTIFY_FORMER = (
    '',
    '{} is not an admin anymore. Should I let them know?',
    ''
)
YOU_NO_MORE_ADMIN = (
    '',
    'YOU_NO_MORE_ADMIN',
    ''
)
FORMER_ADMIN_NOTIFIED = (
    '',
    'FORMER_NOTIFIED',
    ''
)
FORMER_NOT_NOTIFIED = (
    '',
    'FORMER_NOT_NOTIFIED',
    ''
)

# ----------------------------------------------------------------------------------------- removing admin (exceptions)

UNAVAILABLE_REMOVING_ADMIN = (
    '',
    'UNAVAILABLE_REMOVING_ADMIN',
    ''
)
ALREADY_NO_ADMINS = (
    '',
    'ALREADY_NO_ADMINS',
    ''
)
ONGOING_REMOVING_ADMIN = (
    '',
    'ONGOING_REMOVING_ADMIN',
    ''
)
ALREADY_REMOVING_ADMIN = (
    '',
    'ALREADY_REMOVING_ADMIN',
    ''
)

# --------------------------------------------------------------------------------------------------- displaying events

NO_EVENTS = (
    '',
    'NO_EVENTS',
    ''
)

# ---------------------------------------------------------------------------------------------- displaying information

NO_INFO = (
    '',
    'NO_INFO',
    ''
)

# --------------------------------------------------------------------------------------------- adding event (creating)

FT_ASK_NEW_EVENT = (
    '',
    'FT_ASK_NEW_EVENT',
    ''
)
ASK_NEW_EVENT = (
    '',
    'ASK_NEW_EVENT',
    ''
)
FT_ASK_DATE = (
    '',
    'FT_ASK_DATE',
    ''
)
ASK_DATE = (
    '',
    'ASK_DATE',
    ''
)

# -------------------------------------------------------------------------------- adding event (creating) (exceptions)

UNAVAILABLE_ADDING_EVENT = (
    '',
    'UNAVAILABLE_ADDING_EVENT',
    ''
)
ONGOING_ADDING_EVENT = (
    '',
    'ONGOING_ADDING_EVENT',
    ''
)
ALREADY_ADDING_EVENT = (
    '',
    'ALREADY_ADDING_EVENT',
    ''
)
INVALID_EVENT = (
    '',
    'INVALID_EVENT',
    ''
)
INVALID_DATE = (
    '',
    'INVALID_DATE',
    ''
)
MULTIPLE_DATES = (
    '',
    'MULTIPLE_DATES',
    ''
)
MONTH_OVER_12 = (
    '',
    'What are we gonna call the {} month of the year?) Let us deal with only 12 for now. What is the date again?',
    ''
)
MONTH_0 = (
    '',
    'I wonder what the 0th month would be called, "Zercember"?) What is the date again?',
    ''
)
DAY_OVER_MONTH_LENGTH = (
    '',
    'DAY_OVER_MONTH',
    ''
)
DAY_0 = (
    '',
    'DAY_0',
    ''
)
INVALID_HOUR = (
    '',
    'INVALID_HOUR',
    ''
)
INVALID_MINUTE = (
    '',
    'INVALID_MINUTE',
    ''
)

# -------------------------------------------------------------------------------------------- adding event (answering)

FT_NEW_EVENT = (
    '',
    'FT_NEW_EVENT:\n\n{}\n\n{}',
    ''
)
NEW_EVENT = (
    'Нова подія:\n\n{}\n\n{}',
    'New event:\n\n{}\n\n{}',
    ''
)
ASK_TO_NOTIFY = (
    ('Чи нагадувати мені про неї?', 'Мені варто нагадувати про неї?'),
    (
        'Should I notify you about it?',
        'Should I notify you about this one?',
        'Do you want me to notify you about it?',
        'Do you want me to notify you about this one?'
    ),
    ('', '')
)
EXPECT_NOTIFICATIONS = (
    '',
    'I will notify you',
    ''
)
EXPECT_NO_NOTIFICATIONS = (
    '',
    "I won't notify you",
    ''
)

# ------------------------------------------------------------------------------- adding event (answering) (exceptions)

ONGOING_ANSWERING_TO_NOTIFY = (
    '',
    'ONGOING_ANSWERING_TO_NOTIFY',
    ''
)
WOULD_EXPECT_NOTIFICATIONS = (
    '',
    'WOULD_EXPECT_NOTIFICATIONS',
    ''
)
WOULD_EXPECT_NO_NOTIFICATIONS = (
    '',
    'WOULD_EXPECT_NO_NOTIFICATIONS',
    ''
)

# ----------------------------------------------------------------------------------------------------- canceling event

FT_ASK_EVENT = (
    '',
    'FT_ASK_EVENT',
    ''
)
ASK_EVENT = (
    '',
    'ASK_EVENT',
    ''
)
EVENT_CANCELED = (
    '',
    'Canceled:\n\n{}',
    ''
)

# ---------------------------------------------------------------------------------------- canceling event (exceptions)

ALREADY_NO_EVENTS = (
    '',
    'ALREADY_NO_EVENTS',
    ''
)
UNAVAILABLE_CANCELING_EVENT = (
    '',
    'UNAVAILABLE_CANCELING_EVENT',
    ''
)
ONGOING_CANCELING_EVENT = (
    '',
    'ONGOING_CANCELING_EVENT',
    ''
)
ALREADY_CANCELING_EVENT = (
    '',
    'ALREADY_CANCELING_EVENT',
    ''
)

# -------------------------------------------------------------------------------------------------- saving information

FT_ASK_NEW_INFO = (
    '',
    'FT_ASK_NEW_INFO',
    ''
)
ASK_NEW_INFO = (
    '',
    'ASK_NEW_INFO',
    ''
)
NEW_INFO = (
    '',
    'NEW_INFO:\n\n{}',
    ''
)

# ------------------------------------------------------------------------------------- saving information (exceptions)

UNAVAILABLE_SAVING_INFO = (
    '',
    'UNAVAILABLE_SAVING_INFO',
    ''
)
ONGOING_SAVING_INFO = (
    '',
    'ONGOING_SAVING_INFO',
    ''
)
ALREADY_SAVING_INFO = (
    '',
    'ALREADY_SAVING_INFO',
    ''
)
INVALID_INFO = (
    '',
    'INVALID_INFO',
    ''
)

# ------------------------------------------------------------------------------------------------ deleting information

FT_ASK_INFO = (
    '',
    'FT_ASK_INFO',
    ''
)
ASK_INFO = (
    '',
    'ASK_INFO',
    ''
)
INFO_DELETED = (
    '',
    'INFO_DELETED:\n\n{}',
    ''
)

# ----------------------------------------------------------------------------------- deleting information (exceptions)

ALREADY_NO_INFO = (
    '',
    'ALREADY_NO_INFO',
    ''
)
UNAVAILABLE_DELETING_INFO = (
    '',
    'UNAVAILABLE_DELETING_INFO',
    ''
)
ONGOING_DELETING_INFO = (
    '',
    'ONGOING_DELETING_INFO',
    ''
)
ALREADY_DELETING_INFO = (
    '',
    'ALREADY_DELETING_INFO',
    ''
)

# ------------------------------------------------------------------------------------------------ clearing information

FT_ASK_CLEARING_INFO = (
    '',
    'FT_ASK_CLEARING_INFO',
    ''
)
ASK_CLEARING_INFO = (
    '',
    'ASK_CLEARING_INFO',
    ''
)
INFO_CLEARED = (
    '',
    'INFO_CLEARED',
    ''
)
INFO_KEPT = (
    '',
    'INFO_KEPT',
    ''
)

# ----------------------------------------------------------------------------------- clearing information (exceptions)

UNAVAILABLE_CLEARING_INFO = (
    '',
    'UNAVAILABLE_CLEARING_INFO',
    ''
)
ONGOING_CLEARING_INFO = (
    '',
    'ONGOING_CLEARING_INFO',
    ''
)
ALREADY_CLEARING_INFO = (
    '',
    'ALREADY_CLEARING_INFO',
    ''
)

# ----------------------------------------------------------------------------------------------------- notifying group

FT_ASK_MESSAGE = (
    '',
    'FT_ASK_MESSAGE',
    ''
)
ASK_MESSAGE = (
    '',
    'ASK_MESSAGE',
    ''
)
GROUP_NOTIFICATION = (
    '',
    '{} asked me to send this to everyone in your group:',
    ''
)
GROUP_NOTIFIED = (
    '',
    'GROUP_NOTIFIED {}',
    ''
)

# ---------------------------------------------------------------------------------------- notifying group (exceptions)

UNAVAILABLE_NOTIFYING_GROUP = (
    '',
    'UNAVAILABLE_NOTIFYING_GROUP',
    ''
)
NO_GROUPMATES_TO_NOTIFY = (
    '',
    'NO_GROUPMATES_TO_NOTIFY',
    ''
)
ONGOING_NOTIFYING_GROUP = (
    '',
    'ONGOING_NOTIFYING_GROUP',
    ''
)
ALREADY_NOTIFYING_GROUP = (
    '',
    'ALREADY_NOTIFYING_GROUP',
    ''
)

# --------------------------------------------------------------------------------------------- asking group (creating)

FT_ASK_QUESTION = (
    '',
    'FT_ASK_QUESTION',
    ''
)
ASK_QUESTION = (
    '',
    'ASK_QUESTION',
    ''
)
FT_ASK_TO_PUBLISH = (
    '',
    'FT_ASK_TO_PUBLISH',
    ''
)
ASK_TO_PUBLISH = (
    '',
    'ASK_TO_PUBLISH',
    ''
)

ANSWER_LIST = '"{}"{}{}{}'
ANSWERED = (
    '',
    '\n\nAnswers:\n\n{}',
    ''
)
REFUSED = (
    '',
    '\n\nRefused to answer:\n{}',
    ''
)
ASKED = (
    '',
    '\n\nNo response:\n{}',
    ''
)
STOP_ASKING_GROUP = (
    '',
    'STOP_ASKING_GROUP',
    ''
)

# -------------------------------------------------------------------------------- asking group (creating) (exceptions)

UNAVAILABLE_ASKING_GROUP = (
    '',
    'UNAVAILABLE_ASKING_GROUP',
    ''
)
NO_GROUPMATES_TO_ASK = (
    '',
    'NO_GROUPMATES_TO_ASK',
    ''
)
ONGOING_GROUP_ANSWERING = (
    '',
    'ONGOING_GROUP_ANSWERING',
    ''
)
ONGOING_ASKING_GROUP = (
    '',
    'ONGOING_ASKING_GROUP',
    ''
)
ALREADY_ASKING_GROUP = (
    '',
    'ALREADY_ASKING_GROUP',
    ''
)

# -------------------------------------------------------------------------------------------- asking group (answering)

FT_ASK_ANSWER = (
    '',
    'FT_ASK_ANSWER {}',
    ''
)
ASK_ANSWER = (
    '',
    'ASK_ANSWER {}',
    ''
)
PUBLIC_ANSWER = (
    '',
    ' {} made the answers public, so all the answers can be seen in the group chat.',
    ''
)
PRIVATE_ANSWER = (
    '',
    " {} didn't make the answers public, so they are the only person who will be able to see your answer."
    ''
)
ASK_LEADER_ANSWER = (
    '',
    'ASK_LEADER_ANSWER',
    ''
)
REFUSE_TO_ANSWER = (
    '',
    'REFUSE_TO_ANSWER',
    ''
)
ANSWER_SENT = (
    '',
    'ANSWER_SENT',
    ''
)
REFUSAL_SENT = (
    '',
    'REFUSAL_SENT',
    ''
)
ALL_ANSWERED = (
    '',
    'ALL_ANSWERED "{}"',
    ''
)
GROUP_ASKING_TERMINATED = (
    (
        '',
        '[l] GROUP_ASKING_TERMINATED',
        ''
    ),
    (
        '',
        '[s] GROUP_ASKING_TERMINATED',
        ''
    ),
)

# ------------------------------------------------------------------------------- asking group (answering) (exceptions)

ONGOING_ANSWERING = (
    '',
    'ONGOING_ANSWERING',
    ''
)

# ----------------------------------------------------------------------------------------------------- changing leader

FT_ASK_NEW_LEADER = (
    '',
    'FT_ASK_NEW_LEADER',
    ''
)
ASK_NEW_LEADER = (
    '',
    'ASK_NEW_LEADER',
    ''
)
YOU_NOW_LEADER = (
    '',
    'YOU_NOW_LEADER. Here are commands that are now available for you:{}',
    ''
)
NOW_LEADER = (
    '',
    "{} is now your group's leader. Gonna let them know.",
    ''
)

# ---------------------------------------------------------------------------------------- changing leader (exceptions)

UNAVAILABLE_CHANGING_LEADER = (
    '',
    'UNAVAILABLE_CHANGING_LEADER',
    ''
)
NO_GROUPMATES_FOR_RESIGN = (
    '',
    'NO_GROUPMATES',
    ''
)
ONGOING_CHANGING_LEADER = (
    '',
    'ONGOING_CHANGING_LEADER',
    ''
)
ALREADY_CHANGING_LEADER = (
    '',
    'ALREADY_CHANGING_LEADER',
    ''
)

# ---------------------------------------------------------------------------------------------------- sending feedback

FT_ASK_FEEDBACK = (
    '',
    'FT_ASK_FEEDBACK',
    ''
)
ASK_FEEDBACK = (
    '',
    'ASK_FEEDBACK',
    ''
)
FEEDBACK_SENT = (
    '',
    'FEEDBACK_SENT',
    ''
)

# --------------------------------------------------------------------------------------- sending feedback (exceptions)

FEEDBACK_CONDITION = (
    '',
    'FEEDBACK_CONDITION',
    ''
)
ONGOING_SENDING_FEEDBACK = (
    '',
    'ONGOING_SENDING_FEEDBACK',
    ''
)
ALREADY_SENDING_FEEDBACK = (
    '',
    'ALREADY_SENDING_FEEDBACK',
    ''
)

# ------------------------------------------------------------------------------------------------------- deleting data

FT_ASK_LEAVING = (
    '',
    'FT_ASK_LEAVING',
    ''
)
ASK_LEAVING = (
    '',
    'ASK_LEAVING',
    ''
)
DATA_DELETED = (
    '',
    'DATA_DELETED',
    ''
)
DATA_KEPT = (
    '',
    'DATA_KEPT',
    ''
)

# ------------------------------------------------------------------------------------------ deleting data (exceptions)

LEAVING_IN_GROUPS = (
    '',
    'LEAVING_IN_GROUPS',
    ''
)
RESIGN_FIRST = (
    '',
    'RESIGN_FIRST',
    ''
)
ONGOING_LEAVING = (
    '',
    'ONGOING_LEAVING',
    ''
)
ALREADY_LEAVING = (
    '',
    'ALREADY_LEAVING',
    ''
)

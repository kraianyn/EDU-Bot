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
BOTH_FOUND = (
    '',
    '{} groupmate(s) and {} group chat(s) found',
    ''
)
GROUPMATES_FOUND = (
    '',
    '{} groupmate(s) found',
    ''
)
GROUP_CHATS_FOUND = (
    '',
    '{} group chat(s) found',
    ''
)
NONE_FOUND = (
    '',
    "By the way, you are the first student from your group I know of. For me to know that students are from the same "
    "group, they need to enter the same group name (the case doesn't matter), which is {} for your group.",
    ''
)
NEW_GROUPMATE = (
    ('', ''),
    ("{} has just registered", '{} told me they are your groupmate', 'Now I know that {} is from your group'),
    ('', '')
)
STUDENTS_FOUND = (
    '',
    '{} student(s) found:\n\n{}',
    ''
)
NO_STUDENTS_FOUND = (
    '',
    '{} NO_STUDENTS_FOUND',
    ''
)

# ------------------------------------------------------------------------------------------- registration (exceptions)

ALREADY_REGISTERED = (
    '',
    'ALREADY_REGISTERED',
    ''
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
LEADER_CONFIRMATION_QUESTION = (
    '',
    '{} LEADER_CONFIRMATION_QUESTION',
    ''
)
LEADER_CONFIRMED = (
    '',
    "{} is confirmed to be your group's leader",
    ''
)
YOU_CONFIRMED = (
    '',
    'YOU_CONFIRMED',
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
NOT_ENOUGH_FOR_LEADER_CONFIRMATION = (
    '',
    '{} groupmate(s) found, {} more needed',
    ''
)
ONGOING_LEADER_CONFIRMATION = (
    '',
    'ONGOING_LEADER_CONFIRMATION',
    ''
)
ALREADY_LEADER_CONFIRMATION = (
    '',
    'ALREADY_LEADER_CONFIRMATION',
    ''
)
CHEATING_IN_LEADER_CONFIRMATION = (
    '',
    "{} CHEATING_IN_LEADER_CONFIRMATION",
    ''
)
ALREADY_CLAIMED = (
    '',
    '{} ALREADY_CLAIMED',
    ''
)
CANDIDATE_NOT_CONFIRMED = (
    '',
    '{} CANDIDATE_NOT_CONFIRMED',
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

# ------------------------------------------------------------------------------------------------- displaying commands

COMMANDS = (  # these string are meant to be formatted to include non-ordinary commands
    '',

    'Commands that are available for you:\n\n'
    '/events — see your upcoming events\n'
    '/info — see info your group has saved'
    '{}'  # possible /ecampus
    '{}'  # possible non-ordinary commands
    '\n\n/feedback !— make me better with feedback to my creator\n'
    '/leave — make us strangers again'
    '{}',

    ''
)
FT_COMMANDS = (
    '',
    '\n\nBy the way, when you use a command for the first time, I explain how it works as we go',
    ''
)
ADMIN_COMMANDS = (  # leader commands
    '',

    '\n\n/new — add an upcoming event\n'
    '/cancel — cancel an upcoming event\n'
    '/save — save some info\n'
    '/delete — delete some info your group has saved\n'
    '/clear — delete all the info your group has saved',

    ''
)
LEADER_COMMANDS = (  # leader commands
    '',

    '\n\n/trust — add an admin\n'
    '/distrust — remove an admin\n'
    '/tell !— send a message to all of your groupmates\n'
    '/ask !— ask all of your groupmates a question\n'
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

ONGOING_ANSWERING_TO_NOTIFY = (
    '',
    'ONGOING_ANSWERING_TO_NOTIFY',
    ''
)
FT_NEW_EVENT = (
    '',
    'FT_NEW_EVENT:\n\n{}\n\n{}',
    ''
)
NEW_EVENT = (
    '',
    'New event:\n\n{}\n\n{}',
    ''
)
ASK_TO_NOTIFY = (
    ('', ''),
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

# -------------------------------------------------------------------------------------------------------- asking group

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
ONGOING_ANSWERING = (
    '',
    'ONGOING_ANSWERING',
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

# ------------------------------------------------------------------------------------------- asking group (exceptions)

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
    'YOU_NOW_LEADER. New commands:{}',
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

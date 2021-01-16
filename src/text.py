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

# --------------------------------------------------------------------------------------------- registration exceptions

ALREADY_REGISTERED = (
    '',
    'ALREADY_REGISTERED',
    ''
)
ALREADY_REGISTRATION = (
    '',
    "ALREADY_REGISTRATION",
    ''
)
ONGOING_REGISTRATION = (
    '',
    "[s] ONGOING_REGISTRATION",
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
    'CONFIRMATION_POLL_SENT',
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

# -------------------------------------------------------------------------------------- leader confirmation exceptions

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
ALREADY_LEADER_CONFIRMATION = (
    '',
    'ALREADY_LEADER_CONFIRMATION',
    ''
)
ONGOING_LEADER_CONFIRMATION = (
    '',
    'ONGOING_LEADER_CONFIRMATION',
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
    '{}'  # possible command for KPI students
    '{}'  # possible non-ordinary commands
    '\n\n/help command — see description for the command\n'
    '/feedback !— make me better with feedback to my creator\n'
    '/leave — make us strangers again',

    ''
)
ADMIN_COMMANDS = (  # leader commands
    '',

    '\n\n/new — add an upcoming event\n'
    '/cancel !— cancel an upcoming event\n'
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

    '\n/campus !— let me let you know when changes happen in your e-campus account',

    ''
)

# -------------------------------------------------------------------------------------------------------- adding admin

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

# --------------------------------------------------------------------------------------------- adding admin exceptions

UNAVAILABLE_ADDING_ADMIN = (
    '',
    'UNAVAILABLE_ADDING_ADMIN',
    ''
)
NO_GROUPMATES_TO_TRUST = (
    '',
    'NO_GROUPMATES_TO_TRUST',
    ''
)
ADMIN_LIMIT_REACHED = (
    '',
    'ADMIN_LIMIT_REACHED',
    ''
)
ALREADY_ADDING_ADMIN = (
    '',
    'ALREADY_ADDING_ADMIN',
    ''
)
ONGOING_ADDING_ADMIN = (
    '',
    'ONGOING_ADDING_ADMIN',
    ''
)

# ------------------------------------------------------------------------------------------------------ removing admin

ASK_ADMIN = (
    '',
    'ASK_ADMIN',
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
FORMER_ADMIN_NOT_NOTIFIED = (
    '',
    'FORMER_ADMIN_NOT_NOTIFIED',
    ''
)

# ------------------------------------------------------------------------------------------- removing admin exceptions

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
ALREADY_REMOVING_ADMIN = (
    '',
    'ALREADY_REMOVING_ADMIN',
    ''
)
ONGOING_REMOVING_ADMIN = (
    '',
    'ONGOING_REMOVING_ADMIN',
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

# --------------------------------------------------------------------------------- connecting e-campus account
# -------------------------------------------------------------------------------------------------------- adding event

ASK_NEW_EVENT = (
    '',
    'ASK_NEW_EVENT',
    ''
)
ASK_DATE = (
    '',
    'ASK_DATE',
    ''
)

# ----------------------------------------------------------------------------------------- connecting e-campus account

ECAMPUS_ACCOUNT_ACCESS = (
    '',
    'ECAMPUS_ACCOUNT_ACCESS',
    ''
)

# --------------------------------------------------------------------------------------------- adding event exceptions

UNAVAILABLE_ADDING_EVENT = (
    '',
    'UNAVAILABLE_ADDING_EVENT',
    ''
)
ALREADY_ADDING_EVENT = (
    '',
    'ALREADY_ADDING_EVENT',
    ''
)
ONGOING_ADDING_EVENT = (
    '',
    'ONGOING_ADDING_EVENT',
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

# -------------------------------------------------------------------------------------------------- saving information

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

# --------------------------------------------------------------------------------------- saving information exceptions

UNAVAILABLE_SAVING_INFO = (
    '',
    'UNAVAILABLE_SAVING_INFO',
    ''
)
ALREADY_SAVING_INFO = (
    '',
    'ALREADY_SAVING_INFO',
    ''
)
ONGOING_SAVING_INFO = (
    '',
    'ONGOING_SAVING_INFO',
    ''
)
INVALID_INFO = (
    '',
    'INVALID_INFO',
    ''
)

# ------------------------------------------------------------------------------------------------ deleting information

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

# ------------------------------------------------------------------------------------- deleting information exceptions

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
ALREADY_DELETING_INFO = (
    '',
    'ALREADY_DELETING_INFO',
    ''
)
ONGOING_DELETING_INFO = (
    '',
    'ONGOING_DELETING_INFO',
    ''
)

# ------------------------------------------------------------------------------------------------ clearing information

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

# ------------------------------------------------------------------------------------- clearing information exceptions

UNAVAILABLE_CLEARING_INFO = (
    '',
    'UNAVAILABLE_CLEARING_INFO',
    ''
)
ALREADY_CLEARING_INFO = (
    '',
    'ALREADY_CLEARING_INFO',
    ''
)
ONGOING_CLEARING_INFO = (
    '',
    'ONGOING_CLEARING_INFO',
    ''
)

# ----------------------------------------------------------------------------------------------------- changing leader

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
    "{} is now your group's leader",
    ''
)

# ------------------------------------------------------------------------------------------ changing leader exceptions

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
ALREADY_CHANGING_LEADER = (
    '',
    'ALREADY_CHANGING_LEADER',
    ''
)
ONGOING_CHANGING_LEADER = (
    '',
    'ONGOING_CHANGING_LEADER',
    ''
)

# ---------------------------------------------------------------------------------------------- displaying description

REGISTRATION_DESCRIPTION = (
    '',
    'Remember when we first met?)',
    ''
)
LEADER_CONFIRMATION_DESCRIPTION = (
    '',
    'LEADER_CONFIRMATION_DESCRIPTION.',
    ''
)
ADDING_ADMIN_DESCRIPTION = (
    '',
    'ADDING_ADMIN_DESCRIPTION.',
    ''
)
REMOVING_ADMIN_DESCRIPTION = (
    '',
    'REMOVING_ADMIN_DESCRIPTION.',
    ''
)
DISPLAYING_COMMANDS_DESCRIPTION = (
    '',
    "I'm sure that you're good but whatever... This command will display all commands that are available for you. "
    "With a brief description. That's it.",
    ''
)
DISPLAYING_EVENTS_DESCRIPTION = (
    '',
    'DISPLAYING_EVENTS_DESCRIPTION.',
    ''
)
DISPLAYING_INFO_DESCRIPTION = (
    '',
    'DISPLAYING_INFO_DESCRIPTION.',
    ''
)
ADDING_EVENT_DESCRIPTION = (
    '',
    'ADDING_EVENT_DESCRIPTION.',
    ''
)
SAVING_INFO_DESCRIPTION = (
    '',
    'SAVING_INFO_DESCRIPTION.',
    ''
)
DELETING_INFO_DESCRIPTION = (
    '',
    'DELETING_INFO_DESCRIPTION.',
    ''
)
CLEARING_INFO_DESCRIPTION = (
    '',
    'CLEARING_INFO_DESCRIPTION.',
    ''
)
CHANGING_LEADER_DESCRIPTION = (
    '',
    'CHANGING_LEADER_DESCRIPTION.',
    ''
)
DISPLAYING_DESCRIPTION_DESCRIPTION = (
    '',
    'DISPLAYING_DESCRIPTION_DESCRIPTION',
    ''
)
LEAVING_DESCRIPTION = (
    '',
    'LEAVING_DESCRIPTION.',
    ''
)

# ----------------------------------------------------------------------------------- displaying description exceptions

CONTROVERSIAL_DESCRIPTION_REQUEST = (
    '',
    'Good one.',
    ''
)
INVALID_DESCRIPTION_REQUEST = (
    '',
    'Ok... so what do you want me to help you with?',
    ''
)
REMEMBER_UNAVAILABLE = (
    '',
    ' REMEMBER_UNAVAILABLE.',
    ''
)

# ------------------------------------------------------------------------------------------------------------- leaving

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

# -------------------------------------------------------------------------------------------------- leaving exceptions

LEAVING_IN_GROUPS = (
    '',
    'LEAVING_IN_GROUPS',
    ''
)
ALREADY_LEAVING = (
    '',
    'ALREADY_LEAVING',
    ''
)
ONGOING_LEAVING = (
    '',
    'ONGOING_LEAVING',
    ''
)

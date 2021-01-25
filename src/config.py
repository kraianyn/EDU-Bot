from re import compile

from telegram import Chat

LANGUAGES = ('українська', 'English', 'русский')
CHAT_TYPES = (Chat.PRIVATE, Chat.GROUP, Chat.SUPERGROUP)
ORDINARY_ROLE, ADMIN_ROLE, LEADER_ROLE = 0, 1, 2

DATABASE = '../memory.db'
STATIC_INITIAL_STUDENT = (
    ORDINARY_ROLE,  # role in the group
    '000000000000000'  # familiarity with the bot's interactions according to src.auxiliary.Familiarity fields
)
KPI_ID = 100

MAX_GROUP_NAME_LENGTH = 15
MIN_GROUPMATES_FOR_LEADER_CONFORMATION = 1
MAX_UA_EDU_YEARS, MAX_ADMINS_STUDENTS_RATIO = 6, .5

DATE_PATTERN = compile(r'.*?(\d{1,2})\.(\d{1,2})(,? (\d{1,2}):(\d{1,2}))?.*?')

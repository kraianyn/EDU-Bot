from re import compile

from telegram import Chat

LANGUAGES = ('українська', 'English', 'русский')
CHAT_TYPES = (Chat.PRIVATE, Chat.GROUP, Chat.SUPERGROUP)
ORDINARY_ROLE, ADMIN_ROLE, LEADER_ROLE = 0, 1, 2

THRESHOLD = (8, 31)  # August 31, when the next EDU year starts

DATABASE = '../memory.db'
STATIC_INITIAL_STUDENT = (
    ORDINARY_ROLE,  # role in the group
    '000000000000000'  # familiarity with the bot's interactions according to src.auxiliary.Familiarity fields
)
KPI_ID = 100

MAX_GROUP_NAME_LENGTH = 15
MIN_GROUPMATES_FOR_LC = 1  # LC = LEADER CONFIRMATION
MAX_EDU_YEARS, MAX_ADMINS_STUDENTS_RATIO = 6, .5

EDU_YEAR_PATTERN = compile(r'(\d)+.+?(\d)+')
DATE_PATTERN = compile(r'(\d{1,2})\.(\d{1,2})(,? (\d{1,2}):(\d{1,2}))?')

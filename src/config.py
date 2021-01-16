from collections import namedtuple
from re import compile
from telegram import Chat

BOT_LOG, BOT_LOG_FORMAT = '../log/bot.log', '%(levelname)s | %(asctime)s.%(msecs)d | %(name)s | %(message)s'
COMMUNICATION_LOG, NOTIFICATION_LOG = '../log/communication.log', '../log/notification.log'
LOG_FORMAT, TIME_FORMAT = '%(levelname)s | %(asctime)s | %(message)s', '%Y.%m.%d %H:%M:%S'

Command = namedtuple('Command', 'manager, role, interaction, description')
ChatRecord = namedtuple('ChatRecord', 'id, type, username, language, group_id, role, timetable, familiar, registered')
GroupRecord = namedtuple('GroupRecord', 'id, name, year, info, events')

DATABASE = 'memory.db'
DEFAULT_USER = (
    0,  # role in the group (0 for ordinary, 1 for admin, 2 for leader)
    '',  # timetable (points in time (in minutes) before the event when notifications are sent)
    ''  # familiarity with the bot's features in the sequence respectively:
    #
)
KPI_ID = 100

LANGUAGES = ('українська', 'English', 'русский')
CHAT_TYPES = (Chat.PRIVATE, Chat.GROUP, Chat.SUPERGROUP)
ORDINARY_ROLE, ADMIN_ROLE, LEADER_ROLE = 0, 1, 2

MAX_GROUP_NAME_LENGTH = 15
MIN_GROUPMATES_FOR_LEADER_CONFORMATION = 1
MAX_UA_EDU_YEARS, MAX_ADMINS_STUDENTS_RATIO = 6, .5

DATE_PATTERN = compile(r'.*?(\d{1,2})\.(\d{1,2})(,? (\d{1,2}):(\d{1,2}))?.*?')

import logging

BOT_LOG, BOT_LOG_FORMAT = 'log/bot.log', '%(levelname)s | %(asctime)s.%(msecs)d | %(name)s | %(message)s'
COMMUNICATION_LOG, NOTIFICATION_LOG = 'log/communication.log', 'log/notification.log'
LOG_FORMAT, TIME_FORMAT = '%(levelname)s | %(asctime)s | %(message)s', '%Y.%m.%d %H:%M:%S'

# ------------------------------------------------------------------------------------------------------------- loggers

cl = logging.getLogger('communication')  # communication logger
file_handler = logging.FileHandler(COMMUNICATION_LOG, 'w', 'utf8')
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, TIME_FORMAT))
cl.addHandler(file_handler)
cl.setLevel(logging.DEBUG)

# ----------------------------------------------------------------------------------------------------------------- bot

GRADUATES = '{} graduates, {} chats deleted'
CT_STARTS, NT_STARTS = 'communication thread starts', 'notification thread starts'

# ------------------------------------------------------------------------------------------------------- communication

UNAVAILABLE_COMMAND = '{} uses /{} with role {}'
STARTS_NOT_PRIVATELY = '{} is invited to continue {} privately'
STARTS, ENDS, INTERRUPTS = '{} starts {}', '{} ends {}', '{} uses /{} during {}'
BECOMES_FAMILIAR = '{} becomes familiar with "{}" interaction'

START_BEING_REGISTERED, REGISTERS = '{} uses /start being registered', '{} registers as from {}'
GROUP_LANGUAGE_UPDATED = 'language of {} is now {}, spoken by {}'
LEAVE_NOT_PRIVATELY, LEAVES, STAYS = '{} uses /leave in non-private {}', '{} leaves', '{} refuses to leave'

COMMANDS = '{} displays commands'

CLAIM_BEING_LEADER, CLAIM_WITH_LEADER = '{} uses /claim being a leader', "{} uses /claim when the group has a leader"
CLAIM_WITHOUT_ENOUGH, CLAIM_WITHOUT_CHAT = '{} uses /claim with {} groupmates', '{} uses /claim without a group chat'
CLAIMS_LATE = '{} uses /claim when {} is being confirmed'
CONFIRMED, NOT_CONFIRMED = '{} is confirmed to be the leader', '{} is confirmed not to be the leader'
ENTERS_EDU_YEAR = '{} enters the EDU year: {}/{}'

TRUST_OVER_LIMIT = '{} uses /trust when {}/{} in the group are admins'
TRUST_ALONE = '{} attempts to add an admin being alone'
NOW_ADMIN = '{} is made an admin'
DISTRUST_WITHOUT_ADMINS = '{} attempts to remove an admin without admins'
NO_MORE_ADMIN, FORMER_NOTIFIED = '{} is no more an admin', '{} is notified that they are no more an admin'

INVOLVING_GROUP_ALONE = '{} uses /{} alone'
NOW_LEADER = "{} is made the leader"

ADDS, ASKED_EVENT = '{} adds "{}"', 'students of {} are asked about "{}"'
ADDS_DUPLICATE = '{} attempts to add a duplicate of "{}"'
AGREES, DISAGREES = '{} agrees to be notified about "{}"', '{} disagrees to be notified about "{}"'
AGREES_LATE = '{} agrees to be notified about "{}" after it has passed'
DISAGREES_LATE = '{} disagrees to be notified about "{}" after it has passed'
ALL_ANSWERED_EVENT = 'all students of {} have answered concerning reminding about "{}"'
CANCEL_WITHOUT_EVENTS, CANCELS = '{} uses /cancel without events', '{} cancels "{}"'

SAVES, CLEARS, KEEPS = '{} saves "{}"', "{} clears info", "{} refuses to clear info"
DELETE_WITHOUT_INFO, DELETES = "{} uses /{} without info", '{} deletes "{}"'

NOTIFIED = 'students of {} are notified about "{}"'
MAKES_PUBLIC, MAKES_NON_PUBLIC = '{} makes the answers public', '{} makes the answers non-public'
ASKED = 'students of {} are asked "{}"'
ANSWERS, REFUSES = '{} answers with "{}"', '{} refuses to answer'
ALL_ANSWERED, TERMINATES = 'all students of {} have answered', '{} terminates asking'

SENDS_FEEDBACK = '{} sends feedback "{}"'

INFO, EVENTS = '{} displays info', '{} displays events'

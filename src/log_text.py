# ----------------------------------------------------------------------------------------------------------------- bot

CT_STARTS, NT_STARTS = 'communication thread starts', 'notification thread starts'

# ------------------------------------------------------------------------------------------------------- communication

CUT_LENGTH = 40  # included user text is cut to this length, linebreaks are also replaced with spaces

UNAVAILABLE_COMMAND = '{} uses /{} with role {}'
STARTS_NOT_PRIVATELY = '{} is invited to continue {} privately'
STARTS, ENDS, INTERRUPTS = '{} starts {}', '{} ends {}', '{} uses /{} during {}'
BECOMES_FAMILIAR = '{} becomes familiar with {}'

START_BEING_REGISTERED, REGISTERS = '{} uses /start being registered', '{} registers as from {}'
LEAVE_NOT_PRIVATELY, LEAVES, STAYS = '{} uses /leave in non-private {}', '{} leaves from {}', '{} refuses to leave'

COMMANDS = '{} displays commands'

CLAIM_BEING_LEADER = '{} uses /claim being a leader'
CLAIM_WITH_LEADER = "{} uses /claim when the group has a leader"
CLAIM_WITH_NOT_ENOUGH = '{} uses /claim with {} registered students'
CLAIM_WITHOUT_GROUP_CHAT = '{} uses /claim without group chats'
CONFIRMED, NOT_CONFIRMED = '{} is confirmed to be the leader', '{} is confirmed not to be the leader'
CLAIMS_LATE = '{} uses /claim when {} is being confirmed'

TRUST_OVER_LIMIT = '{} uses /trust when {}/{} in the group are admins'
TRUST_ALONE = '{} attempts to add an admin being alone'
NOW_ADMIN = '{} is made an admin'
DISTRUST_WITHOUT_ADMINS = '{} attempts to remove an admin without admins'
NO_MORE_ADMIN, FORMER_NOTIFIED = '{} is no more an admin', '{} is notified that they are no more an admin'

INVOLVING_GROUP_ALONE = '{} uses /{} alone'
NOW_LEADER = "{} is made the leader"

ADDS = '{} adds "{}"'
AGREES, DISAGREES = '{} agrees to be notified about "{}"', '{} disagrees to be notified about "{}"'
AGREES_LATE = '{} agrees to be notified about "{}" after it has passed'
DISAGREES_LATE = '{} disagrees to be notified about "{}" after it has passed'
ALL_ANSWERED_TO_NOTIFY = 'all students of {} have answered concerning reminding about "{}"'
CANCEL_WITHOUT_EVENTS, CANCELS = '{} uses /cancel without events', '{} cancels "{}"'

SAVES, CLEARS, KEEPS = '{} saves "{}"', "{} clears info", "{} refuses to clear info"
DELETE_WITHOUT_INFO, DELETES = "{} uses /{} without info", '{} deletes "{}"'

NOTIFIES = '{} notifies the group with "{}"'
MAKES_PUBLIC, MAKES_NON_PUBLIC = '{} makes the answers public', '{} chooses to not make the answers public'
ASKED = 'students of {} are asked "{}"'
ANSWERS, REFUSES = '{} answers with "{}"', '{} refuses to answer'
ALL_ANSWERED, TERMINATES = 'all students of {} have answered', '{} terminates asking'

SENDS_FEEDBACK = '{} sends feedback "{}"'

INFO, EVENTS = '{} displays info', '{} displays events'

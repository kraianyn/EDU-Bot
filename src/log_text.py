# ----------------------------------------------------------------------------------------------------------------- bot

CT_STARTS, NT_STARTS = 'communication thread starts', 'notification thread starts'

# ------------------------------------------------------------------------------------------------------- communication

UNAVAILABLE_COMMAND = '{} uses /{} with role {}'
STARTS_NOT_PRIVATELY = '{} is invited to continue {} privately'
STARTS, ENDS, INTERRUPTS = '{} starts {}', '{} ends {}', '{} uses /{} during {}'
BECOMES_FAMILIAR = '{} becomes familiar with {}'

START_BEING_REGISTERED, REGISTERS = '{} uses /start already being registered', '{} registers as from {}'
LEAVE_NOT_PRIVATELY, LEAVES, STAYS = '{} uses /leave in non-private {}', '{} leaves from {}', '{} refuses to leave'

COMMANDS = '{} displays commands'

CLAIM_BEING_LEADER = '{} uses /claim already being a leader'
CLAIM_WITH_LEADER = "{} uses /claim when the group's leader is {}"
CLAIM_WITH_NOT_ENOUGH = '{} uses /claim with only {} students registered'
CLAIM_WITHOUT_GROUP_CHAT = '{} uses /claim when no group chats have been registered'
CONFIRMED, NOT_CONFIRMED = '{} is confirmed to be the leader of {}', '{} is confirmed not to be the leader of {}'
CLAIMS_LATE = '{} uses /claim when {} is already being confirmed'

TRUST_OVER_LIMIT = '{} uses /trust when {}/{} in the group are admins'
TRUST_WITHOUT_GROUPMATES = '{} attempts to add an admin being the only registered student from {}'
ADDS_ADMIN = '{} makes {} an admin'
DISTRUST_WITHOUT_ADMINS = '{} attempts to remove an admin when there are no admins in {}'
REMOVES_ADMIN, FORMER_NOTIFIED = '{} unmakes {} an admin', '{} is notified that they are no more an admin'

INVOLVING_GROUP_ALONE = '{} uses /{} being the only registered one from {}'
CHANGES_LEADER = "{} makes {} the leader of {}"

CUT_LENGTH = 40  # included user text is cut to this length, linebreaks are also replaced with spaces

SAVES, CLEARS, KEEPS = '{} saves "{}" to info of {}', "{} clears info of {}", "{} refuses to clear the group's info"
DELETE_WITHOUT_INFO, DELETES = "{} uses /{} when the info of {} is empty", '{} deletes "{}" from info of {}'

ADDS = '{} adds "{}" to events of {}'
AGREES, DISAGREES = '{} agrees to be notified about "{}"', '{} disagrees to be notified about "{}"'
AGREES_LATE = '{} agrees to be notified about "{}" after it has passed'
DISAGREES_LATE = '{} disagrees to be notified about "{}" after it has passed'
LAST_ANSWERS = 'all students of {} have answered concerning "{}"'
CANCEL_WITHOUT_EVENTS, CANCELS = '{} uses /cancel when {} has no events', '{} cancels "{}" of events of {}'

NOTIFIES, ASKS = '{} notifies students of {} with "{}"', '{} asks students of {} "{}"'
ANSWERS, REFUSES = '{} asked "{}"', '{} refuses to answer '

INFO, EVENTS = '{} displays saved info', '{} displays upcoming events'

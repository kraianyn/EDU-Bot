from typing import Union
from sqlite3 import connect
from auxiliary import get_chat_record
import src.interactions as i
import src.config as c
import src.log_text as lt
import src.text as t
from bot_info import USERNAME
from telegram import Update, Chat, Message


def registration(update: Update, reply_to_message_id: Union[int, None]):
    """
    This function is called when a chat uses the command /start. It is responsible for deciding whether
    src.interactions.Registration interaction will be started, which is the case if the chat is not already registered
    and is not already registering. Otherwise, the bot sends a message explaining why the interaction cannot be started,
    which is a reply in non-private chats.

    Args:
        update (telegram.Update): update received after the command is used.
        reply_to_message_id (int or None): id of the message that the response will be a reply to. None disables the
            reply.
    """
    chat = update.effective_chat

    if not (chat_record := get_chat_record(chat.id)):  # if the chat is not already registered
        if chat.id not in i.current:  # if the chat is not already registering
            i.Registration(chat.id, chat.type)
        else:  # if the chat is already registering
            i.current[chat.id].respond(i.Registration.COMMAND, update.effective_message)
    else:  # if the chat is already registered
        chat.send_message(t.ALREADY_REGISTERED[chat_record.language], reply_to_message_id=reply_to_message_id)
        i.cl.info(lt.START_BEING_REGISTERED.format(chat.id))


def leader_confirmation(record: c.ChatRecord, update: Update):
    """
    This function is called when a registered user uses the command /claim. It is responsible for deciding whether
    src.interactions.LeaderConfirmation interaction makes sense to be started. If it does, an attempt to start the
    interaction is made by calling src.managers.attempt_interaction. Otherwise, the bot sends a message explaining why
    the interaction cannot be started, which is a reply in non-private chats.

    Args: see src.managers.leaving.__doc__.
    """
    chat, message = update.effective_chat, update.effective_message
    is_private = chat.type == Chat.PRIVATE

    if record.role == c.LEADER_ROLE:  # is the user is already a leader
        message.reply_text(t.ALREADY_LEADER[record.language], quote=not is_private)
        i.cl.info(lt.CLAIM_BEING_LEADER.format(record.id))
        return

    connection = connect(c.DATABASE)
    cursor = connection.cursor()

    cursor.execute(  # record of the leader of the user's group
        'SELECT id FROM chats WHERE group_id = ? AND role = 2',
        (record.group_id,)
    )
    leader = cursor.fetchone()

    if not leader:  # if there is no leader in the group
        cursor.execute(  # record of the group's first registered group chat
            'SELECT id, language FROM chats WHERE group_id = ? AND type <> 0',
            (record.group_id,)
        )
        group_chat_record = cursor.fetchone()

        if group_chat_record:  # if the group has registered a group chat
            cursor.execute(  # number of registered students from the group
                'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
                (record.group_id,)
            )
            num_groupmates = cursor.fetchone()[0] - 1

            # if many enough students in the group are registered
            if num_groupmates >= c.MIN_GROUPMATES_FOR_LEADER_CONFORMATION:

                is_having = group_chat_record[0] in i.current  # whether the group chat is having an interaction
                # if the group chat is not having an interaction or the interaction is not leader confirmation
                if not is_having or not isinstance(current[group_chat_record[0]], i.LeaderConfirmation):
                    command = COMMANDS[i.LeaderConfirmation.COMMAND]
                    if attempt_interaction(command, record, chat, is_private, message, group_chat_record):
                        i.BOT.send_message(record.id, t.CONFIRMATION_POLL_SENT[record.language])

                else:  # if the group chat is having an interaction and the interaction is leader confirmation
                    interaction = current[group_chat_record[0]]

                    if not interaction.is_candidate(record.id):  # if the candidate's groupmate
                        i.cl.info(lt.CLAIMS_LATE.format(record.id, interaction.CANDIDATE_ID))
                        interaction.add_claimer(record.id, record.language)
                        text = t.ALREADY_CLAIMED[record.language].format(interaction.CANDIDATE_USERNAME)
                        message.reply_text(text, quote=not is_private)
                    else:  # if the user is the candidate
                        interaction.respond(COMMANDS[i.LeaderConfirmation.COMMAND])

            else:  # if there is not enough registered students from the group
                difference = c.MIN_GROUPMATES_FOR_LEADER_CONFORMATION - num_groupmates
                text = t.NOT_ENOUGH_FOR_LEADER_CONFIRMATION[record.language].format(num_groupmates, difference)
                message.reply_text(text, quote=not is_private)
                i.cl.info(lt.CLAIM_WITH_NOT_ENOUGH.format(record.id, num_groupmates))

        else:  # if the group has not registered a group chat
            message.reply_text(t.GROUP_CHAT_NEEDED[record.language], quote=not is_private)
            i.cl.info(lt.CLAIM_WITHOUT_GROUP_CHAT.format(record.id))

    else:  # if there is already a leader in the group
        message.reply_text(t.ALREADY_LEADER_IN_GROUP[record.language], quote=not is_private)
        i.cl.info(lt.CLAIM_WITH_LEADER.format(record.id, leader[0]))

    cursor.close()
    connection.close()


def adding_admin(record: c.ChatRecord, update: Update):
    """
    This function is called when a leader uses the command /trust. It is responsible for deciding whether
    src.interactions.AddingAdmin interaction makes sense to be started, which is the case if adding an will not exceed
    the maximum ratio of admins to all students in the group, defined as src.config.MAX_ADMINS_STUDENTS_RATIO. If it
    will not, an attempt to start the interaction is made by calling src.managers.attempt_interaction. Otherwise, the
    bot sends a message explaining why the interaction cannot be started, which is a reply in non-private chats.

    Args: see src.managers.leaving.__doc__.
    """
    chat, message = update.effective_chat, update.effective_message
    is_private = chat.type == Chat.PRIVATE

    connection = connect(c.DATABASE)
    cursor = connection.cursor()

    cursor.execute(  # records of admins from the leader's group
        'SELECT COUNT(id) FROM chats WHERE group_id = ? AND role = 1',
        (record.group_id,)
    )
    num_admins = cursor.fetchone()[0]

    cursor.execute(  # records of students from the leader's group
        'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
        (record.group_id,)
    )
    num_students = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    if (num_admins + 1) / num_students <= c.MAX_ADMINS_STUDENTS_RATIO:  # if adding an admin will not exceed the limit
        attempt_interaction(COMMANDS[i.AddingAdmin.COMMAND], record, chat, is_private, message)
    else:  # if adding 1 more admin will exceed the limit
        message.reply_text(t.ADMIN_LIMIT_REACHED[record.language], quote=not is_private)
        i.cl.info(lt.TRUST_OVER_LIMIT.format(record.id, num_admins, num_students))


def removing_admin(record: c.ChatRecord, update: Update):
    """
    This function is called when a leader uses the command /distrust. It is responsible for deciding whether
    src.interactions.RemovingAdmin interaction makes sense to be started, which is the case if there are admins in the
    group. If there are, an attempt to start the interaction is made by calling src.managers.attempt_interaction.
    Otherwise, the bot sends a message explaining why the interaction cannot be started, which is a reply in non-private
    chats.

    Args: see src.managers.leaving.__doc__.
    """
    chat, message = update.effective_chat, update.effective_message
    is_private = chat.type == Chat.PRIVATE

    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(  # records of admins from the leader's group
        'SELECT COUNT(id) FROM chats WHERE group_id = ? AND role = 1',
        (record.group_id,)
    )
    num_admins = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    if num_admins:  # if there are admins in the group
        attempt_interaction(COMMANDS[i.RemovingAdmin.COMMAND], record, chat, is_private, message)
    else:  # if there are no admins in the group
        message.reply_text(t.ALREADY_NO_ADMINS[record.language], quote=not is_private)
        i.cl.info(lt.DISTRUST_WITHOUT_ADMINS.format(record.id))


def connecting_ecampus(record: c.ChatRecord, update: Update):
    pass


def adding_event(record: c.ChatRecord, update: Update):
    """
    This function is called when an admin uses the command /new. It is responsible for making an attempt to start
    src.interactions.AddingEvent interaction by calling src.managers.attempt_interaction.

    Args: see src.managers.leaving.__doc__.
    """
    chat = update.effective_chat
    is_private = chat.type == Chat.PRIVATE

    attempt_interaction(COMMANDS[i.AddingEvent.COMMAND], record, chat, is_private, update.effective_message)


def canceling_event(record: c.ChatRecord, update: Update):
    pass


def saving_info(record: c.ChatRecord, update: Update):
    """
    This function is called when an admin uses the command /save. It is responsible for making an attempt to start
    src.interactions.SavingInfo interaction by calling src.managers.attempt_interaction.

    Args: see src.managers.leaving.__doc__.
    """
    chat = update.effective_chat
    is_private = chat.type == Chat.PRIVATE

    attempt_interaction(COMMANDS[i.SavingInfo.COMMAND], record, chat, is_private, update.effective_message)


def deleting_info(record: c.ChatRecord, update: Update):
    """
    This function is called when an admin uses the command /delete or /clear. It is responsible for deciding whether
    src.interactions.DeletingInfo and src.interactions.ClearingInfo interactions make sense to be started, which is the
    case if the group's saved information is not empty. If it is not, an attempt to start the appropriate interaction
    (see src.managers.COMMANDS) is made by calling src.managers.attempt_interaction. Otherwise, the bot sends a message
    explaining why the interaction cannot be started, which is a reply in non-private chats.

    Args: see src.managers.leaving.__doc__.
    """
    chat, message = update.effective_chat, update.effective_message
    is_private, command = chat.type == Chat.PRIVATE, message.text[1:].removesuffix(USERNAME).lower()

    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(
        'SELECT info FROM groups WHERE id = ?',
        (record.group_id,)
    )
    info = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    if info:
        attempt_interaction(COMMANDS[command], record, chat, is_private, message)
    else:
        message.reply_text(t.ALREADY_NO_INFO[record.language], quote=not is_private)
        i.cl.info(lt.DELETE_WITHOUT_INFO.format(record.id, command, record.group_id))


def notifying_group(record: c.ChatRecord, update: Update):
    pass


def asking_group(record: c.ChatRecord, update: Update):
    pass  # kim: refuse to answer


def changing_leader(record: c.ChatRecord, update: Update):
    """
    This function is called when a leader uses the command /resign. It is responsible for deciding whether
    src.interactions.ChangingLeader interaction makes sense to be started, which is the case if the leader is not the
    only registered one from the group. If they are not, an attempt to start the interaction is made by calling
    src.managers.attempt_interaction. Otherwise, the bot sends a message explaining why the interaction cannot be
    started, which is a reply in non-private chats.

    Args: see src.managers.leaving.__doc__.
    """
    chat, message, command = update.effective_chat, update.effective_message, COMMANDS[i.ChangingLeader.COMMAND]
    is_private = chat.type == Chat.PRIVATE

    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(  # records of admins from the leader's group
        'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
        (record.group_id,)
    )
    num_groupmates = cursor.fetchone()[0] - 1  # w/o the leader
    cursor.close()
    connection.close()

    if num_groupmates:  # if the leader is not the only one registered from the group
        attempt_interaction(COMMANDS[i.ChangingLeader.COMMAND], record, chat, is_private, message)
    else:  # if the leader is the only one registered from the group
        message.reply_text(t.NO_GROUPMATES_FOR_RESIGN[record.language], quote=not is_private)
        i.cl.info(lt.RESIGN_ALONE.format(record.id))


def displaying_description(record: c.ChatRecord, update: Update):
    """
    This function is called when a registered user uses the command /help, which is supposed to be followed by a
    different command. It makes the bot display description for the latter command. If the command /help is used alone,
    description for it is displayed. The message is a reply in non-private chats.

    Args: see src.managers.leaving.__doc__.
    """
    message = update.effective_message
    text = message.text

    if text != '/help':
        description_for = text[text.find('/help') + 6:]
        try:
            text = COMMANDS[description_for].description[record.language]
        except KeyError:
            text = t.INVALID_DESCRIPTION_REQUEST[record.language]
        else:
            if record.role < COMMANDS[description_for].role:
                text += t.REMEMBER_UNAVAILABLE[record.language]
    else:
        text = t.DISPLAYING_DESCRIPTION_DESCRIPTION[record.language]
        description_for = 'help'

    message.reply_text(text, quote=update.effective_chat.type != Chat.PRIVATE)
    i.cl.info(lt.DESCRIPTION.format(record.id, description_for))


def sending_feedback(record: c.ChatRecord, update: Update):
    pass


def leaving(record: c.ChatRecord, update: Update):
    """
    This function is called when a registered user uses the command /leave. It is responsible for determining whether
    src.interactions.Leaving interaction makes sense to be started, which is the case if the chat is private. If it is,
    an attempt to start the interaction is made by calling src.managers.attempt_interaction. In non-private chats the
    bot replies with a message explaining how this command works in such chats.

    Args:
        record (src.config.ChatRecord): record of the user who is using the command.
        update (telegram.Update): update received after the command is used.
    """
    chat = update.effective_chat

    if chat.type == Chat.PRIVATE:
        attempt_interaction(COMMANDS[i.Leaving.COMMAND], record, chat, True, update.effective_message)
    else:
        chat.send_message(t.LEAVING_IN_GROUPS[record.language], reply_to_message_id=update.effective_message.message_id)
        i.cl.info(lt.LEAVE_NOT_PRIVATELY.format(record.id, chat.id))


COMMANDS: dict[str, c.Command] = {
    'start': c.Command(registration, c.ORDINARY_ROLE, i.Registration, t.REGISTRATION_DESCRIPTION),
    'claim': c.Command(leader_confirmation, c.ORDINARY_ROLE, i.LeaderConfirmation, t.LEADER_CONFIRMATION_DESCRIPTION),
    'commands': c.Command(i.displaying_commands, c.ORDINARY_ROLE, None, t.DISPLAYING_COMMANDS_DESCRIPTION),
    'trust': c.Command(adding_admin, c.LEADER_ROLE, i.AddingAdmin, t.ADDING_ADMIN_DESCRIPTION),
    'distrust': c.Command(removing_admin, c.LEADER_ROLE, i.RemovingAdmin, t.REMOVING_ADMIN_DESCRIPTION),
    'events': c.Command(i.displaying_events, c.ORDINARY_ROLE, None, t.DISPLAYING_EVENTS_DESCRIPTION),
    'info': c.Command(i.displaying_info, c.ORDINARY_ROLE, None, t.DISPLAYING_INFO_DESCRIPTION),
    # 'campus': c.Command(connecting_ecampus, c.ORDINARY_ROLE, i.ConnectingECampus, t.CONNECTING_ECAMPUS_DESCRIPTION),
    'new': c.Command(adding_event, c.ADMIN_ROLE, i.AddingEvent, t.ADDING_EVENT_DESCRIPTION),
    # 'cancel': c.Command(canceling_event, c.ADMIN_ROLE, i.CancelingEvent, t.CANCELING_EVENT_DESCRIPTION),
    'save': c.Command(saving_info, c.ADMIN_ROLE, i.SavingInfo, t.SAVING_INFO_DESCRIPTION),
    'delete': c.Command(deleting_info, c.ADMIN_ROLE, i.DeletingInfo, t.DELETING_INFO_DESCRIPTION),
    'clear': c.Command(deleting_info, c.ADMIN_ROLE, i.ClearingInfo, t.CLEARING_INFO_DESCRIPTION),
    # 'tell': c.Command(notifying_group, c.LEADER_ROLE, i.NotifyingGroup, t.NOTIFYING_GROUPMATES_DESCRIPTION),
    # 'ask': c.Command(asking_group, c.LEADER_ROLE, i.AskingGroup, t.ASKING_GROUPMATES_DESCRIPTION),
    'resign': c.Command(changing_leader, c.LEADER_ROLE, i.ChangingLeader, t.CHANGING_LEADER_DESCRIPTION),
    'help': c.Command(displaying_description, c.ORDINARY_ROLE, None, t.CONTROVERSIAL_DESCRIPTION_REQUEST),
    # 'feedback': c.Command(sending_feedback, c.ORDINARY_ROLE, i.SendingFeedback, t.SENDING_FEEDBACK_DESCRIPTION),
    'leave': c.Command(leaving, c.ORDINARY_ROLE, i.Leaving, t.LEAVING_DESCRIPTION),
}


def attempt_interaction(command: c.Command, record: c.ChatRecord, chat: Chat, is_private: bool, message: Message,
                        *args) -> bool:
    """
    This function is called when an interaction makes sense to be started. It is responsible for deciding whether it
    will, which is the case if the command is available for the user's role and the chat is not already having an
    interaction. Also, if the command starts a private interaction and is used in a non-private chat, the bot replies to
    the message informing that the interaction will be started privately and sends a private message to do it. However,
    if the interaction will not be started, the bot sends a message explaining why, which is a reply in non-private
    chats.

    Args:
        command (src.config.Command): namedtuple that represents the received command.
        record (src.config.ChatRecord): record of the user who is using the command.
        chat (telegram.Chat): chat the the command is being used in.
        is_private (bool): whether that chat is private.
        message (telegram.Message): message that the command is sent in.
        args: arguments that will be passed to the interaction besides the record, if it will be started.

    Returns (bool): whether the interaction has been started.
    """
    if record.role >= command.role:

        if record.id not in i.current:  # if the chat is not already having an interaction
            # if the interaction is private but the chat is not
            if command.interaction.IS_PRIVATE and not is_private:
                chat.send_message(t.PRIVATE_INTERACTION[record.language], reply_to_message_id=message.message_id)
                i.cl.info(lt.STARTS_NOT_PRIVATELY.format(record.id, command.interaction.__name__))

            command.interaction(record, *args)
            return True

        else:  # if the chat is already having an interaction
            i.current[record.id].respond(command.interaction.COMMAND, message)

    else:  # if the command is an admin one and the user is not an admin
        text = command.interaction.UNAVAILABLE_MESSAGE[record.language]
        chat.send_message(text, reply_to_message_id=None if is_private else message.message_id)
        i.cl.info(lt.UNAVAILABLE_COMMAND.format(record.id, command.interaction.COMMAND, record.role))

    return False

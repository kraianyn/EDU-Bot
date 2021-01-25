from datetime import datetime, timedelta
from typing import Union
from collections import namedtuple
from sqlite3 import connect

from telegram import Update, Chat, Message

import src.interactions as i
import src.auxiliary as a
from src.bot_info import USERNAME
import src.config as c
import src.log_text as lt
import src.text as t


def registration(chat: Chat, is_private: bool, message: Message):
    """
    This function is responsible for deciding whether src.interactions.Registration interaction will be started, which
    is the case if the chat is not already registered and is not already registering. Otherwise, the bot sends a
    message, a reply in non-private chats, explaining why the interaction cannot be started.

    Args:
        chat (telegram.Chat): chat that the command is sent in.
        is_private (bool): whether the chat is private.
        message (telegram.Message): message that the command is sent in.
    """
    if not (record := a.get_chat_record(chat.id)):  # if the chat is not already registered
        if chat.id not in i.current:  # if the chat is not already registering
            i.Registration(chat.id, chat.type)
        else:  # if the chat is already registering
            i.current[chat.id].respond(i.Registration.COMMAND, message)
    else:  # if the chat is already registered
        message.reply_text(t.ALREADY_REGISTERED[is_private][record.language], quote=not is_private)
        i.cl.info(lt.START_BEING_REGISTERED.format(chat.id))


def leader_confirmation(record: a.ChatRecord, update: Update):
    """
    This function is responsible for deciding whether src.interactions.LeaderConfirmation interaction makes sense to be
    started. If it does, an attempt to start the interaction is made by calling src.managers.attempt_interaction.
    Otherwise, the bot sends a message, a reply in non-private chats, explaining why the interaction cannot be started.

    Args: see src.managers.deleting_data.__doc__.
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
                if not is_having or not isinstance(i.current[group_chat_record[0]], i.LeaderConfirmation):
                    command = COMMANDS[i.LeaderConfirmation.COMMAND]
                    attempt_interaction(command, record, chat, is_private, message, group_chat_record)

                else:  # if the group chat is having an interaction and the interaction is leader confirmation
                    interaction: i.LeaderConfirmation = i.current[group_chat_record[0]]

                    if not interaction.is_candidate(record.id):  # if the candidate's groupmate
                        i.cl.info(lt.CLAIMS_LATE.format(record.id, interaction.candidate_id))
                        interaction.add_claimer(record.id, record.language)
                        text = t.ALREADY_CLAIMED[record.language].format(interaction.candidate_username)
                        message.reply_text(text, quote=not is_private)
                    else:  # if the user is the candidate
                        interaction.respond(i.LeaderConfirmation.COMMAND, message)

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
        i.cl.info(lt.CLAIM_WITH_LEADER.format(record.id))

    cursor.close()
    connection.close()


def adding_admin(record: a.ChatRecord, update: Update):
    """
    This function is responsible for deciding whether src.interactions.AddingAdmin interaction makes sense to be
    started, which is the case if adding an will not exceed the maximum ratio of admins to all students in the group,
    defined as src.config.MAX_ADMINS_STUDENTS_RATIO. If it will not, an attempt to start the interaction is made by
    calling src.managers.attempt_interaction. Otherwise, the bot sends a message, a reply in non-private chats,
    explaining why the interaction cannot be started.

    Args: see src.managers.deleting_data.__doc__.
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
    elif num_students > 1:  # if adding 1 more admin will exceed the limit
        message.reply_text(t.ADMIN_LIMIT_REACHED[record.language], quote=not is_private)
        i.cl.info(lt.TRUST_OVER_LIMIT.format(record.id, num_admins, num_students))
    else:  # if the leader is the only registered student from the group
        message.reply_text(t.NO_GROUPMATES_TO_TRUST[record.language], quote=not is_private)
        i.cl.info(lt.TRUST_ALONE.format(record.id, record.group_id))


def removing_admin(record: a.ChatRecord, update: Update):
    """
    This function is responsible for deciding whether src.interactions.RemovingAdmin interaction makes sense to be
    started, which is the case if there are admins in the group. If there are, an attempt to start the interaction is
    made by calling src.managers.attempt_interaction. Otherwise, the bot sends a message, a reply in non-private chats,
    explaining why the interaction cannot be started..

    Args: see src.managers.deleting_data.__doc__.
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
        i.cl.info(lt.DISTRUST_WITHOUT_ADMINS.format(record.id, record.group_id))


def connecting_ecampus(record: a.ChatRecord, update: Update):
    pass


def adding_event(record: a.ChatRecord, update: Update):
    """
    This function is responsible for making an attempt to start src.interactions.AddingEvent interaction by calling
    src.managers.attempt_interaction.

    Args: see src.managers.deleting_data.__doc__.
    """
    chat = update.effective_chat
    is_private = chat.type == Chat.PRIVATE

    attempt_interaction(COMMANDS[i.AddingEvent.COMMAND], record, chat, is_private, update.effective_message)


def canceling_event(record: a.ChatRecord, update: Update):
    """
    This function is responsible for deciding whether src.interactions.CancelingEvent makes sense to be started, which
    is the case if the group has upcoming events. If it does, an attempt to start the interaction is made by calling
    src.managers.attempt_interaction. Otherwise, the bot sends a message, a reply in non-private chats, explaining why
    the interaction cannot be started.

    Args: see src.managers.deleting_data.__doc__.
    """
    chat, message = update.effective_chat, update.effective_message
    is_private = chat.type = Chat.PRIVATE

    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(
        'SELECT events FROM groups WHERE id = ?',
        (record.group_id,)
    )
    events = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    if events:
        attempt_interaction(COMMANDS[i.CancelingEvent.COMMAND], record, chat, is_private, message, events)
    else:
        message.reply_text(t.ALREADY_NO_EVENTS[record.language], quote=not is_private)
        i.cl.info(lt.CANCEL_WITHOUT_EVENTS.format(record.id))


def saving_info(record: a.ChatRecord, update: Update):
    """
    This function is responsible for making an attempt to start src.interactions.SavingInfo interaction by calling
    src.managers.attempt_interaction.

    Args: see src.managers.deleting_data.__doc__.
    """
    chat = update.effective_chat
    is_private = chat.type == Chat.PRIVATE

    attempt_interaction(COMMANDS[i.SavingInfo.COMMAND], record, chat, is_private, update.effective_message)


def deleting_info(record: a.ChatRecord, update: Update):
    """
    This function is responsible for deciding whether src.interactions.DeletingInfo and src.interactions.ClearingInfo
    interactions make sense to be started, which is the case if the group's saved information is not empty. If it is
    not, an attempt to start the appropriate interaction (see src.managers.COMMANDS) is made by calling
    src.managers.attempt_interaction. Otherwise, the bot sends a message, a reply in non-private chats, explaining why
    the interaction cannot be started.

    Args: see src.managers.deleting_data.__doc__.
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
        args = [COMMANDS[command], record, chat, is_private, message]
        if command == i.DeletingInfo.COMMAND:
            args.append(info)

        attempt_interaction(*args)

    else:
        message.reply_text(t.ALREADY_NO_INFO[record.language], quote=not is_private)
        i.cl.info(lt.DELETE_WITHOUT_INFO.format(record.id, command))


def leader_involving_group(record: a.ChatRecord, update: Update):
    """
    This function is responsible for deciding whether src.interactions.ChangingLeader, src.interactions.NotifyingGroup,
    and src.interactions.AskingGroup interactions make sense to be started, which is the case if the leader is not the
    only registered student from the group. If they are not, an attempt to start the appropriate interaction is made by
    calling src.managers.attempt_interaction. Otherwise, the bot sends a message, a reply in non-private chats,
    explaining why the interaction cannot be started.

    Args: see src.managers.deleting_data.__doc__.
    """
    chat, message = update.effective_chat, update.effective_message
    is_private, command = chat.type == Chat.PRIVATE, message.text[1:].removesuffix(USERNAME).lower()
    is_communicative = command != i.ChangingLeader.COMMAND  # whether the command is /tell or /ask

    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(  # records of admins from the leader's group
        'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
        (record.group_id,)
    )
    num_groupmates = cursor.fetchone()[0] - 1  # w/o the leader
    cursor.close()
    connection.close()

    if num_groupmates:  # if the leader is not the only registered one from the group

        if command == i.AskingGroup.COMMAND and record.group_id in i.current:
            message.reply_text(t.ONGOING_GROUP_ANSWERING[record.language], quote=not is_private)
            return

        attempt_interaction(COMMANDS[command], record, chat, is_private, message)

    else:  # if the leader is the only registered one from the group
        i.cl.info(lt.INVOLVING_GROUP_ALONE.format(record.id, command))

        if is_communicative:  # if the command is /tell or /ask
            msg = t.NO_GROUPMATES_TO_NOTIFY if command == i.NotifyingGroup.COMMAND else t.NO_GROUPMATES_TO_ASK
        else:  # if the command is /resign
            msg = t.NO_GROUPMATES_FOR_RESIGN
        message.reply_text(msg[record.language], quote=not is_private)


def sending_feedback(record: a.ChatRecord, update: Update):
    chat, message = update.effective_chat, update.effective_message
    is_private = chat.type == Chat.PRIVATE

    registered = record.registered
    year, month, day, hour = int(registered[:4]), int(registered[5:7]), int(registered[8:10]), int(registered[11:13])

    if datetime.now() - datetime(year, month, day, hour) >= timedelta(weeks=1):
        attempt_interaction(COMMANDS[i.SendingFeedback.COMMAND], record, chat, is_private, message)
    else:
        message.reply_text(t.FEEDBACK_CONDITION[record.language], quote=not is_private)


def deleting_data(record: a.ChatRecord, update: Update):
    """
    This function is responsible for determining whether src.interactions.DeletingData interaction makes sense to be
    started, which is the case if the chat is private. If it is, an attempt to start the interaction is made by calling
    src.managers.attempt_interaction. In non-private chats, the bot replies with a message explaining how this command
    works in such chats.

    Args:
        record (src.auxiliary.ChatRecord): record of the user who is using the command.
        update (telegram.Update): update received after the command is used.
    """
    chat = update.effective_chat

    if chat.type == Chat.PRIVATE:
        attempt_interaction(COMMANDS[i.DeletingData.COMMAND], record, chat, True, update.effective_message)
    else:
        chat.send_message(t.LEAVING_IN_GROUPS[record.language], reply_to_message_id=update.effective_message.message_id)
        i.cl.info(lt.LEAVE_NOT_PRIVATELY.format(record.id, chat.id))


Command = namedtuple('Command', ('manager', 'role', 'interaction'))
COMMANDS: dict[str, Command] = {
    'start': Command(registration, c.ORDINARY_ROLE, i.Registration),
    'claim': Command(leader_confirmation, c.ORDINARY_ROLE, i.LeaderConfirmation),
    'commands': Command(i.displaying_commands, c.ORDINARY_ROLE, None),
    'trust': Command(adding_admin, c.LEADER_ROLE, i.AddingAdmin),
    'distrust': Command(removing_admin, c.LEADER_ROLE, i.RemovingAdmin),
    'events': Command(i.displaying_events, c.ORDINARY_ROLE, None),
    'info': Command(i.displaying_info, c.ORDINARY_ROLE, None),
    # 'ecampus': Command(connecting_ecampus, c.ORDINARY_ROLE, i.ConnectingECampus),
    'new': Command(adding_event, c.ADMIN_ROLE, i.AddingEvent),
    'cancel': Command(canceling_event, c.ADMIN_ROLE, i.CancelingEvent),
    'save': Command(saving_info, c.ADMIN_ROLE, i.SavingInfo),
    'delete': Command(deleting_info, c.ADMIN_ROLE, i.DeletingInfo),
    'clear': Command(deleting_info, c.ADMIN_ROLE, i.ClearingInfo),
    'tell': Command(leader_involving_group, c.LEADER_ROLE, i.NotifyingGroup),
    'ask': Command(leader_involving_group, c.LEADER_ROLE, i.AskingGroup),
    'resign': Command(leader_involving_group, c.LEADER_ROLE, i.ChangingLeader),
    'feedback': Command(sending_feedback, c.ORDINARY_ROLE, i.SendingFeedback),
    'leave': Command(deleting_data, c.ORDINARY_ROLE, i.DeletingData),
}


def attempt_interaction(command: Command, record: a.ChatRecord, chat: Chat, is_private: bool, message: Message,
                        *args):
    """
    This function is called when an interaction makes sense to be started. It is responsible for deciding whether it
    will, which is the case if the command is available for the user's role and the chat is not already having an
    interaction. Also, if the command starts a private interaction and is used in a non-private chat, the bot replies to
    the message informing that the interaction will be started privately and sends a private message to do it. However,
    if the interaction will not be started, the bot sends a message explaining why, which is a reply in non-private
    chats.

    Args:
        command (src.managers.Command): namedtuple that represents the received command.
        record (src.auxiliary.ChatRecord): record of the user who is using the command.
        chat (telegram.Chat): chat the the command is being used in.
        is_private (bool): whether that chat is private.
        message (telegram.Message): message that the command is sent in.
        args: arguments that will be passed to the interaction besides the record, if it will be started.
    """
    if record.role >= command.role:

        if record.id not in i.current:  # if the chat is not already having an interaction
            # if the interaction is private but the chat is not
            if command.interaction.IS_PRIVATE and not is_private:
                chat.send_message(t.PRIVATE_INTERACTION[record.language], reply_to_message_id=message.message_id)
                i.cl.info(lt.STARTS_NOT_PRIVATELY.format(record.id, command.interaction.__name__))

            command.interaction(record, *args)

        else:  # if the chat is already having an interaction
            i.current[record.id].respond(command.interaction.COMMAND, message)

    else:  # if the command is an admin one and the user is not an admin
        text = command.interaction.UNAVAILABLE_MESSAGE[record.language]
        chat.send_message(text, reply_to_message_id=None if is_private else message.message_id)
        i.cl.info(lt.UNAVAILABLE_COMMAND.format(record.id, command.interaction.COMMAND, record.role))

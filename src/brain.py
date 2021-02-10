from time import sleep
from datetime import datetime, timedelta

from telegram import Update, Chat

import src.interactions as i
from src.managers import COMMANDS
import src.notification as n
import src.auxiliary as a
from src.text import REGISTRATION_NEEDED
from src.bot_info import USERNAME
from src.config import LEADER_ROLE, NOTIFICATION_TIME
from src.loggers import cl, UNAVAILABLE_COMMAND


# -------------------------------------------------------------------------------------------------------- communication

def command_handler(update: Update, _):
    """
    This function is the callback for the CommandHandler of src.launch.DISPATCHER. It is called when the bot receives a
    command and is responsible for starting an interaction (instantiating src.interactions.Interaction). It also makes
    the bot properly respond (or not respond) if the command is used inappropriately.

    Args:
        update (telegram.Update): update received after a command is received.
        _ (telegram.CallbackContext): context object passed by the CommandHandler. Not used.
    """
    chat = update.effective_chat

    if chat.type == Chat.CHANNEL:  # if the chat is a channel
        return  # no response

    message = update.effective_message
    command_str = message.text[1:].removesuffix(USERNAME).lower()  # without '/' and possible bot mention
    is_private = chat.type == Chat.PRIVATE

    if command_str != i.Registration.COMMAND:  # if the command does not start the registration

        if record := a.get_chat_record(update.effective_user.id):  # if the user is registered
            try:
                command = COMMANDS[command_str]
            except KeyError:  # if the message contains text other than the command
                return  # no response since the command is used inappropriately

            # if the command is not a leader one or the user is a leader
            if command.role != LEADER_ROLE or record.role == LEADER_ROLE:
                command.manager(record, update)
            else:  # if the command is a leader one and the user is not a leader
                text = command.interaction.UNAVAILABLE_MESSAGE[record.language]
                message.reply_text(text, quote=not is_private)
                cl.info(UNAVAILABLE_COMMAND.format(record.id, command_str, record.role))

        # if the user is not registered but the group chat is
        elif group_chat_record := a.get_chat_record(update.effective_chat.id):
            message.reply_text(REGISTRATION_NEEDED[group_chat_record.language], quote=not is_private)

    else:  # if the command starts the registration
        COMMANDS[i.Registration.COMMAND].manager(chat, is_private, message)


def callback_query_handler(update: Update, _):
    """
    This function is the callback for the CallbackQueryHandler of src.launch.DISPATCHER. It is called when an inline
    button sent by the bot is clicked. It considers the chosen option and may make the bot take next action of the
    interaction.

    Args:
        update (telegram.Update): update received after an inline button is clicked.
        _ (telegram.CallbackContext): context object passed by the CallbackQueryHandler. Not used.
    """
    chat_id = update.effective_chat.id
    try:
        i.current[chat_id].next_action(update)
    except KeyError:
        try:
            i.current[a.get_chat_record(chat_id).group_id].next_action(update)
        except KeyError:
            pass


def text_handler(update: Update, _):
    """
    This function is the callback for the MessageHandler of src.launch.DISPATCHER. It is called when the bot receives a
    text message. It considers the message and may make the bot take the next action of the interaction.

    Args:
        update (telegram.Update): update received after the text message is received.
        _ (telegram.CallbackContext): context object passed by the MessageHandler. Not used.
    """
    if (chat_id := update.effective_chat.id) in i.current:
        i.current[chat_id].next_action(update)


def poll_answer_handler(update: Update, _):
    """
    This function is the callback for the PollAnswerHandler of src.launch.DISPATCHER. It is called when a poll answer is
    given. It considers the answer and may make the bot take next action of the interaction.

    Args:
        update (telegram.Update): update received after a poll answer is given.
        _ (telegram.CallbackContext): context object passed by the PollAnswerHandler. Not used.
    """
    if record := a.get_chat_record(update.effective_user.id):  # if the user is registered
        i.current[record.group_id].next_action(update)


# --------------------------------------------------------------------------------------------------------- notification

def notification():
    while True:
        n.remind_about_events()

        now = datetime.now()
        notification_time_tomorrow = datetime(now.year, now.month, now.day, *NOTIFICATION_TIME) + timedelta(days=1)
        sleep((notification_time_tomorrow - now).total_seconds())

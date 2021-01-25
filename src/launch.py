__author__ = 'Victor Serhiyovych Buhaiov'

from threading import Thread
import logging

from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, PollAnswerHandler

import src.interactions as i
import src.brain as b
import src.managers as m
import src.loggers as l

logging.basicConfig(filename=l.BOT_LOG, filemode='w', format=l.BOT_LOG_FORMAT, datefmt=l.TIME_FORMAT,
                    level=logging.INFO)

# ------------------------------------------------------------------------------------------------------------ handlers

DISPATCHER = i.UPDATER.dispatcher

DISPATCHER.add_handler(CommandHandler(tuple(m.COMMANDS.keys()), b.command_handler))
DISPATCHER.add_handler(CallbackQueryHandler(b.callback_query_handler))
DISPATCHER.add_handler(MessageHandler(Filters.text, b.text_handler))
DISPATCHER.add_handler(PollAnswerHandler(b.poll_answer_handler))

# ------------------------------------------------------------------------------ communication and notification threads

communication_thread = Thread(target=i.UPDATER.start_polling)

communication_thread.start()
logging.info(l.CT_STARTS)

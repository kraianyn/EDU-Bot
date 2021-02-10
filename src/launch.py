__author__ = 'Victor Serhiyovych Buhaiov'

from datetime import datetime
from threading import Thread
from sqlite3 import connect
import logging

from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, PollAnswerHandler

import src.interactions as i
import src.brain as b
import src.managers as m
from src.config import THRESHOLD_DATE, DATABASE
import src.loggers as l

logging.basicConfig(filename=l.BOT_LOG, filemode='w', format=l.BOT_LOG_FORMAT, datefmt=l.TIME_FORMAT,
                    level=logging.INFO)

# ------------------------------------------------------------------------------------------------ cleaning the database

now = datetime.now()
if now.month >= THRESHOLD_DATE[0] and now.day >= THRESHOLD_DATE[1]:
    graduation_year = now.year - 2000

    connection = connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(  # ids of graduated groups and number of chats related to each one of them
        'SELECT group_id, COUNT(id) FROM chats '
        'WHERE group_id IN (SELECT id FROM groups WHERE graduation = ?)'
        'GROUP BY group_id',
        (graduation_year,)
    )
    graduated_groups: list[tuple[int, int]] = cursor.fetchall()
    for group_id, num_chats in graduated_groups:
        logging.info(l.GRADUATES.format(group_id, num_chats))

    cursor.execute(  # deleting records of chats that are related to graduated groups
        'DELETE FROM chats '
        'WHERE group_id IN (SELECT id FROM groups WHERE graduation = ?)',
        (graduation_year,)
    )
    cursor.execute(  # deleting records of graduated groups
        'DELETE FROM groups WHERE graduation = ?',
        (graduation_year,)
    )

    connection.commit()
    cursor.close()
    connection.close()

# ------------------------------------------------------------------------------------------------------------- handlers

dispatcher = i.updater.dispatcher

dispatcher.add_handler(CommandHandler(tuple(m.COMMANDS.keys()), b.command_handler))
dispatcher.add_handler(CallbackQueryHandler(b.callback_query_handler))
dispatcher.add_handler(MessageHandler(Filters.text, b.text_handler))
dispatcher.add_handler(PollAnswerHandler(b.poll_answer_handler))

# ------------------------------------------------------------------------------- communication and notification threads

communication_thread = Thread(target=i.updater.start_polling)
notification_thread = Thread(target=b.notification)

communication_thread.start()
logging.info(l.CT_STARTS)
notification_thread.start()
logging.info(l.NT_STARTS)

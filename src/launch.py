from datetime import datetime
from threading import Thread
import logging
from src.config import BOT_LOG, BOT_LOG_FORMAT, TIME_FORMAT
from src.interactions import UPDATER
import src.brain as b
from src.log_text import CT_STARTS, NT_STARTS
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, PollAnswerHandler

logging.basicConfig(filename=BOT_LOG, filemode='w', format=BOT_LOG_FORMAT, datefmt=TIME_FORMAT,
                    level=logging.INFO)

# ------------------------------------------------------------------------------------------------------------ handlers

DISPATCHER = UPDATER.dispatcher

DISPATCHER.add_handler(CommandHandler(tuple(b.COMMANDS.keys()), b.command_handler))
DISPATCHER.add_handler(CallbackQueryHandler(b.callback_query_handler))
DISPATCHER.add_handler(MessageHandler(Filters.text, b.text_handler))
DISPATCHER.add_handler(PollAnswerHandler(b.poll_answer_handler))

# ------------------------------------------------------------------------------ communication and notification threads

communication_thread = Thread(target=UPDATER.start_polling)
# notification_thread = Thread(target=b.notification)

communication_thread.start()
logging.info(CT_STARTS)

# ----------------------------------------- delaying the notification thread so that notification loops run at xx:xx:00

launch_time = datetime.today()
# sleep(60 - (launch_time.second + launch_time.microsecond / 1000000))
# notification_thread.start()
# logging.info(NT_STARTS)

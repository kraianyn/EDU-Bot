from datetime import datetime
from typing import Callable, Union
from random import choice
from re import findall
import logging
from sqlite3 import connect
import src.config as c
from src.bot_info import TOKEN
import src.log_text as lt
import src.text as t
import src.auxiliary as a
from telegram.ext import Updater
from telegram import Update, Chat, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.error import BadRequest

cl = logging.getLogger('communication')  # communication logger
file_handler = logging.FileHandler(c.COMMUNICATION_LOG, 'w', 'utf8')
file_handler.setFormatter(logging.Formatter(c.LOG_FORMAT, c.TIME_FORMAT))
cl.addHandler(file_handler)
cl.setLevel(logging.DEBUG)

UPDATER = Updater(TOKEN)
BOT = UPDATER.bot


class Interaction:
    """
    This class represents an interaction between the bot and a student/group. It is never instantiated and is extended
    by subclasses to represent different types of interaction.

    Attributes:
        COMMAND (str): command that starts the interaction.
        IS_PRIVATE (bool): whether this interaction can only be in a private chat.
        ONGOING_MESSAGE (tuple[str]): message in case of an attempt to start a different interaction.
        ALREADY_MESSAGE (tuple[str]): message in case of using self.COMMAND during the interaction.
        chat_id (int): id of the chat that the interaction is in.
        language (int): index of the language of the interaction, according to the indexation in src.text.LANGUAGES.
        next_action (Callable[[Update], None]): method that will make the bot take the next step of the interaction.
    """
    COMMAND: str
    IS_PRIVATE: bool
    ONGOING_MESSAGE: tuple[str]
    ALREADY_MESSAGE: tuple[str]

    chat_id: int
    language: int
    next_action: Callable[[Update], None]

    def __init__(self, declare: Union[c.ChatRecord, None]):
        """
        This method is called when an interaction is started. It initializes the instance's chat_id and language
        attributes and adds the interaction to src.interactions.current.
        """
        if declare:
            self.chat_id = declare.id
            self.language = declare.language
            self.group_id = declare.group_id

            self.is_familiar = bool(int(getattr(declare.familiarity, self.COMMAND)))
            self.familiarity = None if self.is_familiar else declare.familiarity

        current[self.chat_id] = self
        cl.info(lt.STARTS.format(self.chat_id, type(self).__name__))

    def send_message(self, *args, **kwargs):
        """
        This method makes the bot send a message to the chat.
        """
        BOT.send_message(self.chat_id, *args, **kwargs)

    def ask_polar(self, question: str, specifier: Union[CallbackQuery, int] = None):
        """
        This method makes the bot ask the chat a polar (general) question. The answer is expected to be given by
        clicking on one of the two provided inline buttons.

        Args:
            question (str): text of the message that will be sent.
            specifier (telegram.CallbackQuery or int, optional): If a callback query is given, the question will be
                asked by editing the query's message. If a chat id is given, the question is sent to the chat.
        """
        answers = [
            [
                InlineKeyboardButton(t.YES[self.language], callback_data='y'),
                InlineKeyboardButton(t.NO[self.language], callback_data='n')
            ]
        ]
        markup = InlineKeyboardMarkup(answers)

        if not specifier:
            self.send_message(question, reply_markup=markup)
        else:
            try:
                specifier.message.edit_text(question, reply_markup=markup)
            except AttributeError:  # if the specifier is a chat id, not a callback query
                BOT.send_message(specifier, question, reply_markup=markup)

    def respond(self, command: str, message: Message):
        """
        This method is called when the chat uses a command during an interaction. It makes the bot respond with a
        message, which is a reply in non-private chats.

        Some interactions are not individual and involve the whole group. When such interaction is started, no one from
        the group can use the command that starts the interaction, neither privately or in the group chat. In case of an
        attempt to do it the bot responds in the same chat, which can be not the chat with self.chat_id id. Hence, in
        order to respond in the same chat, this method uses telegram.Message.reply_text instead of
        Interaction.send_message (which is telegram.Bot.send_message(self.chat_id, ...)).

        Args:
            command (str): command received during the interaction.
            message (telegram.Message): message that the command is sent in.
        """
        msg = self.ALREADY_MESSAGE if command == self.COMMAND else self.ONGOING_MESSAGE
        message.reply_text(msg[self.language], quote=message.chat.type != Chat.PRIVATE)
        cl.info(lt.INTERRUPTS.format(message.from_user.id, command, type(self).__name__))

    @staticmethod
    def update_familiarity(user_id: int, familiarity: c.Familiarity, **kwargs):
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE chats SET familiarity = ? WHERE id = ?',
            (''.join(familiarity._replace(**kwargs)), user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.BECOMES_FAMILIAR.format(user_id, tuple(kwargs.keys())[0]))

    def terminate(self):
        """
        This method is called when the interaction is finished. It terminates the interaction by deleting the instance.
        """
        cl.info(lt.ENDS.format(self.chat_id, type(self).__name__))
        del current[self.chat_id]


current: dict[int, Interaction] = dict()


class Registration(Interaction):
    COMMAND, IS_PRIVATE = 'start', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_REGISTRATION, t.ALREADY_REGISTRATION

    def __init__(self, chat_id: int, chat_type: str):
        self.chat_id, self.language = chat_id, None
        super().__init__(None)

        self.is_student = not bool(c.CHAT_TYPES.index(chat_type))
        self.is_first = False  # whether the chat is the first one from the group to be registered
        self.username: str = None

        self.ask_language()
        self.next_action = self.ask_city

    def ask_language(self):
        """
        This method makes the bot ask the chat their language. The options are provided as inline buttons.
        """
        languages = [
            [InlineKeyboardButton(l, callback_data=str(i)) for i, l in enumerate(c.LANGUAGES)]
        ]
        markup = InlineKeyboardMarkup(languages)

        self.send_message(t.ASK_LANGUAGE, reply_markup=markup)

    def ask_city(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their language. If the update is
        not caused by choosing a language (by clicking on one of the provided inline buttons), it is ignored. Otherwise,
        the chosen language is saved and the bot asks the chat their city. The options are provided as inline buttons.

        Args:
            update (telegram.Update): update received after the chat is asked their language.
        """
        query = update.callback_query

        try:
            self.language = int(query.data)
        except AttributeError:  # if the update is not caused by choosing the language
            return  # no response

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute('SELECT DISTINCT city FROM EDUs')
        cities: list[tuple[str]] = sorted(cursor.fetchall(), key=lambda city: a.string_sort_key(city[0]))
        cursor.close()
        connection.close()

        cities = [
            [InlineKeyboardButton(c[0], callback_data=c[0])] for c in cities
        ]
        markup = InlineKeyboardMarkup(cities)

        query.message.edit_text(t.ASK_CITY[self.is_student][self.language], reply_markup=markup)
        self.next_action = self.ask_edu

    def ask_edu(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their city. If the update is not
        caused by choosing a city (by clicking on one of the provided inline buttons), it is ignored. Otherwise, the bot
        ask the chat their EDU. The options are EDUs in the chosen city and are provided as inline buttons.

        Args:
            update (telegram.Update): update received after the chat is asked their city.
        """
        query = update.callback_query

        try:
            city = query.data
        except AttributeError:  # if the update is not caused by choosing the city
            return  # no response

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # records of EDUs in the chosen city
            'SELECT id, name FROM EDUs WHERE city = ?',
            (city,)
        )
        edus: list[tuple[int, str]] = sorted(cursor.fetchall(), key=lambda e: a.string_sort_key(e[1]))
        cursor.close()
        connection.close()

        edus = [
            [InlineKeyboardButton(e[1], callback_data=e[0])] for e in edus
        ]
        markup = InlineKeyboardMarkup(edus)

        query.message.edit_text(t.ASK_EDU[self.language], reply_markup=markup)
        self.next_action = self.ask_department

    def ask_department(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their EDU. If the update is not
        caused by choosing an EDU (by clicking on one of the provided inline buttons), it is ignored. Otherwise, the
        chosen EDU is saved and the bot ask the chat their department. The options are departments of the chosen EDU and
        are provided as inline buttons.

        Args:
            update (telegram.Update): update received after the chat is asked their EDU.
        """
        query = update.callback_query

        try:
            self.group_id = int(query.data)
        except AttributeError:  # if the update is not caused by choosing the EDU
            return  # no response

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'SELECT departments FROM EDUs WHERE id = ?',  # departments of the chosen EDU
            (self.group_id,)
        )
        departments = cursor.fetchone()[0].split()  # departments are stored sorted in the database
        cursor.close()
        connection.close()

        departments = [
            [InlineKeyboardButton(d, callback_data=str(i))] for i, d in enumerate(departments)
        ]
        markup = InlineKeyboardMarkup(departments)

        query.message.edit_text(t.ASK_DEPARTMENT[self.language], reply_markup=markup)
        self.next_action = self.ask_group_name

    def ask_group_name(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their department. If the update is
        not caused by choosing a department (by clicking on one of the provided inline buttons), it is ignored.
        Otherwise, the chosen department is saved and the bot asks the chat their group's name. The answer is expected
        as a text message.

        Args:
            update (telegram.Update): update received after the chat is asked their department.
        """
        query = update.callback_query

        try:
            self.group_id = self.group_id * 100 + int(query.data)  # 100 = 10^2, where 2 is how long a department id is
        except AttributeError:  # if the update is not caused by choosing the department
            return  # no response

        query.message.edit_text(t.ASK_GROUP_NAME[self.is_student][self.language])
        self.next_action = self.handle_group_name

    def handle_group_name(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their group's name. It checks
        whether the name is valid and finishes the registration if it is. Otherwise, the bot sends a message explaining
        why the entered name is invalid, which is a reply in non-private chats.

        Args:
            update (telegram.Update): update received after the chat is asked their group's name.
        """
        message = update.effective_message
        message_id = None if self.is_student else message.message_id
        entered_group_name = message.text

        if '\n' in entered_group_name:
            self.send_message(t.INVALID_GROUP_NAME[self.language], reply_to_message_id=message_id)
        elif (l := len(entered_group_name)) > c.MAX_GROUP_NAME_LENGTH:
            text = t.TOO_LONG_GROUP_NAME[self.language].format(l - c.MAX_GROUP_NAME_LENGTH)
            self.send_message(text, reply_to_message_id=message_id)
        else:
            registered_at = datetime.today().strftime(c.TIME_FORMAT)  # time the chat finished the registration
            group_name = entered_group_name.upper()

            self.determine_group_id(group_name)
            self.create_record(update, registered_at, group_name)
            cl.info(lt.REGISTERS.format(self.chat_id, self.group_id))

            self.send_message(t.INTRODUCTION[self.is_student][self.language])
            self.find_related_chats(entered_group_name)
            self.terminate()

    def determine_group_id(self, group_name: str):
        """
        This method is the first step of finishing the registration. It determines group id that is related to the chat.
        If the chat is the first one from the group to be registered, a new id is generated based on the chat's EDU and
        department. Otherwise, the existing id is found.

        Args:
            group_name (str): entered group name, converted to uppercase.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'SELECT id, name FROM groups WHERE id / 1000 = ?',
            (self.group_id,)
        )
        department_group_records = cursor.fetchall()
        cursor.close()
        connection.close()

        if department_group_records:  # if the chat is not the first one from the department to be registered

            for dgr in department_group_records:
                if dgr[1] == group_name:  # if the chat is not the first one from the group to be registered
                    self.group_id = dgr[0]  # taking id of the group
                    break
            else:  # if the chat is the first one from the group to be registered
                self.group_id = department_group_records[-1][0] + 1
                self.is_first = True

        else:  # if the chat is the first one from the department to be registered
            self.group_id *= 1000  # 1000 = 10^3, where 3 is how long a group id within a department (to be added) is
            self.is_first = True
            # the first group to be registered of a department has index 0 within the department

    def create_record(self, update: Update, registered_at: str, group_name: str):
        """
        This method is the second step of finishing the registration. It creates a new record in the database for the
        chat, saving its id, type (only the first letter: 'p' / 'g' / 's'), username (if unavailable, replaced with
        full name or first name for private chats, with title for others), language (0 for Ukrainian, 1 for English, 2
        for Russian), id of the related group in the EDU, role in the group (0 for ordinary, 1 for admin, 2 for leader),
        timetable for sending the notifications, familiarity with the bot's features, time when the chat has finished
        the registration.

        If the chat is the first one from the group to be registered, a new record for the group is also created, saving
        its id and name.

        Args:
            update (telegram.Update): update received after the group's name is entered.
            registered_at (str): time when the chat finished the registration (format: '%d.%m.%Y %H:%M:%S').
            group_name (str): entered group name, converted to uppercase.
        """
        chat = update.effective_chat

        if self.is_student:
            self.username = update.effective_user.name  # username / full name / first name
        else:
            self.username = chat.username or chat.title  # username / title

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'INSERT INTO chats (id, type, username, language, group_id, role, familiarity, registered)'
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (self.chat_id, c.CHAT_TYPES.index(chat.type), self.username, self.language, self.group_id,
             *c.STATIC_DEFAULT_USER, registered_at)
        )

        if self.is_first:  # if the chat is the first one from the group to be registered
            cursor.execute(
                'INSERT INTO groups (id, name) VALUES(?, ?)',
                (self.group_id, group_name)
            )

        connection.commit()
        cursor.close()
        connection.close()

    def find_related_chats(self, group_name: str):
        """
        This method is the third and the last step of finishing the registration, which the interaction is terminated
        after. It looks for records in the database that are related to (have the same group id with) the chat of the
        interaction which a record has just been created of.

        If the chat is private (the new user is a student), the method makes the bot show how many of their groupmates
        have already registered and how many group chats the group has registered (most groups only have one). Otherwise
        (the new chat is a chat of a group), the method makes the bot show which students from the group have
        already registered.

        Args:
            group_name (str): entered group name.
        """
        if self.is_first:  # if the chat is the first one from the group to be registered
            msg = t.NONE_FOUND if self.is_student else t.NO_STUDENTS_FOUND
            self.send_message(msg[self.language].format(group_name))
            return

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if self.is_student:  # if the new chat is a student
            cursor.execute(
                'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
                (self.group_id,)
            )
            num_groupmates = cursor.fetchone()[0] - 1  # w/o the registering student

            cursor.execute(
                'SELECT id FROM chats WHERE group_id = ? AND type <> 0',
                (self.group_id,)
            )
            group_chat_records: list[tuple[int]] = cursor.fetchall()
            num_group_chats = len(group_chat_records)

            if num_groupmates:  # if at least 1 of the groupmates has registered
                if num_group_chats:  # if at least 1 group chat has also been registered
                    text = t.BOTH_FOUND[self.language].format(num_groupmates, num_group_chats)
                else:  # if no group chats have been registered
                    text = t.GROUPMATES_FOUND[self.language].format(num_groupmates)
            else:  # if at least 1 group chat has been registered
                text = t.GROUP_CHATS_FOUND[self.language].format(num_group_chats)

            for gcr in group_chat_records:
                BOT.send_message(gcr[0], choice(t.NEW_GROUPMATE[self.language]).format(self.username))

        else:  # if the new chat is a chat of a group
            cursor.execute(
                'SELECT username FROM chats WHERE group_id = ? AND type = 0',
                (self.group_id,)
            )
            student_records = cursor.fetchall()
            student_usernames = tuple(sr[0] for sr in student_records)

            text = t.STUDENTS_FOUND[self.language].format(len(student_usernames), '\n'.join(student_usernames))

        self.send_message(text)

        cursor.close()
        connection.close()

    def respond(self, command: str, message: Message):
        if self.language:
            super().respond(command, message)


class LeaderConfirmation(Interaction):
    COMMAND, IS_PRIVATE = 'claim', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_LEADER_CONFIRMATION, t.ALREADY_LEADER_CONFIRMATION

    def __init__(self, record: c.ChatRecord, group_chat_record: tuple[int, int]):
        self.chat_id, self.language = group_chat_record
        self.group_id = record.group_id
        super().__init__(None)

        self.candidate_id = record.id
        self.candidate_username, self.candidate_language = record.username, record.language
        self.poll_message_id: Message = None
        self.num_votes, self.num_positive_votes = 0, 0
        self.late_claimers: list[tuple[int, int]] = list()

        self.send_confirmation_poll()
        self.next_action = self.handle_answer

    def send_confirmation_poll(self):
        """
        This method makes the bot send a leader confirmation poll to the group chat of the candidate's group. The answer
        is either positive or negative.
        """
        BOT.send_message(self.candidate_id, t.CONFIRMATION_POLL_SENT[self.candidate_language])

        options = [t.YES[self.language], t.NO[self.language]]
        question = t.LEADER_CONFIRMATION_QUESTION[self.language].format(self.candidate_username)
        self.poll_message_id = BOT.send_poll(self.chat_id, question, options, is_anonymous=False).message_id

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the leader confirmation poll is sent. If the update
        is not caused by giving a poll answer, it is ignored. Otherwise, the given answer is counted unless it is given
        by the candidate. If the number of votes has reached src.config.MIN_GROUPMATES_FOR_LEADER_CONFORMATION, it is
        checked whether the candidate is confirmed to be the group's leader. In the positive case, the candidate is made
        the group's leader.

        Args:
            update (telegram.Update): update received after the leader confirmation poll is sent.
        """
        answer = update.poll_answer

        try:
            user_id = answer.user.id
        except AttributeError:  # if the update is not caused by a poll answer
            return

        if user_id != self.candidate_id:  # if the answer is not given by the candidate
            self.num_votes += 1

            if not answer.option_ids[0]:  # if the answer is positive
                self.num_positive_votes += 1

            if self.num_votes == c.MIN_GROUPMATES_FOR_LEADER_CONFORMATION:  # if many enough groupmates have answered

                if self.handle_result():
                    candidate_msg, group_msg = t.YOU_CONFIRMED, t.LEADER_CONFIRMED
                else:
                    candidate_msg, group_msg = t.YOU_NOT_CONFIRMED, t.LEADER_NOT_CONFIRMED

                BOT.send_message(self.candidate_id, candidate_msg[self.language])

                try:
                    BOT.delete_message(self.chat_id, self.poll_message_id)
                except BadRequest:  # if it has been more than 48 hours since the poll message was sent
                    BOT.stop_poll(self.chat_id, self.poll_message_id)
                self.send_message(group_msg[self.language].format(self.candidate_username))

                self.terminate()

        else:  # if the answer is given by the candidate
            self.send_message(t.CHEATING_IN_LEADER_CONFIRMATION[self.language].format(self.candidate_username))

    def handle_result(self) -> bool:
        """
        This method is called when the number of votes reaches src.config.MIN_GROUPMATES_FOR_LEADER_CONFORMATION and
        checks whether the candidate is confirmed to be the group's leader. In the positive case, the candidate is made
        the leader by updating their record in the database.

        Return (bool): whether the candidate is confirmed to be the leader.
        """
        if self.num_positive_votes / c.MIN_GROUPMATES_FOR_LEADER_CONFORMATION > .5:
            connection = connect(c.DATABASE)
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE chats SET role = 2 WHERE id = ?',
                (self.candidate_id,)
            )
            connection.commit()
            cursor.close()
            connection.close()
            cl.info(lt.CONFIRMED.format(self.candidate_id, self.group_id))

            return True

        else:
            cl.info(lt.NOT_CONFIRMED.format(self.candidate_id, self.group_id))
            for i, l in self.late_claimers:
                BOT.send_message(i, t.CANDIDATE_NOT_CONFIRMED[l].format(self.candidate_username))

            return False

    def is_candidate(self, user_id: int) -> bool:
        """
        This method is called when someone from the candidate's group uses /claim. It checks whether the user is the
        candidate by comparing their ids.

        Args:
            user_id (int): id of the user who is using the command.

        Returns (bool): whether the user is the candidate of the ongoing leader confirmation.
        """
        return user_id == self.candidate_id

    def add_claimer(self, user_id: int, user_language: int):
        """
        This method is called when the candidate's groupmate uses /claim. It remembers the groupmate to notify them if
        the candidate will not be confirmed.

        Args:
            user_id (int): id of the groupmate who is using the command.
            user_language (int): language of the groupmate who is using the command.
        """
        self.late_claimers.append((user_id, user_language))


def displaying_commands(record: c.ChatRecord, update: Update):
    """
    This function is called when a registered user uses the command /commands. It makes the bot display commands that
    are available for the user's role. The message is a reply in non-private chats.

    Args: see src.managers.leaving.__doc__.
    """
    kpi_command = t.KPI_CAMPUS_COMMAND[record.language] if record.group_id // 10**5 == c.KPI_ID else ''

    non_ordinary_commands = ''
    if record.role > c.ORDINARY_ROLE:
        non_ordinary_commands += t.ADMIN_COMMANDS[record.language]
        if record.role > c.ADMIN_ROLE:
            non_ordinary_commands += t.LEADER_COMMANDS[record.language]

    if int(record.familiarity.commands):
        unfamiliar = ''
    else:
        unfamiliar = t.FT_COMMANDS[record.language]
        Interaction.update_familiarity(record.id, record.familiarity, commands='1')

    text = t.COMMANDS[record.language].format(kpi_command, non_ordinary_commands, unfamiliar)
    update.effective_message.reply_text(text, quote=update.effective_chat.type != Chat.PRIVATE)
    cl.info(lt.COMMANDS.format(record.id))


class AddingAdmin(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'trust', t.UNAVAILABLE_ADDING_ADMIN, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ADDING_ADMIN, t.ALREADY_ADDING_ADMIN

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        self.ask_new_admin()
        self.next_action = self.add_admin

    def ask_new_admin(self):
        """
        This method makes the bot ask the leader which of the group's ordinary students to make an admin. The options
        are provided as inline buttons.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # record of ordinary students from the group
            'SELECT id, username, language FROM chats WHERE group_id = ? AND role = 0 AND type = 0',
            (self.group_id,)
        )
        ordinary_records: list[tuple[int, str, int]] = sorted(cursor.fetchall(), key=lambda r: a.string_sort_key(r[1]))
        cursor.close()
        connection.close()

        ordinary_students = [
            [InlineKeyboardButton(r[1], callback_data=f'{r[0]} {r[1]} {r[2]}')] for r in ordinary_records
        ]
        markup = InlineKeyboardMarkup(ordinary_students)
        msg = t.ASK_NEW_ADMIN if self.is_familiar else t.FT_ASK_NEW_ADMIN
        self.send_message(msg[self.language], reply_markup=markup)

    def add_admin(self, update: Update):
        """
        This method is called when the bot receives an update after the leader is asked which of the group's ordinary
        students to make an admin. If the update is not caused by choosing an ordinary student (by clicking on one of
        the provided inline buttons), it is ignored. Otherwise, the chosen student is made an admin by updating their
        record, and the bot notifies them about the new abilities.

        Args:
            update (telegram.Update): update received after the leader is asked which of the group's ordinary students
                to make an admin.
        """
        query = update.callback_query
        try:
            new_admin = query.data.split()
        except AttributeError:  # if the update is not caused by choosing a student
            return  # no response

        if not self.is_familiar:  # if the leader is adding an admin for the first time
            self.update_familiarity(self.chat_id, self.familiarity, trust='1')

        new_admin_id, new_admin_username, new_admin_language = int(new_admin[0]), new_admin[1], int(new_admin[2])

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE chats SET role = 1 WHERE id = ?',
            (new_admin_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.ADDS_ADMIN.format(self.chat_id, new_admin_id))

        BOT.send_message(new_admin_id, t.YOU_NOW_ADMIN[new_admin_language].format(t.ADMIN_COMMANDS[new_admin_language]))
        query.message.edit_text(t.NOW_ADMIN[self.language].format(new_admin_username))

        self.terminate()


class RemovingAdmin(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'distrust', t.UNAVAILABLE_REMOVING_ADMIN, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_REMOVING_ADMIN, t.ALREADY_REMOVING_ADMIN

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        self.admin_id: int = None
        self.admin_username: str = None
        self.admin_language: int = None

        self.ask_admin()
        self.next_action = self.remove_admin

    def ask_admin(self):
        """
        This method makes the bot ask the leader which admin of the group to unmake an admin. The options are provided
        as inline buttons.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # record of ordinary students from the group
            'SELECT id, username, language FROM chats WHERE group_id = ? AND role = 1',
            (self.group_id,)
        )
        admin_records: list[tuple[int, str, int]] = sorted(cursor.fetchall(), key=lambda r: a.string_sort_key(r[1]))
        cursor.close()
        connection.close()

        admins = [
            [InlineKeyboardButton(r[1], callback_data=f'{r[0]} {r[1]} {r[2]}')] for r in admin_records
        ]
        markup = InlineKeyboardMarkup(admins)
        msg = t.ASK_ADMIN if self.is_familiar else t.FT_ASK_ADMIN
        self.send_message(msg[self.language], reply_markup=markup)

    def remove_admin(self, update: Update):
        """
        This method is called when the bot receives an update after the leader is asked which admin of the group to
        unmake an admin. If the update is not caused by choosing an admin (by clicking on one of the provided inline
        buttons), it is ignored. Otherwise, the chosen admin is made an ordinary student by updating their record in the
        database and the leader is asked whether they should be notified about this.

        Args:
            update (telegram.Update): update received after the leader is asked which admin of the group to unmake an
                admin.
        """
        query = update.callback_query

        try:
            admin = query.data.split()
        except AttributeError:  # if the update is not caused by choosing an admin
            return  # no response

        self.admin_id, self.admin_username, self.admin_language = int(admin[0]), admin[1], int(admin[2])

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE chats SET role = 0 WHERE id = ?',
            (self.admin_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.REMOVES_ADMIN.format(self.chat_id, self.admin_id))

        msg = t.ASK_TO_NOTIFY_FORMER if self.is_familiar else t.FT_ASK_TO_NOTIFY_FORMER
        self.ask_polar(msg[self.language].format(self.admin_username), query)
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        """
        This method is the last step of removing an admin, which the interaction is be terminated after. It is called
        when the bot receives an update after the leader is asked whether the former admin should be notified. If the
        update is not caused by giving an answer (by clicking on one of the provided inline buttons), it is ignored.
        Otherwise, if the answer is positive, the former admin is notified about losing some abilities.

        Args:
            update (telegram.Update): update received after the leader is asked whether the former admin should be
                notified.
        """
        query = update.callback_query

        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by giving an answer
            return  # no response

        if not self.is_familiar:  # if the leader is removing an admin for the first time
            self.update_familiarity(self.chat_id, self.familiarity, distrust='1')

        if answer == 'y':
            BOT.send_message(self.admin_id, t.YOU_NO_MORE_ADMIN[self.admin_language])
            cl.info(lt.FORMER_NOTIFIED.format(self.admin_id))
            query.message.edit_text(t.FORMER_ADMIN_NOTIFIED[self.language])
        else:
            query.message.edit_text(t.FORMER_NOT_NOTIFIED[self.language])

        self.terminate()


def displaying_events(record: c.ChatRecord, update: Update):
    """
    This function is called when a registered user uses the command /events. It makes the bot display upcoming events of
    the user's group. The message is a reply in non-private chats.

    Args: see src.manager.leaving.__doc__.
    """
    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(
        'SELECT events FROM groups WHERE id = ?',
        (record.group_id,)
    )
    events = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    try:
        events = tuple(f'{t.WEEKDAYS[int(e[0])][record.language]} {e[2:]}' for e in events.split('\n'))
    except AttributeError:  # if there are no upcoming events
        events = t.NO_EVENTS[record.language]
    else:
        events = '\n'.join(events)

    update.effective_message.reply_text(events, quote=update.effective_chat.type != Chat.PRIVATE)
    cl.info(lt.EVENTS.format(record.id))


def displaying_info(record: c.ChatRecord, update: Update):
    """
    This function is called when a registered user uses the command /info. It makes the bot display information that
    the user's group has saved. The message is a reply in non-private chats.

    Args: see src.manager.leaving.__doc__.
    """
    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(
        'SELECT info FROM groups WHERE id = ?',
        (record.group_id,)
    )
    info = cursor.fetchone()[0] or t.NO_INFO[record.language]
    cursor.close()
    connection.close()

    update.effective_message.reply_text(info, quote=update.effective_chat.type != Chat.PRIVATE)
    cl.info(lt.INFO.format(record.id))


class AddingEvent(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'new', t.UNAVAILABLE_ADDING_EVENT, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ADDING_EVENT, t.ALREADY_ADDING_EVENT

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        self.event: str = None
        self.event_log: str = None  # self.event cut to src.logs_text.CUT_LENGTH
        self.date: str = None
        self.datetime_: datetime = None
        self.weekday_index: int = None
        self.num_to_answer = 0

        msg = t.ASK_NEW_EVENT if self.is_familiar else t.FT_ASK_NEW_EVENT
        self.send_message(msg[self.language])
        self.next_action = self.handle_event

    def handle_event(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked the event. It checks
        whether the entered event is valid (contains no linebreaks) and asks the admin the event's date if it is.
        Otherwise, the bot sends a message explaining why the entered event is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked the event.
        """
        event = update.effective_message.text

        if '\n' not in event:
            self.event = event

            msg = t.ASK_DATE if self.is_familiar else t.FT_ASK_DATE
            self.send_message(msg[self.language])
            self.next_action = self.handle_date

        else:
            self.send_message(t.INVALID_EVENT[self.language])

    def handle_date(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked the entered event's date. It
        checks whether the entered date is valid and finishes the first part of the interaction (collecting information
        and saving the event) if it is. Otherwise, the bot sends a message explaining why the entered date is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked the entered event's date.
        """
        if not (text := self.reason_invalid(update.effective_message.text)):  # if the given date is valid
            if not self.is_familiar:  # if the admin is adding an event for the first time
                self.update_familiarity(self.chat_id, self.familiarity, new='1')

            self.save_event()

            self.notify()
            self.next_action = self.handle_answer

        else:  # if the given date is invalid
            self.send_message(text)

    def reason_invalid(self, date: str) -> Union[str, None]:
        """
        This method looks for the reason why the given date is invalid. It involves using src.config.DATE_PATTERN
        regular expression to check the format, and checks the given values for month and day of the month (and for hour
        and minute if time is also given). February's non-constant length is considered. The given date is always
        considered as the next time it comes, not of the current year.

        Args:
            date (str): the entered date.

        Returns (str or None): text describing why the date is invalid (to be sent to the admin). None if the date is
            valid.
        """
        dates = findall(c.DATE_PATTERN, date)

        if (l := len(dates)) == 1:  # if 1 date is given
            day_str, month_str, time, hour_str, minute_str = dates[0]

            day, month = int(day_str), int(month_str)
            if month <= 12:

                if month >= 1:
                    now = datetime.today()

                    next_february_year = now.year + 1 if now.month > 2 else now.year
                    next_february_length = 28 if next_february_year % 4 else 29
                    if day <= (31, next_february_length, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month - 1]:

                        if day >= 1:  # if the given date is valid
                            # if the given date of this year is yet to become past
                            year = now.year if datetime(now.year, month, day + 1) > now else now.year + 1
                            self.datetime_ = datetime(year, month, day)
                            self.weekday_index = int(self.datetime_.strftime('%u')) - 1  # 0 for Monday
                            self.date = f'{self.weekday_index} {day:02}.{month:02}'

                            if time:  # if time is given

                                hour, minute = int(hour_str), int(minute_str)
                                if hour <= 23:

                                    if minute <= 59:  # if the given time is valid
                                        self.datetime_ = datetime(year, month, day, hour, minute)
                                        self.date += f', {hour:02}:{minute:02}'
                                    else:
                                        return t.INVALID_MINUTE[self.language]

                                else:
                                    return t.INVALID_HOUR[self.language]

                        else:  # if the given day is 0
                            return t.DAY_0[self.language]

                    else:
                        return t.DAY_OVER_MONTH_LENGTH[self.language]

                else:  # if the given month is 0
                    return t.MONTH_0[self.language]

            else:
                return t.MONTH_OVER_12[self.language].format(month)

        elif not l:  # if no dates are given
            return t.INVALID_DATE[self.language]

        else:  # if multiple date are given
            return t.MULTIPLE_DATES[self.language]

        return None

    def save_event(self):
        """
        This method is the first step of finishing the first part of the interaction. It creates the string
        representation of the event from the provided information and updates record of the admin's group in the
        database by adding the event to upcoming events of th group. If there are events already, the new event is
        placed so that they are sorted by their date (within a day, events without time go last).
        """
        self.event = f'{self.date} — {self.event}'
        self.event_log = self.event if len(self.event) <= lt.CUT_LENGTH else f'{self.event[:lt.CUT_LENGTH - 3]}...'

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'SELECT events FROM groups WHERE id = ?',
            (self.group_id,)
        )
        try:
            events = cursor.fetchone()[0].split('\n')  # splitting events w/o the last \n
        except AttributeError:  # if the group has no upcoming events
            updated_events = f'{self.event}\n'
        else:
            length = len(events)
            for i in range(length):
                if self.datetime_ > a.str_to_datetime(events[length - i - 1]):  # if the new event is later
                    events.insert(length - i, self.event)  # the new event goes after the latest one of the earlier ones
                    break
            else:  # if the new event is the earliest one
                events.insert(0, self.event)

            updated_events = '\n'.join(events)

        cursor.execute(
            'UPDATE groups SET events = ? WHERE id = ?',
            (updated_events, self.group_id)
        )

        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.ADDS.format(self.chat_id, self.event_log, self.group_id))

    def notify(self):
        """
        This method is the second and the last step of finishing the first part of the interaction. It sends a
        notification about the new event to all chats that are related to the group. Each student is also asked whether
        they want the bot to send them reminders about the event. Asking the question makes the bot start the
        interaction with each student (all keys created by this in src.interactions.current reference the same
        interaction instance). This method also counts how many students have been asked so that the interaction can be
        terminated when the last student gives the answer.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'SELECT id, type, language, familiarity FROM chats WHERE group_id = ?',
            (self.group_id,)
        )
        related_records: list[tuple[int, int, int, str]] = cursor.fetchall()
        cursor.close()
        connection.close()

        # the event with the weekday on each language
        event = tuple(f'{t.WEEKDAYS[self.weekday_index][i]} {self.event[2:]}' for i in range(len(c.LANGUAGES)))
        for r in related_records:
            language = int(r[2])

            if not int(r[1]):  # if the record is of a private chat
                chat_id = int(r[0])
                current[chat_id] = self  # the student is now answering whether they want to be notified about the event

                msg = t.NEW_EVENT if int(c.Familiarity(*r[3]).answer_notify) else t.FT_NEW_EVENT
                self.ask_polar(msg[language].format(event[language], choice(t.ASK_TO_NOTIFY[language])), chat_id)
                self.num_to_answer += 1

            else:  # if the record is of a non-private chat
                BOT.send_message(int(r[0]), t.NEW_EVENT[language].format(event[language], ''))

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the student is asked whether they want the bot to
        send them reminders about the new event. If the update is not caused by giving the answer (by clicking on one of
        the two provided inline buttons), it is ignored. Otherwise, the bot counts the answer and replaces the question
        with a response, which depends from whether the interaction has already passed. If it has not and the answer is
        positive, .

        Args:
            update (telegram.Update): update.
        """
        query = update.callback_query

        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by giving the answer
            return  # no response

        self.num_to_answer -= 1

        user_id = update.effective_user.id
        record = a.get_chat_record(user_id)
        language, familiarity = record.language, record.familiarity

        # if the user is answering for the first time whether they want to be notified about the event
        if not int(familiarity.answer_notify):
            Interaction.update_familiarity(user_id, familiarity, answer_notify='1')

        has_passed = self.datetime_ < datetime.today()

        if answer == 'y':

            if not has_passed:
                update.effective_chat.send_message('If you see this, I am pretending to consider your answer, because '
                                                   'my creator has not designed the notification mechanism yet')
                log_msg, msg = lt.AGREES, t.EXPECT_NOTIFICATIONS
            else:
                log_msg, msg = lt.AGREES_LATE, t.WOULD_EXPECT_NOTIFICATIONS

        else:
            if not has_passed:
                log_msg, msg = lt.DISAGREES, t.EXPECT_NO_NOTIFICATIONS
            else:
                log_msg, msg = lt.DISAGREES_LATE, t.WOULD_EXPECT_NO_NOTIFICATIONS

        cl.info(log_msg.format(user_id, self.event_log))
        event = query.message.text.rpartition('\n\n')[0]
        query.message.edit_text(f"{event}\n\n{msg[language]}")

        if not self.num_to_answer:
            cl.info(lt.LAST_ANSWERS.format(self.group_id, self.event_log))

        del current[user_id]


class SavingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'save', t.UNAVAILABLE_SAVING_INFO, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_SAVING_INFO, t.ALREADY_SAVING_INFO

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        self.info: str = None

        msg = t.ASK_NEW_INFO if self.is_familiar else t.FT_ASK_NEW_INFO
        self.send_message(msg[self.language])
        self.next_action = self.handle_info

    def handle_info(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked information to save. It checks
        whether the information is valid (contains no empty lines) and saves it if it is. Otherwise, the
        bot sends a message explaining why the entered info is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked information to save.
        """
        info = update.effective_message.text
        if '\n\n' not in info:
            if not self.is_familiar:  # if the admin is saving info for the first time
                self.update_familiarity(self.chat_id, self.familiarity, save='1')

            self.info = info
            self.save_info()

            self.notify()
            self.terminate()

        else:
            self.send_message(t.INVALID_INFO[self.language])

    def save_info(self):
        """
        This method is the last step of saving information, which the interaction is terminates after. It updates record
        of the admin's group, adding the entered information to it, and notifies the group's students about it.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'SELECT info FROM groups WHERE id = ?',
            (self.group_id,)
        )
        info = cursor.fetchone()[0] or ''

        updated_info = f'{info}{self.info}\n\n'
        cursor.execute(
            'UPDATE groups SET info = ? WHERE id = ?',
            (updated_info, self.group_id)
        )

        connection.commit()
        cursor.close()
        connection.close()
        info_log = self.info if len(self.info) <= lt.CUT_LENGTH else f'{self.info[:lt.CUT_LENGTH - 3]}...'
        cl.info(lt.SAVES.format(self.chat_id, info_log.replace('\n', ' '), self.group_id))

    def notify(self):
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'SELECT id, language FROM chats WHERE group_id = ?',
            (self.group_id,)
        )
        student_records: list[tuple[int, int]] = cursor.fetchall()

        cursor.close()
        connection.close()

        for r in student_records:
            BOT.send_message(r[0], t.NEW_INFO[r[1]].format(self.info))


class DeletingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'delete', t.UNAVAILABLE_DELETING_INFO, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_DELETING_INFO, t.ALREADY_DELETING_INFO

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        self.info: list[str] = None
        self.one_left = False

        self.ask_info()
        self.next_action = self.delete_info

    def ask_info(self):
        """
        This method makes the bot ask the admin the group's saved information to delete. The options are provided as
        inline buttons.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # saved information of the admin's group
            'SELECT info FROM groups WHERE id = ?',
            (self.group_id,)
        )
        self.info = cursor.fetchone()[0].split('\n\n')
        cursor.close()
        connection.close()

        if len(self.info) == 1:
            self.one_left = True

        info = [  # using indices because information can be longer than 64, which is the limit for callback_data
            [InlineKeyboardButton(i, callback_data=str(index))] for index, i in enumerate(self.info)
        ]
        markup = InlineKeyboardMarkup(info)

        msg = t.ASK_INFO if self.is_familiar else t.FT_ASK_INFO
        self.send_message(msg[self.language], reply_markup=markup)

    def delete_info(self, update: Update):
        """
        This method is the last step of deleting the group's saved information, which the interaction is terminates
        after. It is called when the bot receives an update after the admin is asked the group's saved information to
        delete. If the update is not caused by choosing information (by clicking on one of the provided inline buttons),
        it is ignored. Otherwise, record of the admin's group is updated. It is necessary to get the group's saved
        information from the database again in order not to lose information that may have been saved by the admin's
        groupmates during the interaction.

        Args:
            update (telegram.Update): update received after the admin is asked the group's saved information to delete.
        """
        query = update.callback_query

        try:
            info = self.info[int(query.data)]
        except AttributeError:  # if the update is not caused by choosing information
            return  # no response

        if not self.is_familiar:  # if the admin is deleting some of the saved for the first time
            self.update_familiarity(self.chat_id, self.familiarity, delete='1')

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if not self.one_left:
            cursor.execute(  # saved information of the admin's group
                'SELECT info FROM groups WHERE id = ?',
                (self.group_id,)
            )
            updated_info = cursor.fetchone()[0].replace(f'{info}\n\n', '')
            cursor.execute(
                'UPDATE groups SET info = ? WHERE id = ?',
                (updated_info, self.group_id)
            )
        else:
            cursor.execute(
                'UPDATE groups SET info = NULL WHERE id = ?',
                (self.group_id,)
            )

        connection.commit()
        cursor.close()
        connection.close()
        info_log = info if len(info) <= lt.CUT_LENGTH else f'{info[:lt.CUT_LENGTH - 3]}...'
        cl.info(lt.DELETES.format(self.chat_id, info_log.replace('\n', ' '), self.group_id))

        query.message.edit_text(t.INFO_DELETED[self.language].format(info_log))
        self.terminate()


class ClearingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'clear', t.UNAVAILABLE_CLEARING_INFO, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CLEARING_INFO, t.ALREADY_CLEARING_INFO

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        msg = t.ASK_CLEARING_INFO if self.is_familiar else t.FT_ASK_CLEARING_INFO
        self.ask_polar(msg[self.language])
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        query = update.callback_query
        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by choosing the answer
            return  # no response

        if not self.is_familiar:  # if the admin is clearing the saved info for the first time
            self.update_familiarity(self.chat_id, self.familiarity, clear='1')

        if answer == 'y':
            query.message.edit_text(t.INFO_CLEARED[self.language])
        else:
            cl.info(lt.KEEPS.format(self.chat_id))
            query.message.edit_text(t.INFO_KEPT[self.language])

        self.terminate()

    def clear_info(self):
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE groups SET info = NULL WHERE id = ?',
            (self.group_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.CLEARS.format(self.chat_id, self.group_id))


# class AskingGroup(Interaction):  # 1 instance for all
#     COMMAND, UNAVAILABLE_MESSAGE = 'ask', t.UNAVAILABLE_ASKING_GROUP
#     ALREADY_MESSAGE, ONGOING_MESSAGE = t.ALREADY_ASKING_GROUP, t.ONGOING_ASKING_GROUP
#
#     def __init__(self, record: c.ChatRecord):
#         super().__init__(record.id, record.language)
#         self.question: str = None
#         self.group_chat_id, self.public_answers_message_id = None, None
#         self.answers: dict[int, list[str]] = None
#         self.num_answers_left: int = None
#         self.private_answers_message_id: int = None
#
#         self.ask_question()
#
#     def ask_question(self):
#         # declare self.question
#         self.next_action = self.ask_to_publish
#
#     def ask_to_publish(self, update: Update):  # if positive, the leader has to answer as well
#         # if positive, declare self.group_chat_id
#         self.next_action = self.send_message
#
#     def send_question(self, update: Update):
#         # self.answers,  = {id : [username, answer]}
#         # self.num_answers_left = len(self.answers)
#         # self.private_answers_message_id = self.send_message(answers).message_id
#         # if self.group_chat_id:
#         #   self.public_answers_message_id = BOT.send_message(self.group_chat_id, answers).message_id
#
#         # refuse = [[
#         #     InlineKeyboardButton(t.REFUSE_TO_ANSWER[self.language])
#         # ]]
#         # markup = InlineKeyboardMarkup(refuse)
#         # send question
#
#         # the interaction with the leader is over
#         self.next_action = self.update_answers
#
#     def update_answers(self, update: Update):
#         # respond
#         self.num_answers_left -= 1
#         # update
#         if not self.num_answers_left:  # if all the students have answered
#             # notify the leader (and the group chat)
#             self.terminate()


class ChangingLeader(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'resign', t.UNAVAILABLE_CHANGING_LEADER, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CHANGING_LEADER, t.ALREADY_CHANGING_LEADER

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        self.to_admin = True  # whether the leader role will be given to an admin

        self.ask_new_leader()
        self.next_action = self.change_leader

    def ask_new_leader(self):
        """
        This method makes the bot ask the leader which of their groupmates will be the group's new leader. The options
        are the group's admins (or ordinary groupmates) and are provided as inline buttons.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # records of the group's admins
            'SELECT id, username, language FROM chats WHERE group_id = ? AND role = 1',
            (self.group_id,)
        )
        candidate_records: list[tuple[int, str, int]] = cursor.fetchall()

        if not candidate_records:  # if the are no admins in the group
            cursor.execute(  # records of the leader's groupmates
                'SELECT id, username, language FROM chats WHERE group_id = ? AND role = 0 AND type = 0',
                (self.group_id,)
            )
            candidate_records: list[tuple[int, str, int]] = cursor.fetchall()
            self.to_admin = False  # the leader role will be given to an ordinary student

        cursor.close()
        connection.close()

        candidate_records: list[tuple[int, str, int]] = sorted(candidate_records, key=lambda r: a.string_sort_key(r[1]))

        candidates = [
            [InlineKeyboardButton(r[1], callback_data=f'{r[0]} {r[1]} {r[2]}')] for r in candidate_records
        ]
        markup = InlineKeyboardMarkup(candidates)

        msg = t.FT_ASK_NEW_LEADER if not self.is_familiar else t.ASK_NEW_LEADER
        self.send_message(msg[self.language], reply_markup=markup)

    def change_leader(self, update: Update):
        """
        This method is the last step of changing the group's leader, which the interaction is terminated after. It is
        called when the bot receives an update after the leader is asked which of the groupmates will become the group's
        new leader. If the update is not caused by choosing a groupmate (by clicking on one of the provided inline
        buttons), it is ignored. Otherwise, the chosen groupmate's and the leader's records are updated and the new
        leader is notified about the new abilities.

        Args:
            update (telegram.Update): update received after the leader is asked which of the groupmates will become the
                group's new leader.
        """
        query = update.callback_query

        try:
            new_leader = query.data.split()
        except AttributeError:  # if the update is not caused by choosing a candidate
            return  # no response

        if not self.is_familiar:  # if the leader is giving away their authorities for the first time
            self.update_familiarity(self.chat_id, self.familiarity, resign='1')

        new_leader_id, new_leader_username, new_leader_language = int(new_leader[0]), new_leader[1], int(new_leader[2])

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE chats SET role = 2 WHERE id = ?',
            (new_leader_id,)
        )
        cursor.execute(
            'UPDATE chats SET role = 0 WHERE id = ?',
            (self.chat_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.CHANGES_LEADER.format(self.chat_id, new_leader_id))

        new_commands = '' if self.to_admin else t.ADMIN_COMMANDS[new_leader_language]
        new_commands += t.LEADER_COMMANDS[new_leader_language]
        BOT.send_message(new_leader_id, t.YOU_NOW_LEADER[new_leader_language].format(new_commands))
        query.message.edit_text(t.NOW_LEADER[self.language].format(new_leader_username))
        self.terminate()


class Leaving(Interaction):
    COMMAND, IS_PRIVATE = 'leave', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_LEAVING, t.ALREADY_LEAVING

    def __init__(self, record: c.ChatRecord):
        super().__init__(record)

        msg = t.FT_ASK_LEAVING if not self.is_familiar else t.ASK_LEAVING
        self.ask_polar(msg[self.language])
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        """
        This method is the last step of leaving, which the interaction is terminated after. It is called when the bot
        receives an update after the user is asked whether they are sure to leave. If the update is not caused by giving
        the answer (by clicking on one of the provided inline buttons), it is ignored. Otherwise, if the answer is
        positive, the chat's record in the database is deleted.

        Args:
            update (telegram.Update): update received after the user is asked whether they are sure to leave.
        """
        query = update.callback_query
        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by choosing the answer
            return  # no response

        if not self.is_familiar:  # if the user is using /leave for the first time
            self.update_familiarity(self.chat_id, self.familiarity, leave='1')

        if answer == 'y':
            if self.delete_record():
                cl.info(lt.LEAVES.format(self.group_id))
            cl.info(lt.LEAVES.format(self.chat_id, self.group_id))
            query.message.edit_text(t.DATA_DELETED[self.language])
        else:
            cl.info(lt.STAYS.format(self.chat_id))
            query.message.edit_text(t.DATA_KEPT[self.language])

        self.terminate()

    def delete_record(self) -> bool:
        """
        This method deletes the chat's record in the database. If the chat is the last registered one from the group,
        records of the group's group chats and the group's record are also deleted.

        Returns (bool): whether the chat is the last registered one in the group.
        """
        is_last = False
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
            (self.group_id,)
        )

        if cursor.fetchone()[0] != 1:  # if the chat is not the last registered one from the group
            cursor.execute(  # deleting the chat's record
                'DELETE FROM chats WHERE id = ?',
                (self.chat_id,)
            )
        else:  # if the chat is the last registered one from the group
            is_last = True
            cursor.execute(  # deleting the chat's record and records of group chats of the chat's group
                'DELETE FROM chats WHERE group_id = ?',
                (self.group_id,)
            )
            cursor.execute(  # deleting record of the chat's group
                'DELETE FROM groups WHERE id = ?',
                (self.group_id,)
            )

        connection.commit()
        cursor.close()
        connection.close()

        return is_last

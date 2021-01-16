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
        UNAVAILABLE_MESSAGE (tuple[str] or None): message in case of an attempt to start the interaction with a role
            that it is unavailable for.
        ONGOING_MESSAGE (tuple[str]): message in case of an attempt to start a different interaction.
        ALREADY_MESSAGE (tuple[str]): message in case of using self.COMMAND during the interaction.
        CHAT_ID (int): id of the chat that the interaction is in.
        LANGUAGE (int): index of the language of the interaction, according to the indexation in src.text.LANGUAGES.
        next_action (Callable[[Update], None]): method that will make the bot take the next step of the interaction.
    """
    COMMAND: str
    IS_PRIVATE = True
    UNAVAILABLE_MESSAGE: tuple[str] = None
    ONGOING_MESSAGE: tuple[str]
    ALREADY_MESSAGE: tuple[str]
    CHAT_ID: int
    LANGUAGE: int

    next_action: Callable[[Update], None]

    def __init__(self, chat_id: int, language: int):
        """
        This method is called when an interaction is started. It initializes the instance's CHAT_ID and LANGUAGE
        attributes and adds the interaction to src.interactions.current.
        """
        self.CHAT_ID = chat_id
        self.LANGUAGE = language

        current[self.CHAT_ID] = self
        cl.info(lt.STARTS.format(self.CHAT_ID, type(self).__name__))

    def send_message(self, *args, **kwargs):
        """
        This method makes the bot send a message to the chat.
        """
        BOT.send_message(self.CHAT_ID, *args, **kwargs)

    def ask_polar(self, question: str, specifier: Union[CallbackQuery, int] = None):
        """
        This method makes the bot ask the chat a polar (general) question. The answer is expected to be given by
        clicking one of the two provided inline buttons.

        Args:
            question (str): text of the message that will be sent.
            specifier (telegram.CallbackQuery or int, optional): If a callback query is given, the question will be
                asked by editing the query's message. If a chat id is given, the question is sent to the chat.
        """
        answers = [
            [
                InlineKeyboardButton(t.YES[self.LANGUAGE], callback_data='y'),
                InlineKeyboardButton(t.NO[self.LANGUAGE], callback_data='n')
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
        attempt to do it the bot responds in the same chat, which can be not the chat with self.CHAT_ID id. Hence, in
        order to respond in the same chat, this method uses telegram.Message.reply_text instead of
        Interaction.send_message (which is telegram.Bot.send_message(self.CHAT_ID, ...)).

        Args:
            command (str): command received during the interaction.
            message (telegram.Message): message that the command is sent in.
        """
        text = self.ALREADY_MESSAGE if command == self.COMMAND else self.ONGOING_MESSAGE
        message.reply_text(text[self.LANGUAGE], quote=message.chat.type != Chat.PRIVATE)
        cl.info(lt.INTERRUPTS.format(message.from_user.id, command, type(self).__name__))

    def terminate(self):
        """
        This method is called when the interaction is finished. It terminates the interaction by deleting the instance.
        """
        cl.info(lt.ENDS.format(self.CHAT_ID, type(self).__name__))
        del current[self.CHAT_ID]


current: dict[int, Interaction] = dict()


class Registration(Interaction):
    COMMAND, IS_PRIVATE = 'start', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_REGISTRATION, t.ALREADY_REGISTRATION

    def __init__(self, chat_id: int, chat_type: str):
        # this subclass represents the only interaction that language value needs to change of
        super().__init__(chat_id, None)
        self.IS_PRIVATE = not bool(c.CHAT_TYPES.index(chat_type))

        self.group_id: int = None
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
            self.LANGUAGE = int(query.data)
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

        query.message.edit_text(t.ASK_CITY[self.IS_PRIVATE][self.LANGUAGE], reply_markup=markup)
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

        query.message.edit_text(t.ASK_EDU[self.LANGUAGE], reply_markup=markup)
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

        query.message.edit_text(t.ASK_DEPARTMENT[self.LANGUAGE], reply_markup=markup)
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

        query.message.edit_text(t.ASK_GROUP_NAME[self.IS_PRIVATE][self.LANGUAGE])
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
        message_id = None if self.IS_PRIVATE else message.message_id
        entered_group_name = message.text

        if '\n' in entered_group_name:
            self.send_message(t.INVALID_GROUP_NAME[self.LANGUAGE], reply_to_message_id=message_id)
        elif (l := len(entered_group_name)) > c.MAX_GROUP_NAME_LENGTH:
            text = t.TOO_LONG_GROUP_NAME[self.LANGUAGE].format(l - c.MAX_GROUP_NAME_LENGTH)
            self.send_message(text, reply_to_message_id=message_id)
        else:
            registered_at = datetime.today().strftime(c.TIME_FORMAT)  # time the chat finished the registration
            group_name = entered_group_name.upper()

            self.determine_group_id(group_name)
            self.create_record(update, registered_at, group_name)
            cl.info(lt.REGISTERS.format(self.CHAT_ID, self.group_id))

            self.send_message(t.INTRODUCTION[self.IS_PRIVATE][self.LANGUAGE])
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

        if self.IS_PRIVATE:
            self.username = update.effective_user.name  # username / full name / first name
        else:
            self.username = chat.username or chat.title  # username / title

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'INSERT INTO chats (id, type, username, language, group_id, role, timetable, familiar, registered)'
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (self.CHAT_ID, c.CHAT_TYPES.index(chat.type), self.username, self.LANGUAGE, self.group_id, *c.DEFAULT_USER,
             registered_at)
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
            text = t.NONE_FOUND if self.IS_PRIVATE else t.NO_STUDENTS_FOUND
            self.send_message(text[self.LANGUAGE].format(group_name))
            return

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if self.IS_PRIVATE:  # if the new chat is a student
            cursor.execute(
                'SELECT COUNT(id) FROM chats WHERE group_id = ? AND type = 0',
                (self.group_id,)
            )
            num_groupmates = cursor.fetchone()[0] - 1  # w/o the registering student

            cursor.execute(
                'SELECT id FROM chats WHERE group_id = ? AND type <> 0',
                (self.group_id,)
            )
            group_chat_records = cursor.fetchall()
            num_group_chats = len(group_chat_records)

            if num_groupmates:  # if at least 1 of the groupmates has registered
                if num_group_chats:  # if at least 1 group chat has also been registered
                    text = t.BOTH_FOUND[self.LANGUAGE].format(num_groupmates, num_group_chats)
                else:  # if no group chats have been registered
                    text = t.GROUPMATES_FOUND[self.LANGUAGE].format(num_groupmates)
            else:  # if at least 1 group chat has been registered
                text = t.GROUP_CHATS_FOUND[self.LANGUAGE].format(num_group_chats)

            for gcr in group_chat_records:
                BOT.send_message(gcr[0], choice(t.NEW_GROUPMATE[self.LANGUAGE]).format(self.username))

        else:  # if the new chat is a chat of a group
            cursor.execute(
                'SELECT username FROM chats WHERE group_id = ? AND type = 0',
                (self.group_id,)
            )
            student_records = cursor.fetchall()
            student_usernames = tuple(sr[0] for sr in student_records)

            text = t.STUDENTS_FOUND[self.LANGUAGE].format(len(student_usernames), '\n'.join(student_usernames))

        self.send_message(text)

        cursor.close()
        connection.close()

    def respond(self, command: str, message: Message):
        if self.LANGUAGE:
            super().respond(command, message)


class LeaderConfirmation(Interaction):
    COMMAND, IS_PRIVATE = 'claim', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_LEADER_CONFIRMATION, t.ALREADY_LEADER_CONFIRMATION

    def __init__(self, record: c.ChatRecord, group_chat_record: tuple[2]):
        super().__init__(*group_chat_record)
        self.CANDIDATE_ID = record.id
        self.CANDIDATE_USERNAME, self.CANDIDATE_LANGUAGE = record.username, record.language
        self.GROUP_ID = record.group_id
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
        options = [t.YES[self.LANGUAGE], t.NO[self.LANGUAGE]]

        question = t.LEADER_CONFIRMATION_QUESTION[self.LANGUAGE].format(self.CANDIDATE_USERNAME)
        self.poll_message_id = BOT.send_poll(self.CHAT_ID, question, options, is_anonymous=False).message_id

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

        if user_id != self.CANDIDATE_ID:  # if the answer is not given by the candidate
            self.num_votes += 1

            if not answer.option_ids[0]:  # if the answer is positive
                self.num_positive_votes += 1

            if self.num_votes == c.MIN_GROUPMATES_FOR_LEADER_CONFORMATION:  # if many enough groupmates have answered
                if self.handle_result():
                    candidate_text, group_text = t.YOU_CONFIRMED, t.LEADER_CONFIRMED
                else:
                    candidate_text, group_text = t.YOU_NOT_CONFIRMED, t.LEADER_NOT_CONFIRMED

                BOT.send_message(self.CANDIDATE_ID, candidate_text[self.LANGUAGE])

                try:
                    BOT.delete_message(self.CHAT_ID, self.poll_message_id)
                except BadRequest:  # if it has been more than 48 hours since the poll message was sent
                    BOT.stop_poll(self.CHAT_ID, self.poll_message_id)
                self.send_message(group_text[self.LANGUAGE].format(self.CANDIDATE_USERNAME))

                self.terminate()

        else:  # if the answer is given by the candidate
            self.send_message(t.CHEATING_IN_LEADER_CONFIRMATION[self.LANGUAGE].format(self.CANDIDATE_USERNAME))

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
                (self.CANDIDATE_ID,)
            )
            connection.commit()
            cursor.close()
            connection.close()
            cl.info(lt.CONFIRMED.format(self.CANDIDATE_ID, self.GROUP_ID))

            return True

        else:
            cl.info(lt.NOT_CONFIRMED.format(self.CANDIDATE_ID, self.GROUP_ID))
            for i, l in self.late_claimers:
                BOT.send_message(i, t.CANDIDATE_NOT_CONFIRMED[l].format(self.CANDIDATE_USERNAME))

            return False

    def is_candidate(self, user_id: int) -> bool:
        """
        This method is called when someone from the candidate's group uses /claim. It checks whether the user is the
        candidate by comparing their ids.

        Args:
            user_id (int): id of the user who is using the command.

        Returns (bool): whether the user is the candidate of the ongoing leader confirmation.
        """
        return user_id == self.CANDIDATE_ID

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
    text = t.COMMANDS[record.language].format(kpi_command, non_ordinary_commands)

    update.effective_message.reply_text(text, quote=update.effective_chat.type != Chat.PRIVATE)
    cl.info(lt.COMMANDS.format(record.id))


class AddingAdmin(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE = 'trust', t.UNAVAILABLE_ADDING_ADMIN
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ADDING_ADMIN, t.ALREADY_ADDING_ADMIN

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id

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
            (self.GROUP_ID,)
        )
        ordinary_records: list[tuple[int, str, int]] = sorted(cursor.fetchall(), key=lambda r: a.string_sort_key(r[1]))
        cursor.close()
        connection.close()

        ordinary_students = [
            [InlineKeyboardButton(r[1], callback_data=f'{r[0]} {r[1]} {r[2]}')] for r in ordinary_records
        ]
        markup = InlineKeyboardMarkup(ordinary_students)

        self.send_message(t.ASK_NEW_ADMIN[self.LANGUAGE], reply_markup=markup)

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
        cl.info(lt.ADDS_ADMIN.format(self.CHAT_ID, new_admin_id))

        BOT.send_message(new_admin_id, t.YOU_NOW_ADMIN[new_admin_language].format(t.ADMIN_COMMANDS[new_admin_language]))
        query.message.edit_text(t.NOW_ADMIN[self.LANGUAGE].format(new_admin_username))
        self.terminate()


class RemovingAdmin(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE = 'distrust', t.UNAVAILABLE_REMOVING_ADMIN
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_REMOVING_ADMIN, t.ALREADY_REMOVING_ADMIN

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id
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
            (self.GROUP_ID,)
        )
        admin_records: list[tuple[int, str, int]] = sorted(cursor.fetchall(), key=lambda r: a.string_sort_key(r[1]))
        cursor.close()
        connection.close()

        admins = [
            [InlineKeyboardButton(r[1], callback_data=f'{r[0]} {r[1]} {r[2]}')] for r in admin_records
        ]
        markup = InlineKeyboardMarkup(admins)

        self.send_message(t.ASK_ADMIN[self.LANGUAGE], reply_markup=markup)

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
        cl.info(lt.REMOVES_ADMIN.format(self.CHAT_ID, self.admin_id))

        self.ask_polar(t.ASK_TO_NOTIFY_FORMER[self.LANGUAGE].format(self.admin_username), query)
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

        if answer == 'y':
            notification_text = t.YOU_NO_MORE_ADMIN[self.admin_language].format(t.ADMIN_COMMANDS[self.admin_language])
            BOT.send_message(self.admin_id, notification_text)
            cl.info(lt.FORMER_NOTIFIED.format(self.admin_id))

            text = t.FORMER_ADMIN_NOTIFIED
        else:
            text = t.FORMER_ADMIN_NOT_NOTIFIED

        query.message.edit_text(text[self.LANGUAGE])
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
    COMMAND, UNAVAILABLE_MESSAGE = 'new', t.UNAVAILABLE_ADDING_EVENT
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ADDING_EVENT, t.ALREADY_ADDING_EVENT

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id
        self.event: str = None
        self.event_log: str = None  # self.event cut to src.logs_text.CUT_LENGTH
        self.date: str = None
        self.datetime_: datetime = None
        self.weekday_index: int = None
        self.num_to_answer: int = None

        self.send_message(t.ASK_NEW_EVENT[self.LANGUAGE])
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
            self.send_message(t.ASK_DATE[self.LANGUAGE])
            self.next_action = self.handle_date
        else:
            self.send_message(t.INVALID_EVENT[self.LANGUAGE])

    def handle_date(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked the entered event's date. It
        checks whether the entered date is valid and finishes the first part of the interaction (collecting information
        and saving the event) if it is. Otherwise, the bot sends a message explaining why the entered date is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked the entered event's date.
        """
        if not (text := self.reason_invalid(update.effective_message.text)):  # if the given date is valid
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
                                        return t.INVALID_MINUTE[self.LANGUAGE]

                                else:
                                    return t.INVALID_HOUR[self.LANGUAGE]

                        else:  # if the given day is 0
                            return t.DAY_0[self.LANGUAGE]

                    else:
                        return t.DAY_OVER_MONTH_LENGTH[self.LANGUAGE]

                else:  # if the given month is 0
                    return t.MONTH_0[self.LANGUAGE]

            else:
                return t.MONTH_OVER_12[self.LANGUAGE].format(month)

        elif not l:  # if no dates are given
            return t.INVALID_DATE[self.LANGUAGE]

        else:  # if multiple date are given
            return t.MULTIPLE_DATES[self.LANGUAGE]

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
            (self.GROUP_ID,)
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
            (updated_events, self.GROUP_ID)
        )

        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.ADDS.format(self.CHAT_ID, self.event_log, self.GROUP_ID))

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
            'SELECT id, type, language FROM chats WHERE group_id = ?',
            (self.GROUP_ID,)
        )
        related_records: list[tuple[int, int, int]] = cursor.fetchall()
        cursor.close()
        connection.close()

        # the event with the weekday on each language
        event = tuple(f'{t.WEEKDAYS[self.weekday_index][i]} {self.event[2:]}' for i in range(len(c.LANGUAGES)))
        self.num_to_answer = 0

        for r in related_records:
            language = int(r[2])

            if not int(r[1]):  # if the record is of a private chat
                chat_id = int(r[0])
                current[chat_id] = self  # the student is now answering whether they want to be notified about the event

                text = t.NEW_EVENT[language].format(event[language], choice(t.ASK_TO_NOTIFY[language]))
                self.ask_polar(text, chat_id)
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
        except AttributeError:  # if the update is not caused by giving an answer
            return  # no response

        has_passed = self.datetime_ < datetime.today()
        user_id = update.effective_user.id
        language = a.get_chat_record(user_id).language

        if answer == 'y':

            if not has_passed:
                update.effective_chat.send_message('If you see this, I am pretending to consider your answer, because '
                                                   'my creator has not designed the notification mechanism yet')
                log_text, text = lt.AGREES, t.EXPECT_NOTIFICATIONS[language]
            else:
                log_text, text = lt.AGREES_LATE, t.WOULD_EXPECT_NOTIFICATIONS[language]

        else:
            if not has_passed:
                log_text, text = lt.DISAGREES, t.EXPECT_NO_NOTIFICATIONS[language]
            else:
                log_text, text = lt.DISAGREES_LATE, t.WOULD_EXPECT_NO_NOTIFICATIONS[language]

        cl.info(log_text.format(user_id, self.event_log))
        event = query.message.text.rpartition('\n\n')[0]
        query.message.edit_text(f"{event}\n\n{text}")

        self.num_to_answer -= 1
        if not self.num_to_answer:
            cl.info(lt.LAST_ANSWERS.format(self.GROUP_ID, self.event_log))

        del current[user_id]


class SavingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE = 'save', t.UNAVAILABLE_SAVING_INFO
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_SAVING_INFO, t.ALREADY_SAVING_INFO

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id

        self.send_message(t.ASK_NEW_INFO[self.LANGUAGE])
        self.next_action = self.handle_info

    def handle_info(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked information to save. It checks
        whether the information is valid (contains no empty lines) and saves it if it is. Otherwise, the
        bot sends a message explaining why the entered info is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked information to save.
        """
        new_info = update.effective_message.text
        if '\n\n' not in new_info:
            self.save_info(new_info)
            self.terminate()
        else:
            self.send_message(t.INVALID_INFO[self.LANGUAGE])

    def save_info(self, new_info: str):
        """
        This method is the last step of saving information, which the interaction is terminates after. It updates record
        of the admin's group, adding the entered information to it, and notifies the group's students about it.

        Args:
            new_info (str): the entered information.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'SELECT info FROM groups WHERE id = ?',
            (self.GROUP_ID,)
        )
        info = cursor.fetchone()[0] or ''

        updated_info = f'{info}{new_info}\n\n'

        cursor.execute(
            'UPDATE groups SET info = ? WHERE id = ?',
            (updated_info, self.GROUP_ID)
        )

        cursor.execute(
            'SELECT id, language FROM chats WHERE group_id = ?',
            (self.GROUP_ID,)
        )
        student_records: list[tuple[int, int]] = cursor.fetchall()

        connection.commit()
        cursor.close()
        connection.close()
        short_new_info = new_info if len(new_info) <= lt.CUT_LENGTH else f'{new_info[:lt.CUT_LENGTH - 3]}...'
        cl.info(lt.SAVES.format(self.CHAT_ID, short_new_info, self.GROUP_ID))

        for r in student_records:
            BOT.send_message(r[0], t.NEW_INFO[r[1]].format(new_info))


class DeletingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE = 'delete', t.UNAVAILABLE_DELETING_INFO
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_DELETING_INFO, t.ALREADY_DELETING_INFO

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id
        self.info: list[str] = None

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
            (self.GROUP_ID,)
        )
        self.info = cursor.fetchone()[0].split('\n\n')
        cursor.close()
        connection.close()

        info = [  # using indices because information can be longer than 64, which is the limit for callback_data
            [InlineKeyboardButton(i, callback_data=str(index))] for index, i in enumerate(self.info)
        ]
        markup = InlineKeyboardMarkup(info)

        self.send_message(t.ASK_INFO[self.LANGUAGE], reply_markup=markup)

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

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # saved information of the admin's group
            'SELECT info FROM groups WHERE id = ?',
            (self.GROUP_ID,)
        )
        updated_info = cursor.fetchone()[0].replace(f'{info}\n\n', '')
        cursor.execute(
            'UPDATE groups SET info = ? WHERE id = ?',
            (updated_info, self.GROUP_ID)
        )

        connection.commit()
        cursor.close()
        connection.close()
        short_info = info if len(info) <= lt.CUT_LENGTH else f'{info[:lt.CUT_LENGTH - 3]}...'
        cl.info(lt.DELETES.format(self.CHAT_ID, short_info, self.GROUP_ID))

        query.message.edit_text(t.INFO_DELETED[self.LANGUAGE].format(short_info))
        self.terminate()


class ClearingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE = 'clear', t.UNAVAILABLE_CLEARING_INFO
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CLEARING_INFO, t.ALREADY_CLEARING_INFO

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id

        self.ask_polar(t.ASK_CLEARING_INFO[self.LANGUAGE])
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        query = update.callback_query
        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by choosing the answer
            return  # no response

        if answer == 'y':
            if self.clear_info():
                cl.info(lt.CLEARS.format(self.GROUP_ID))
            query.message.edit_text(t.INFO_CLEARED[self.LANGUAGE])
        else:
            cl.info(lt.KEEPS.format(self.CHAT_ID))
            query.message.edit_text(t.INFO_KEPT[self.LANGUAGE])

        self.terminate()

    def clear_info(self):
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE groups SET info = NULL WHERE id = ?',
            (self.GROUP_ID,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.CLEARS.format(self.CHAT_ID, self.GROUP_ID))


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
#         #     InlineKeyboardButton(t.REFUSE_TO_ANSWER[self.LANGUAGE])
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
    COMMAND, UNAVAILABLE_MESSAGE = 'resign', t.UNAVAILABLE_CHANGING_LEADER
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CHANGING_LEADER, t.ALREADY_CHANGING_LEADER

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id
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
            (self.GROUP_ID,)
        )
        candidate_records: list[tuple[int, str, int]] = cursor.fetchall()

        if not candidate_records:  # if the are no admins in the group
            cursor.execute(  # records of the leader's groupmates
                'SELECT id, username, language FROM chats WHERE group_id = ? AND role = 0 AND type = 0',
                (self.GROUP_ID,)
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

        self.send_message(t.ASK_NEW_LEADER[self.LANGUAGE], reply_markup=markup)

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

        new_leader_id, new_leader_username, new_leader_language = int(new_leader[0]), new_leader[1], int(new_leader[2])

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE chats SET role = 2 WHERE id = ?',
            (new_leader_id,)
        )
        cursor.execute(
            'UPDATE chats SET role = 0 WHERE id = ?',
            (self.CHAT_ID,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        cl.info(lt.CHANGES_LEADER.format(self.CHAT_ID, new_leader_id))

        new_commands = '' if self.to_admin else t.ADMIN_COMMANDS[new_leader_language]
        new_commands += t.LEADER_COMMANDS[new_leader_language]
        BOT.send_message(new_leader_id, t.YOU_NOW_LEADER[new_leader_language].format(new_commands))
        query.message.edit_text(t.NOW_LEADER[self.LANGUAGE].format(new_leader_username))
        self.terminate()


class Leaving(Interaction):
    COMMAND, IS_PRIVATE = 'leave', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_LEAVING, t.ALREADY_LEAVING

    def __init__(self, record: c.ChatRecord):
        super().__init__(record.id, record.language)
        self.GROUP_ID = record.group_id

        self.ask_polar(t.ASK_LEAVING[self.LANGUAGE])
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

        if answer == 'y':
            if self.delete_record():
                cl.info(lt.LEAVES.format(self.GROUP_ID))
            cl.info(lt.LEAVES.format(self.CHAT_ID, self.GROUP_ID))
            query.message.edit_text(t.DATA_DELETED[self.LANGUAGE])
        else:
            cl.info(lt.STAYS.format(self.CHAT_ID))
            query.message.edit_text(t.DATA_KEPT[self.LANGUAGE])

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
            (self.GROUP_ID,)
        )

        if cursor.fetchone()[0] != 1:  # if the chat is not the last registered one from the group
            cursor.execute(  # deleting the chat's record
                'DELETE FROM chats WHERE id = ?',
                (self.CHAT_ID,)
            )
        else:  # if the chat is the last registered one from the group
            is_last = True
            cursor.execute(  # deleting the chat's record and records of group chats of the chat's group
                'DELETE FROM chats WHERE group_id = ?',
                (self.GROUP_ID,)
            )
            cursor.execute(  # deleting record of the chat's group
                'DELETE FROM groups WHERE id = ?',
                (self.GROUP_ID,)
            )

        connection.commit()
        cursor.close()
        connection.close()

        return is_last

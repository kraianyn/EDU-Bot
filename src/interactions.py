from datetime import datetime
from random import choice
from typing import Callable, Union
from re import findall
from sqlite3 import connect

from telegram.ext import Updater
from telegram import Update, Chat, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.error import BadRequest

import src.auxiliary as a
import src.text as t
from src.bot_info import TOKEN
import src.config as c
import src.loggers as l

updater = Updater(TOKEN)
bot = updater.bot


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
        language (int): index of interaction's language, according to src.text.LANGUAGES.
        next_action (Callable[[Update], None]): method that makes the bot take the next step of the interaction.
    """
    COMMAND: str
    IS_PRIVATE: bool
    ONGOING_MESSAGE: tuple[str]
    ALREADY_MESSAGE: tuple[str]

    chat_id: int
    language: int
    next_action: Callable[[Update], None]

    def __init__(self, record: a.ChatRecord = None):
        """
        This method is called when an interaction is started. It adds the interaction to src.interactions.current and if
        possible, initializes the interaction's attributes: chat_id, language, group_id (id of the group that the chat
        is related to), is_familiar (whether the user starts the interaction for the first time), familiarity
        (src.auxiliary.Familiarity, None if the user starts the interaction not for the first time).

        Args:
            record (src.auxiliary.ChatRecord, optional): record of the user who starts the interaction. If given, the
                attributes described above are initialized.
        """
        if record:
            self.chat_id, self.language, self.group_id = record.id, record.language, record.group_id

            familiarity = a.Familiarity(*record.familiarity)
            self.is_familiar = bool(int(getattr(familiarity, self.COMMAND)))
            self.familiarity = None if self.is_familiar else familiarity

        current[self.chat_id] = self
        l.cl.info(l.STARTS.format(self.chat_id, type(self).__name__))

    def send_message(self, *args, **kwargs) -> Message:
        """
        This method makes the bot send a message to the chat.

        Returns (telegram.Message): the sent message.
        """
        return bot.send_message(self.chat_id, *args, **kwargs)

    def ask_polar(self, question: str, query: CallbackQuery = None) -> Message:
        """
        This method makes the bot ask the chat a polar (general) question. The options are provided as two inline
        buttons.
        Args:
            question (str): text of the message that will be sent.
            query (telegram.CallbackQuery, optional): If given, the question will be asked by editing the query's
                message.
        """
        answers = [[
            InlineKeyboardButton(t.YES[self.language], callback_data='y'),
            InlineKeyboardButton(t.NO[self.language], callback_data='n')
        ]]
        markup = InlineKeyboardMarkup(answers)

        if not query:
            return self.send_message(question, reply_markup=markup)
        else:
            return query.message.edit_text(question, reply_markup=markup)

    def respond(self, command: str, message: Message):
        """
        This method makes the bot respond if the user uses a command during the interaction. If the command is used in a
        non-private chat, the response is a reply.

        Some interactions are not individual and involve the whole group. When a student is having such interaction, no
        one from the group can start it, neither privately or in the group chat. In case of an attempt to do it, the bot
        should in the same chat, which can be not the chat of the interaction. Hence, in order to respond in the same
        chat, this method uses telegram.Message.reply_text instead of Interaction.send_message.

        Args:
            command (str): command used during the interaction.
            message (telegram.Message): message that the command is sent in.
        """
        text = (self.ALREADY_MESSAGE if command == self.COMMAND else self.ONGOING_MESSAGE)[self.language]
        message.reply_text(text, quote=message.chat.type != Chat.PRIVATE)
        l.cl.info(l.INTERRUPTS.format(message.from_user.id, command, type(self).__name__))

    @staticmethod
    def update_familiarity(user_id: int, familiarity: a.Familiarity, **kwargs):
        """
        This method updates the user's familiarity with the bot's interactions.

        Args:
            user_id (int): id of the user that familiarity will be updated of.
            familiarity (src.auxiliary.Familiarity): the user's current familiarity.
            kwargs: new values that familiarity fields will be set to.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # updating the user's familiarity
            'UPDATE chats SET familiarity = ? WHERE id = ?',
            (''.join(familiarity._replace(**kwargs)), user_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.BECOMES_FAMILIAR.format(user_id, tuple(kwargs.keys())[0]))

    def terminate(self):
        """
        This method terminates the interaction by deleting the instance in src.interactions.current.
        """
        del current[self.chat_id]
        l.cl.info(l.ENDS.format(self.chat_id, type(self).__name__))


current: dict[int, Interaction] = dict()


class Registration(Interaction):
    COMMAND, IS_PRIVATE = 'start', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_REGISTRATION, t.ALREADY_REGISTRATION

    def __init__(self, chat_id: int, chat_type: str):
        self.chat_id, self.language = chat_id, None
        super().__init__()
        self.is_student = not bool(c.CHAT_TYPES.index(chat_type))
        self.is_first = False  # whether the chat is the first one from the group to be registered
        self.username: str = None

        self.ask_language()
        self.next_action = self.ask_city

    def ask_language(self):
        """
        This method makes the bot ask the chat their language. The options are provided as inline buttons.
        """
        languages = [[
            InlineKeyboardButton(language, callback_data=str(index)) for index, language in enumerate(c.LANGUAGES)
        ]]
        markup = InlineKeyboardMarkup(languages)

        self.send_message(t.ASK_LANGUAGE, reply_markup=markup)

    def ask_city(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their language. If the update is
        not caused by choosing one (by clicking on one of the provided inline buttons), it is ignored. Otherwise, the
        chosen language is saved and the chat is asked their city. The options are provided as inline buttons.

        Args:
            update (telegram.Update): update received after the chat is asked their language.
        """
        query = update.callback_query

        try:
            self.language = int(query.data)
        except AttributeError:  # if the update is not caused by choosing the language
            return  # no response

        cities = [
            [InlineKeyboardButton(city, callback_data=city)] for city in self.get_cities()
        ]
        markup = InlineKeyboardMarkup(cities)
        query.message.edit_text(t.ASK_CITY[self.is_student][self.language], reply_markup=markup)
        self.next_action = self.ask_edu

    @staticmethod
    def get_cities() -> list[str]:
        """
        Returns (list[str]): sorted list of all cities in the database.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute('SELECT DISTINCT city FROM EDUs')
        cities: list[str] = [city[0] for city in cursor.fetchall()]

        cursor.close()
        connection.close()

        cities.sort(key=a.string_sort_key)
        return cities

    def ask_edu(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their city. If the update is not
        caused by choosing one (by clicking on one of the provided inline buttons), it is ignored. Otherwise, the chat
        is asked their EDU. The options are EDUs in the chosen city and are provided as inline buttons.

        Args:
            update (telegram.Update): update received after the chat is asked their city.
        """
        query = update.callback_query

        try:
            city = query.data
        except AttributeError:  # if the update is not caused by choosing the city
            return  # no response

        edus = [
            [InlineKeyboardButton(name, callback_data=edu_id)] for edu_id, name in self.get_edus(city)
        ]
        markup = InlineKeyboardMarkup(edus)

        query.message.edit_text(t.ASK_EDU[self.language], reply_markup=markup)
        self.next_action = self.ask_department

    @staticmethod
    def get_edus(city: str) -> list[tuple[int, str]]:
        """
        Returns (list[tuple[int, str]]): EDUs in the given city, sorted by their name. Namely, list of tuples containing
            the EDUs id and full name.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # records of EDUs in the chosen city
            'SELECT id, name FROM EDUs WHERE city = ?',
            (city,)
        )
        edus: list[tuple[int, str]] = cursor.fetchall()

        cursor.close()
        connection.close()

        edus.sort(key=lambda e: a.string_sort_key(e[1]))
        return edus

    def ask_department(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their EDU. If the update is not
        caused by choosing one (by clicking on one of the provided inline buttons), it is ignored. Otherwise, the
        chosen EDU is considered and the chat is asked their department. The options are departments of the chosen EDU
        and are provided as inline buttons.

        Args:
            update (telegram.Update): update received after the chat is asked their EDU.
        """
        query = update.callback_query

        try:
            self.group_id = int(query.data)
        except AttributeError:  # if the update is not caused by choosing the EDU
            return  # no response

        departments = self.get_departments()
        departments = [
            [InlineKeyboardButton(name, callback_data=str(department_id)) for department_id, name in row]
            for row in [departments[i:i + 4] for i in range(0, len(departments), 4)]
        ]
        markup = InlineKeyboardMarkup(departments)

        query.message.edit_text(t.ASK_DEPARTMENT[self.language], reply_markup=markup)
        self.next_action = self.ask_group_name

    def get_departments(self) -> list[tuple[int, str]]:
        """
        Returns (list[tuple[int, str]]): departments of the chosen EDU, sorted by their names. Namely, list of tuples
            containing the department's id and name.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # departments of the chosen EDU
            'SELECT departments FROM EDUs WHERE id = ?',
            (self.group_id,)
        )
        departments: str = cursor.fetchone()[0]  # departments are stored sorted in the database

        cursor.close()
        connection.close()

        return list(enumerate(departments.split()))

    def ask_group_name(self, update: Update):
        """
        This method is called when the bot receives an update after the chat is asked their department. If the update is
        not caused by choosing one (by clicking on one of the provided inline buttons), it is ignored. Otherwise, the
        chosen department is considered and the chat is asked their group's name. The answer is expected as a text
        message.

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
        whether the given name is valid and finishes the registration if it is. Otherwise, the bot sends a message, a
        reply in non-private chats, explaining why the given name is invalid.

        Args:
            update (telegram.Update): update received after the chat is asked their group's name.
        """
        message = update.effective_message
        message_id = None if self.is_student else message.message_id
        entered_group_name = message.text

        if '\n' in entered_group_name:
            self.send_message(t.INVALID_GROUP_NAME[self.language], reply_to_message_id=message_id)
        elif (length := len(entered_group_name)) > c.MAX_GROUP_NAME_LENGTH:
            text = t.TOO_LONG_GROUP_NAME[self.language].format(length - c.MAX_GROUP_NAME_LENGTH)
            self.send_message(text, reply_to_message_id=message_id)
        else:
            registered_at = datetime.now().strftime(l.TIME_FORMAT)  # time the chat finished the registration
            group_name = entered_group_name.upper()

            self.determine_group_id(group_name)
            self.create_record(update, registered_at, group_name)
            if not self.is_first:
                a.update_group_chat_language(self.group_id)

            self.send_message(t.INTRODUCTION[self.is_student][self.language])
            self.report_on_related_chats(entered_group_name)
            self.terminate()

    def determine_group_id(self, group_name: str):
        """
        This method is the first step of finishing the registration. It determines the group id that is related to the
        chat. If the chat is the first one from the group to be registered, a new id is generated based on the chat's
        EDU and department. Otherwise, the existing id is taken.

        Args:
            group_name (str): the given group name, converted to uppercase.
        """
        department_group_records = self.get_department_group_records()

        if department_group_records:  # if the chat is not the first one from the department to be registered

            for group_id, name in department_group_records:
                if name == group_name:  # if the chat is not the first one from the group to be registered
                    self.group_id = group_id  # taking id of the group
                    break
            else:  # if the chat is the first one from the group to be registered
                self.group_id = group_id + 1
                self.is_first = True

        else:  # if the chat is the first one from the department to be registered
            self.group_id *= 1000  # 1000 = 10^3, where 3 is how long a group id within a department is
            self.is_first = True
            # the first group to be registered of a department has index 0 within the department

    def get_department_group_records(self) -> list[tuple[int, str]]:
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # groups of the chosen department of the chosen EDU
            'SELECT id, name FROM groups WHERE id / 1000 = ?',
            (self.group_id,)
        )
        department_group_records: list[tuple[int, str]] = cursor.fetchall()

        cursor.close()
        connection.close()

        return department_group_records

    def create_record(self, update: Update, registered_at: str, group_name: str):
        """
        This method is the second step of finishing the registration. It creates a new record in the database for the
        chat, saving its id, type index (according to src.config.CHAT_TYPES), username (if unavailable, replaced with
        full name or first name for private chats, with title for others), language index (according to
        src.config.LANGUAGES), id of the group that it is related to, time when the chat has finished the registration.
        For private chats, also are included src.config.STATIC_INITIAL_STUDENT values of the chat's role in the group
        and familiarity with the bot's interactions.

        If the chat is the first one from the group to be registered, a new record for the group is also created, saving
        its id and name.

        Args:
            update (telegram.Update): update received after the group's name is entered.
            registered_at (str): time when the chat finished the registration (format: '%d.%m.%Y %H:%M:%S').
            group_name (str): the given group name, converted to uppercase.
        """
        chat = update.effective_chat
        type_index = c.CHAT_TYPES.index(chat.type)

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if self.is_student:
            self.username = update.effective_user.name  # username / full name / first name
            cursor.execute(  # creating a user record
                'INSERT INTO chats (id, type, username, language, group_id, role, familiarity, registered)'
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (self.chat_id, type_index, self.username, self.language, self.group_id, c.INITIAL_ROLE,
                 c.INITIAL_FAMILIARITY, registered_at)
            )
        else:
            self.username = chat.username or chat.title  # username / title
            cursor.execute(  # creating a group-chat record
                'INSERT INTO chats (id, type, username, language, group_id, registered) VALUES (?, ?, ?, ?, ?, ?)',
                (self.chat_id, type_index, self.username, self.language, self.group_id, registered_at)
            )

        if self.is_first:  # if the chat is the first one from the group to be registered
            cursor.execute(  # creating a group record
                'INSERT INTO groups (id, name) VALUES(?, ?)',
                (self.group_id, group_name)
            )

        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.REGISTERS.format(self.chat_id, self.group_id))

    def report_on_related_chats(self, given_group_name: str):
        """
        This method is the third and the last step of finishing the registration, which the interaction is terminated
        after. It makes the bot show information about registered chats that are related to (have the same group id
        with) the new chat.

        If the chat is private (the new user is a student) and has made the number of registered students from the
        group, defined as src.config.MIN_GROUPMATES_FOR_LC, big enough for leader confirmation (LC), the students are
        notified about it. If the group has not registered a group chat, they are also reminded to do it, since it is
        necessary for LC.

        Args:
            given_group_name (str): the given group name.
        """
        if self.is_first:  # if the chat is the first one from the group to be registered
            text = (t.NONE_FOUND if self.is_student else t.NO_STUDENTS_FOUND)[self.language].format(given_group_name)
            self.send_message(text)
            return

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if self.is_student:  # if the new chat is a student
            cursor.execute(  # the new student's groupmates
                'SELECT id, language FROM chats '
                'WHERE group_id = ? AND type = 0 AND id <> ?',
                (self.group_id, self.chat_id)
            )
            groupmate_records: list[tuple[int, int]] = cursor.fetchall()

            cursor.execute(  # group chats of the student's group
                'SELECT id FROM chats '
                'WHERE group_id = ? AND type <> 0',
                (self.group_id,)
            )
            group_chat_records: list[tuple[int]] = cursor.fetchall()

            for r in group_chat_records:
                bot.send_message(r[0], choice(t.NEW_GROUPMATE[self.language]).format(self.username))

            num_groupmates, num_group_chats = len(groupmate_records), len(group_chat_records)
            text_leader, lc_available_msg = t.report_on_related_chats(num_groupmates, num_group_chats, self.language)

            if lc_available_msg:
                for user_id, language in groupmate_records:
                    text = t.LC_NOW_AVAILABLE[language].format(c.MIN_GROUPMATES_FOR_LC + 1, lc_available_msg[language])
                    bot.send_message(user_id, text)

        else:  # if the new chat is a chat of a group
            cursor.execute(  # the group's students
                'SELECT username FROM chats '
                'WHERE group_id = ? AND type = 0',
                (self.group_id,)
            )
            student_usernames = tuple(r[0] for r in cursor.fetchall())

            text_leader = t.STUDENTS_FOUND[self.language].format('\n'.join(student_usernames))

        self.send_message(text_leader)

        cursor.close()
        connection.close()

    def respond(self, command: str, message: Message):
        if self.language:  # if the chat has already provided their language
            super().respond(command, message)


class LeaderConfirmation(Interaction):
    COMMAND, IS_PRIVATE = 'claim', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ENTERING_YEARS, t.ALREADY_LC

    def __init__(self, record: a.ChatRecord, group_chat_record: tuple[int, int]):
        self.chat_id, self.language, self.group_id = record.id, record.language, record.group_id
        current[self.group_id] = self
        l.cl.info(l.STARTS.format(self.chat_id, type(self).__name__))

        self.username = record.username
        self.group_chat = group_chat_record

        self.poll_message_id: int = None
        self.num_votes, self.num_positive_votes = 0, 0
        self.late_claimers: list[tuple[int, int]] = list()

        self.send_confirmation_poll()
        self.next_action = self.handle_answer

    def send_confirmation_poll(self):
        """
        This method makes the bot send a leader confirmation poll to the group chat of the candidate's group. The
        options are positive and negative.
        """
        bot.send_message(self.chat_id, t.CONFIRMATION_POLL_SENT[self.language])

        options = [t.YES[self.group_chat[1]], t.NO[self.group_chat[1]]]
        question = t.LC_QUESTION[self.group_chat[1]].format(self.username)
        self.poll_message_id = bot.send_poll(self.group_chat[0], question, options, is_anonymous=False).message_id

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the leader confirmation poll is sent. If the update
        is not caused by giving a poll answer, it is ignored. Otherwise, the given answer is counted unless it is given
        by the candidate. If the number of votes reaches src.config.MIN_GROUPMATES_FOR_LEADER_CONFORMATION, the poll is
        deleted (closed) and it is checked whether the candidate is confirmed to be the group's leader.

        Args:
            update (telegram.Update): update received after the leader confirmation poll is sent.
        """
        answer = update.poll_answer

        try:
            user_id = answer.user.id
        except AttributeError:  # if the update is not caused by a poll answer
            return  # no response

        if user_id != self.chat_id:  # if the answer is not given by the candidate
            self.num_votes += 1

            if not answer.option_ids[0]:  # if the answer is positive
                self.num_positive_votes += 1

            if self.num_votes == c.MIN_GROUPMATES_FOR_LC:  # if many enough groupmates have answered

                try:
                    bot.delete_message(self.group_chat[0], self.poll_message_id)
                except BadRequest:  # if it has been more than 48 hours since the poll message was sent
                    bot.stop_poll(self.group_chat[0], self.poll_message_id)

                del current[self.group_id]

                if self.handle_result():
                    new_commands = t.ADMIN_COMMANDS[self.language] + t.LEADER_COMMANDS[self.language]
                    self.send_message(t.YOU_CONFIRMED[self.language].format(new_commands))
                    bot.send_message(self.group_chat[0], t.LEADER_CONFIRMED[self.group_chat[1]].format(self.username))

                    current[self.chat_id] = self
                    self.send_message(t.ASK_EDU_YEAR[self.language])
                    self.next_action = self.handle_year

                else:
                    self.send_message(t.YOU_NOT_CONFIRMED[self.language])
                    text = t.LEADER_NOT_CONFIRMED[self.group_chat[1]].format(self.username)
                    bot.send_message(self.group_chat[0], text)

        else:  # if the answer is given by the candidate
            bot.send_message(self.group_chat[0], t.CHEATING_IN_LC[self.language].format(self.username))

    def handle_result(self) -> bool:
        """
        This method checks whether the candidate is confirmed to be the group's leader. In the positive case, they are
        made the leader by updating their record in the database.

        Returns (bool): whether the candidate is confirmed to be the leader.
        """
        if self.num_positive_votes / c.MIN_GROUPMATES_FOR_LC > .5:
            connection = connect(c.DATABASE)
            cursor = connection.cursor()
            cursor.execute(  # making the candidate the group's leader
                'UPDATE chats SET role = 2 WHERE id = ?',
                (self.chat_id,)
            )
            connection.commit()
            cursor.close()
            connection.close()
            l.cl.info(l.CONFIRMED.format(self.chat_id))

            return True

        else:
            l.cl.info(l.NOT_CONFIRMED.format(self.chat_id))

            for user_id, language in self.late_claimers:
                bot.send_message(user_id, t.CANDIDATE_NOT_CONFIRMED[language].format(self.username))

            return False

    def is_candidate(self, user_id: int) -> bool:
        """
        This method checks whether a user is the candidate of the interaction.

        Args:
            user_id (int): id of the user who will be checked.

        Returns (bool): whether the user is the candidate of the ongoing leader confirmation.
        """
        return user_id == self.chat_id

    def add_claimer(self, user_id: int, user_language: int):
        """
        This method remembers the candidate's groupmate if they attempt to start leader confirmation. If the candidate
        will not be confirmed to be the group's leader, the groupmate will be notified about availability of the
        interaction.

        Args:
            user_id (int): id of the groupmate to remember.
            user_language (int): language of the groupmate to remember, according to src.text.LANGUAGES.
        """
        self.late_claimers.append((user_id, user_language))

    def handle_year(self, update: Update):
        """
        This method is called when the bot receives an update after the leader is asked what year their group are and
        how many years the group is going to study in total. It checks whether the given information is valid and
        finishes the interaction if it is. Otherwise, the bot sends a message explaining why the given information is
        invalid.

        Args:
            update (telegram.Update): update received after the leader is asked what year their group are and how many
                years the group is going to study in total.
        """
        edu_year = self.inspect_edu_year(update.effective_message.text)
        try:
            current_edu_year, all_edu_years = edu_year
        except ValueError:  # if the given EDU year is invalid
            self.send_message(edu_year)
        else:  # if the given EDU year is valid
            graduation_year = self.save_graduation_year(current_edu_year, all_edu_years)
            self.send_message(t.GRADUATION_YEAR_SAVED[self.language].format(graduation_year))
            self.terminate()

    def inspect_edu_year(self, edu_year: str) -> Union[tuple[int, int], str]:
        """
        This method looks for a possible reason why the given information about the group's years in the EDU is invalid.
        It involves using src.config.EDU_YEAR_PATTERN regular expression to check the format, and checks the given
        values for the current year and for how many years the group is going to study in total.

        Args:
            edu_year (str): the given information about the group's years in the EDU.

        Returns (tuple[int, int] or str): current year and how many years the group is going to study in total, if the
            information is valid. Otherwise, text describing why the given information is invalid.
        """
        edu_years = findall(c.EDU_YEAR_PATTERN, edu_year)

        if (num_edu_years := len(edu_years)) == 1:  # if 1 EDU year is given
            current_edu_year, all_edu_years = int(edu_years[0][0]), int(edu_years[0][1])

            if current_edu_year <= all_edu_years:
                if all_edu_years > c.MAX_EDU_YEARS:
                    return t.INVALID_ALL_EDU_YEARS[self.language]
            else:
                return t.INVALID_CURRENT_EDU_YEAR[self.language]

            return current_edu_year, all_edu_years

        elif not num_edu_years:  # if no years are given
            return t.INVALID_EDU_YEAR[self.language]

        else:  # if multiple years are given
            return t.MULTIPLE_EDU_YEARS[self.language]

    def save_graduation_year(self, current_edu_year: int, all_edu_years: int) -> int:
        """
        This method determines the group's graduation year and saves it bu updating the group's record in the database.

        Args:
            current_edu_year (int): the group's current year in the EDU.
            all_edu_years (int): how many years the group is going to study in total.

        Returns (int): year that the group graduates in.
        """
        now = datetime.now()
        is_first_term = now.month >= c.THRESHOLD_DATE[0] and now.day >= c.THRESHOLD_DATE[1]
        graduation_year = now.year + (all_edu_years - current_edu_year) + is_first_term

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE groups SET graduation = ? WHERE id = ?',
            (graduation_year - 2000, self.group_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.ENTERS_EDU_YEAR.format(self.chat_id, current_edu_year, all_edu_years))

        return graduation_year


def displaying_commands(record: a.ChatRecord, update: Update):
    """
    This function makes the bot send a message, a reply in non-private chats, containing commands that are available for
    the user. They depend from the user's role and EDU.

    Args: see src.managers.deleting_data.__doc__.
    """
    kpi_command = t.KPI_CAMPUS_COMMAND[record.language] if record.group_id // 10 ** 5 == c.KPI_ID else ''

    non_ordinary_commands = ''
    if record.role > c.ORDINARY_ROLE:
        non_ordinary_commands += t.ADMIN_COMMANDS[record.language]
        if record.role > c.ADMIN_ROLE:
            non_ordinary_commands += t.LEADER_COMMANDS[record.language]

    familiarity = a.Familiarity(*record.familiarity)
    if int(familiarity.commands):
        unfamiliar = ''
    else:
        unfamiliar = t.FT_COMMANDS[record.language]
        Interaction.update_familiarity(record.id, familiarity, commands='1')

    text = t.COMMANDS[record.language].format(kpi_command, non_ordinary_commands, unfamiliar)
    update.effective_message.reply_text(text, quote=update.effective_chat.type != Chat.PRIVATE)
    l.cl.info(l.COMMANDS.format(record.id))


class AddingAdmin(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'trust', t.UNAVAILABLE_ADDING_ADMIN, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ADDING_ADMIN, t.ALREADY_ADDING_ADMIN

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)

        self.ask_new_admin()
        self.next_action = self.add_admin

    def ask_new_admin(self):
        """
        This method makes the bot ask the leader which of their group's ordinary students to make an admin. The options
        are provided as inline buttons.
        """
        ordinary_students = [
            [InlineKeyboardButton(username, callback_data=f'{user_id} {username} {language}')]
            for user_id, username, language in self.get_ordinary_records()
        ]
        markup = InlineKeyboardMarkup(ordinary_students)

        text = (t.ASK_NEW_ADMIN if self.is_familiar else t.FT_ASK_NEW_ADMIN)[self.language]
        self.send_message(text, reply_markup=markup)

    def get_ordinary_records(self) -> list[tuple[int, str, int]]:
        """
        Returns (list[tuple[int, str, int]]): the group's ordinary students, sorted by their usernames or other
            identifiers. Namely, list of tuples containing the student's telegram id, username or other identifier, and
            language.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's ordinary students
            'SELECT id, username, language FROM chats '
            'WHERE group_id = ? AND role = 0',
            (self.group_id,)
        )
        ordinary_records: list[tuple[int, str, int]] = cursor.fetchall()

        cursor.close()
        connection.close()

        ordinary_records.sort(key=lambda r: a.string_sort_key(r[1]))
        return ordinary_records

    def add_admin(self, update: Update):
        """
        This method is the last step of adding an admin, which the interaction is terminated after. It is called when
        the bot receives an update after the leader is asked which of their group's ordinary students to make an admin.
        If the update is not caused by choosing one (by clicking on one of the provided inline buttons), it is ignored.
        Otherwise, the chosen student is made an admin by updating their record in the database, and is notified about
        the new abilities.

        Args:
            update (telegram.Update): update received after the leader is asked which of their group's ordinary students
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
        cursor.execute(  # making the chosen ordinary student an admin
            'UPDATE chats SET role = 1 WHERE id = ?',
            (new_admin_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.NOW_ADMIN.format(new_admin_id))

        bot.send_message(new_admin_id, t.YOU_NOW_ADMIN[new_admin_language].format(t.ADMIN_COMMANDS[new_admin_language]))
        query.message.edit_text(t.NOW_ADMIN[self.language].format(new_admin_username))

        self.terminate()


class RemovingAdmin(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'distrust', t.UNAVAILABLE_REMOVING_ADMIN, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_REMOVING_ADMIN, t.ALREADY_REMOVING_ADMIN

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)
        self.admin_id: int = None
        self.admin_username: str = None
        self.admin_language: int = None

        self.ask_admin()
        self.next_action = self.remove_admin

    def ask_admin(self):
        """
        This method makes the bot ask the leader which admin of their group to make an ordinary student. The options are
        provided as inline buttons.
        """
        admins = [
            [InlineKeyboardButton(username, callback_data=f'{user_id} {username} {language}')]
            for user_id, username, language in self.get_admin_records()
        ]
        markup = InlineKeyboardMarkup(admins)

        text = (t.ASK_ADMIN if self.is_familiar else t.FT_ASK_ADMIN)[self.language]
        self.send_message(text, reply_markup=markup)

    def get_admin_records(self) -> list[tuple[int, str, int]]:
        """
        Returns (list[tuple[int, str, int]]): the group's admins, sorted by their usernames or other identifiers.
            Namely, list of tuples containing the admin's telegram id, username or other identifier, and language.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's admins
            'SELECT id, username, language FROM chats '
            'WHERE group_id = ? AND role = 1',
            (self.group_id,)
        )
        admin_records: list[tuple[int, str, int]] = cursor.fetchall()

        cursor.close()
        connection.close()

        admin_records.sort(key=lambda r: a.string_sort_key(r[1]))
        return admin_records

    def remove_admin(self, update: Update):
        """
        This method is called when the bot receives an update after the leader is asked which admin of their group to
        make an ordinary student. If the update is not caused by choosing one (by clicking on one of the provided inline
        buttons), it is ignored. Otherwise, the chosen admin is made an ordinary student by updating their record in the
        database, and the leader is asked whether they admin be notified about this.

        Args:
            update (telegram.Update): update received after the leader is asked which admin of their group to make an
                ordinary student.
        """
        query = update.callback_query

        try:
            admin = query.data.split()
        except AttributeError:  # if the update is not caused by choosing an admin
            return  # no response

        self.admin_id, self.admin_username, self.admin_language = int(admin[0]), admin[1], int(admin[2])

        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # making the chosen admin an ordinary student
            'UPDATE chats SET role = 0 WHERE id = ?',
            (self.admin_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.NO_MORE_ADMIN.format(self.admin_id))

        msg = (t.ASK_TO_NOTIFY_FORMER if self.is_familiar else t.FT_ASK_TO_NOTIFY_FORMER)
        self.ask_polar(msg[self.language].format(self.admin_username), query)
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        """
        This method is the last step of removing an admin, which the interaction is terminated after. It is called
        when the bot receives an update after the leader is asked whether the former admin should be notified about
        losing the admin abilities. If the update is not caused by giving the answer (by clicking on one of the two
        provided inline buttons), it is ignored. Otherwise, if the answer is positive, the former admin is notified.

        Args:
            update (telegram.Update): update received after the leader is asked whether the former admin should be
                notified about losing the admin abilities.
        """
        query = update.callback_query

        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by giving the answer
            return  # no response

        if not self.is_familiar:  # if the leader is removing an admin for the first time
            self.update_familiarity(self.chat_id, self.familiarity, distrust='1')

        if answer == 'y':  # if the answer is positive
            bot.send_message(self.admin_id, t.YOU_NO_MORE_ADMIN[self.admin_language])
            l.cl.info(l.FORMER_NOTIFIED.format(self.admin_id))
            query.message.edit_text(t.FORMER_ADMIN_NOTIFIED[self.language])
        else:  # if the answer is negative
            query.message.edit_text(t.FORMER_NOT_NOTIFIED[self.language])

        self.terminate()


def displaying_events(record: a.ChatRecord, update: Update):
    """
    This function makes the bot send a message, a reply in non-private chats, containing upcoming events of the user's
    group.

    Args: see src.manager.deleting_data.__doc__.
    """
    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(  # the group's upcoming events
        'SELECT events FROM groups WHERE id = ?',
        (record.group_id,)
    )
    events = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    try:
        events = tuple(f'{t.WEEKDAYS[int(event[0])][record.language]} {event[2:]}' for event in events.split('\n'))
    except AttributeError:  # if there are no upcoming events
        events = t.NO_EVENTS[record.language]
    else:
        events = '\n'.join(events)

    update.effective_message.reply_text(events, quote=update.effective_chat.type != Chat.PRIVATE)
    l.cl.info(l.EVENTS.format(record.id))


def displaying_info(record: a.ChatRecord, update: Update):
    """
    This function makes the bot send a message, a reply in non-private chats, containing information that the user's
    group has saved.

    Args: see src.manager.deleting_data.__doc__.
    """
    connection = connect(c.DATABASE)
    cursor = connection.cursor()
    cursor.execute(  # the group's saved information
        'SELECT info FROM groups WHERE id = ?',
        (record.group_id,)
    )
    info = cursor.fetchone()[0] or t.NO_INFO[record.language]
    cursor.close()
    connection.close()

    update.effective_message.reply_text(info, quote=update.effective_chat.type != Chat.PRIVATE)
    l.cl.info(l.INFO.format(record.id))


class AddingEvent(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'new', t.UNAVAILABLE_ADDING_EVENT, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ADDING_EVENT, t.ALREADY_ADDING_EVENT

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)
        self.event: str = None
        self.cut_event: str = None
        self.date: datetime = None
        self.weekday_index: int = None
        self.date_str: str = None
        self.time_str = ''
        self.num_to_answer = 0

        self.send_message((t.ASK_NEW_EVENT if self.is_familiar else t.FT_ASK_NEW_EVENT)[self.language])
        self.next_action = self.handle_event

    def handle_event(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked the new event. It checks whether
        the given string is valid (contains no linebreaks). If it is, the admin is asked the event's date. Otherwise,
        the bot sends a message explaining why the given event string is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked the new event.
        """
        event = update.effective_message.text

        if '\n' not in event:
            self.event = event

            self.send_message((t.ASK_DATE if self.is_familiar else t.FT_ASK_DATE)[self.language])
            self.next_action = self.handle_date

        else:
            self.send_message(t.INVALID_EVENT[self.language])

    def handle_date(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked the new event's date. It checks
        whether the given date is valid and finishes the first part of the interaction (collecting information
        and saving the event) if it is. Otherwise, the bot sends a message explaining why the given date is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked the new event's date.
        """
        if not (text := self.inspect_date(update.effective_message.text)):  # if the given date is valid
            if not self.is_familiar:  # if the admin is adding an event for the first time
                self.update_familiarity(self.chat_id, self.familiarity, new='1')

            self.save_event()
            self.ONGOING_MESSAGE = self.ALREADY_MESSAGE = t.ONGOING_ANSWERING_TO_NOTIFY
            self.notify()
            self.next_action = self.handle_answer

        else:  # if the given date is invalid
            self.send_message(text)

    def inspect_date(self, date: str) -> Union[None, str]:
        """
        This method looks for a possible reason why the given date is invalid. It involves using src.config.DATE_PATTERN
        regular expression to check the format, and checks the given values for month and day of the month (and for hour
        and minute if time is also given). February's non-constant length is considered. The given date is always
        considered as the next time it comes, not of the current year.

        Args:
            date (str): the given date.

        Returns (None or str): None if the date is valid. Otherwise, text describing why the given date is invalid.
        """
        dates = findall(c.DATE_PATTERN, date)

        if (num_dates := len(dates)) == 1:
            day_str, month_str, time, hour_str, minute_str = dates[0]
            day, month = int(day_str), int(month_str)

            if month <= 12:

                if month >= 1:
                    now = datetime.now()
                    next_february_year = now.year + 1 if now.month > 2 else now.year
                    next_february_length = 28 if next_february_year % 4 else 29

                    if day <= (31, next_february_length, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month - 1]:

                        if day >= 1:  # if the given date is valid

                            if time:  # if time is given
                                hour, minute = int(hour_str), int(minute_str)

                                if hour <= 23:

                                    if minute <= 59:  # if the given time is valid
                                        self.time_str = f', {hour:02}:{minute:02}'
                                    else:  # if the given minute is greater than 59
                                        return t.INVALID_MINUTE[self.language]

                                else:
                                    return t.INVALID_HOUR[self.language]

                            else:
                                hour, minute = 23, 59

                            date_this_year = datetime(now.year, month, day, hour, minute)
                            self.date = date_this_year if now < date_this_year \
                                else datetime(now.year + 1, month, day, hour, minute)
                            self.weekday_index = int(self.date.strftime('%u')) - 1  # 0 to 6 = Monday to Sunday
                            self.date_str = f'{self.weekday_index} {day:02}.{month:02}{self.time_str}'

                        else:  # if the given day is 0
                            return t.DAY_0[self.language]

                    else:
                        return t.DAY_OVER_MONTH_LENGTH[self.language]

                else:  # if the given month is 0
                    return t.MONTH_0[self.language]

            else:
                return t.MONTH_OVER_12[self.language].format(month)

        elif not num_dates:  # if no dates are given
            return t.INVALID_DATE[self.language]

        else:  # if multiple dates are given
            return t.MULTIPLE_DATES[self.language]

        return None

    def save_event(self):
        """
        This method is the first step of finishing the first part of the interaction. From the information provided
        about the event, a string representation of it is created and saved by updating record of the admin's group in
        the database. The new event is placed so that the upcoming events are sorted by their date (within a day, events
        with time go first).
        """
        self.event = f'{self.date_str} — {self.event}'
        self.cut_event = a.cut(self.event)

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's upcoming events
            'SELECT events FROM groups WHERE id = ?',
            (self.group_id,)
        )
        try:
            events = cursor.fetchone()[0].split('\n')
        except AttributeError:  # if the group has no upcoming events
            updated_events = f'{self.event}'
        else:
            num_events = len(events)
            for i in range(num_events):
                if self.date > a.str_to_datetime(events[num_events - i - 1]):  # if the new event is later
                    events.insert(num_events - i, self.event)
                    break
            else:  # if the new event is the earliest one
                events.insert(0, self.event)

            updated_events = '\n'.join(events)

        cursor.execute(  # updating the group's upcoming events
            'UPDATE groups SET events = ? WHERE id = ?',
            (updated_events, self.group_id)
        )

        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.ADDS.format(self.chat_id, self.cut_event))

    def notify(self):
        """
        This method is the second and the last step of finishing the first part of the interaction. It sends a
        notification about the new event to chats that are related to the admin's group. Each student is also asked
        whether they want the bot to send them reminders about the event.
        """
        # the event with the weekday in each language
        event = tuple(f'{t.WEEKDAYS[self.weekday_index][index]} {self.event[2:]}' for index in range(len(c.LANGUAGES)))

        answers = tuple(
            [[
                InlineKeyboardButton(t.YES[index], callback_data='y'),
                InlineKeyboardButton(t.NO[index], callback_data='n')
            ]]
            for index in range(len(c.LANGUAGES))
        )
        markup = tuple(InlineKeyboardMarkup(buttons) for buttons in answers)

        for chat_id, chat_type, language, familiarity in self.get_related_records():

            if not chat_type:  # if the record is of a private chat
                current[chat_id] = self  # the student is now answering whether they want to be notified about the event
                self.num_to_answer += 1

                msg = t.NEW_EVENT if int(a.Familiarity(*familiarity).answer_to_notify) else t.FT_NEW_EVENT
                text = msg[language].format(event[language], choice(t.ASK_TO_NOTIFY[language]))
                bot.send_message(chat_id, text, reply_markup=markup[language])

            else:  # if the record is of a non-private chat
                bot.send_message(chat_id, t.NEW_EVENT[language].format(event[language], ''))

    def get_related_records(self) -> list[tuple[int, int, int, str]]:
        """
        Returns (list[tuple[int, int, int, str]]): chats that are related to the admin's group. Namely, list of tuples
            containing the chat's telegram id, type, language, and familiarity with the bot's interactions as an
            argument for src.auxiliary.Familiarity.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # chats related to the group
            'SELECT id, type, language, familiarity FROM chats WHERE group_id = ?',
            (self.group_id,)
        )
        related_records: list[tuple[int, int, int, str]] = cursor.fetchall()

        cursor.close()
        connection.close()

        return related_records

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the student is asked whether they want the bot to
        send them reminders about the new event. If the update is not caused by giving the answer (by clicking on one of
        the two provided inline buttons), it is ignored. Otherwise, the bot responds considering the answer and whether
        the events has already passed.

        Args:
            update (telegram.Update): update received after the student is asked whether they want the bot to send them
                reminders about the new event.
        """
        query = update.callback_query

        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by giving the answer
            return  # no response

        chat_id = update.effective_chat.id
        record = a.get_chat_record(chat_id)
        familiarity = a.Familiarity(*record.familiarity)

        # if the user is answering for the first time whether they want to be notified about the event
        if not int(familiarity.answer_to_notify):
            Interaction.update_familiarity(chat_id, familiarity, answer_to_notify='1')

        if self.date > datetime.now():  # if the event has not already passed
            if answer == 'y':  # if the answer is positive
                self.add_student(chat_id)
                log_msg, msg = l.AGREES, t.EXPECT_NOTIFICATIONS
            else:  # if the answer is negative
                log_msg, msg = l.DISAGREES, t.EXPECT_NO_NOTIFICATIONS

        else:  # if the event has passed or has been canceled
            if answer == 'y':  # if the answer is positive
                log_msg, msg = l.AGREES_LATE, t.WOULD_EXPECT_NOTIFICATIONS
            else:  # if the answer is negative
                log_msg, msg = l.DISAGREES_LATE, t.WOULD_EXPECT_NO_NOTIFICATIONS

        l.cl.info(log_msg.format(chat_id, self.cut_event))
        event = query.message.text.rpartition('\n\n')[0]
        query.message.edit_text(f"{event}\n\n{msg[record.language]}")

        del current[chat_id]
        self.num_to_answer -= 1
        if not self.num_to_answer:  # if the student is the last one to answer
            l.cl.info(l.ALL_ANSWERED_TO_NOTIFY.format(self.group_id, self.cut_event))

    def add_student(self, user_id):
        pass  # todo


class CancelingEvent(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'cancel', t.UNAVAILABLE_CANCELING_EVENT, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CANCELING_EVENT, t.ALREADY_CANCELING_EVENT

    def __init__(self, record: a.ChatRecord, events: str):
        super().__init__(record)
        self.events = events.split('\n')

        self.ask_event()
        self.next_action = self.delete_event

    def ask_event(self):
        """
        This method makes the bot ask the admin which of the group's upcoming events to cancel. The options
        are provided as inline buttons.
        """
        events = [  # the group's upcoming events with their weekdays in the admin's language
            [InlineKeyboardButton(f'{t.WEEKDAYS[int(event[0])][self.language]} {event[2:]}', callback_data=str(index))]
            for index, event in enumerate(self.events)
        ]
        markup = InlineKeyboardMarkup(events)

        self.send_message((t.FT_ASK_EVENT if self.is_familiar else t.ASK_EVENT)[self.language], reply_markup=markup)

    def delete_event(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked which of the group's upcoming
        events to cancel. If the update is not caused by choosing one (by clicking on one of the provided inline
        buttons), it is ignored. Otherwise, the chosen event is deleted by updating the group's record in the database,
        and the admin's groupmates are notified about this. It is necessary to get the group's upcoming events from the
        database again in order not to lose events that may have been added by the admin's groupmates during the
        interaction.

        Args:
            update (telegram.Update): update received after the admin is asked which of the group's upcoming events to
                cancel.
        """
        query = update.callback_query

        try:
            event = self.events[int(query.data)]
        except AttributeError:  # if the update is not caused by choosing an event
            return  # no response

        if not self.is_familiar:  # if the admin is canceling an upcoming event for the first time
            self.update_familiarity(self.chat_id, self.familiarity, cancel='1')

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's upcoming events
            'SELECT events FROM groups WHERE id = ?',
            (self.group_id,)
        )
        try:
            events = cursor.fetchone()[0].split('\n')
        except AttributeError:  # if there are no upcoming events
            updated_events = ''
        else:  # if there are upcoming events
            try:
                events.remove(event)
            except ValueError:  # if the event has already been canceled by one of the admin's groupmates
                pass
            updated_events = '\n'.join(events)

        if updated_events:  # if there are upcoming events besides the canceled one
            cursor.execute(  # updating the group's saved info
                'UPDATE groups SET events = ? WHERE id = ?',
                (updated_events, self.group_id)
            )
        else:  # if the canceled event is the only upcoming event or there are none
            cursor.execute(  # clearing the group's upcoming events
                'UPDATE groups SET events = NULL WHERE id = ?',
                (self.group_id,)
            )

        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.CANCELS.format(self.chat_id, a.cut(event)))

        # the event with its weekday in each language
        event = tuple(f'{t.WEEKDAYS[int(event[0])][index]} {event[2:]}' for index in range(len(c.LANGUAGES)))

        query.message.edit_text(t.EVENT_CANCELED[self.language].format(event[self.language]))
        self.notify(event)
        self.terminate()

    def notify(self, event: tuple[str]):
        """
        This method is the last step of canceling an event, which the interaction is terminates after. It sends a
        notification to chats that are related to the admin's group, letting them know that the event has been canceled.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # chats related to the group w/o the admin
            'SELECT id, language FROM chats '
            'WHERE group_id = ? AND id <> ?',
            (self.group_id, self.chat_id)
        )
        student_records: list[tuple[int, int]] = cursor.fetchall()

        cursor.close()
        connection.close()

        for user_id, language in student_records:
            bot.send_message(user_id, t.EVENT_CANCELED[language].format(event[language]))


class SavingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'save', t.UNAVAILABLE_SAVING_INFO, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_SAVING_INFO, t.ALREADY_SAVING_INFO

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)
        self.info: str = None

        self.send_message((t.ASK_NEW_INFO if self.is_familiar else t.FT_ASK_NEW_INFO)[self.language])
        self.next_action = self.handle_info

    def handle_info(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked a piece of information to save.
        It checks whether the given information is valid (contains no empty lines) and saves it if it is. Otherwise, the
        bot sends a message explaining why the given information is invalid.

        Args:
            update (telegram.Update): update received after the admin is asked a piece of information to save.
        """
        if '\n\n' not in (info := update.effective_message.text):
            if not self.is_familiar:  # if the admin is saving info for the first time
                self.update_familiarity(self.chat_id, self.familiarity, save='1')

            self.save_info(info)
            self.notify(info)
            self.terminate()

        else:
            self.send_message(t.INVALID_INFO[self.language])

    def save_info(self, new_info: str):
        """
        This method saves the given information by updating record of the admin's group in the database.

        Args:
            new_info (str): the given information.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's saved info
            'SELECT info FROM groups WHERE id = ?',
            (self.group_id,)
        )
        try:
            info = cursor.fetchone()[0] + f'\n\n{new_info}'
        except TypeError:
            info = new_info

        cursor.execute(  # updating the group's saved info
            'UPDATE groups SET info = ? WHERE id = ?',
            (info, self.group_id)
        )

        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.SAVES.format(self.chat_id, a.cut(info)))

    def notify(self, info: str):
        """
        This method is the last step of saving information, which the interaction is terminates after. It sends a
        notification about the new information to chats that are related to the admin's group.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # chats related to the group
            'SELECT id, language FROM chats WHERE group_id = ?',
            (self.group_id,)
        )
        student_records: list[tuple[int, int]] = cursor.fetchall()

        cursor.close()
        connection.close()

        for user_id, language in student_records:
            bot.send_message(user_id, t.NEW_INFO[language].format(info))


class DeletingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'delete', t.UNAVAILABLE_DELETING_INFO, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_DELETING_INFO, t.ALREADY_DELETING_INFO

    def __init__(self, record: a.ChatRecord, info: str):
        super().__init__(record)
        self.info = info.split('\n\n')

        self.ask_info()
        self.next_action = self.delete_info

    def ask_info(self):
        """
        This method makes the bot ask the admin which piece of their group's saved information to delete. The options
        are provided as inline buttons.
        """
        info = [  # using indices because info can be longer than 64, which is the limit for a callback_data value
            [InlineKeyboardButton(info_piece, callback_data=str(index))] for index, info_piece in enumerate(self.info)
        ]
        markup = InlineKeyboardMarkup(info)

        self.send_message((t.ASK_INFO if self.is_familiar else t.FT_ASK_INFO)[self.language], reply_markup=markup)

    def delete_info(self, update: Update):
        """
        This method is the last step of deleting some the group's saved information, which the interaction is terminated
        after. It is called when the bot receives an update after the admin is asked which piece of their group's saved
        information to delete. If the update is not caused by choosing one (by clicking on one of the provided inline
        buttons), it is ignored. Otherwise, the chosen piece of information is deleted by updating the group's record in
        the database. It is necessary to get the group's saved information from the database again in order not to lose
        information that may have been saved by the admin's groupmates during the interaction.

        Args:
            update (telegram.Update): update received after the admin is asked which piece of their group's saved
                information to delete.
        """
        query = update.callback_query

        try:
            info_piece = self.info[int(query.data)]
        except AttributeError:  # if the update is not caused by choosing an info piece
            return  # no response

        if not self.is_familiar:  # if the admin is deleting a piece of the group's saved info for the first time
            self.update_familiarity(self.chat_id, self.familiarity, delete='1')

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's saved info
            'SELECT info FROM groups WHERE id = ?',
            (self.group_id,)
        )
        try:
            info = cursor.fetchone()[0].split('\n\n')
        except AttributeError:  # if the saved info is empty
            updated_info = ''
        else:  # if the saved info is not empty
            try:
                info.remove(info_piece)
            except ValueError:  # if the info piece has already been deleted by one of the admin's groupmates
                pass
            updated_info = '\n\n'.join(info)

        if updated_info:  # if there is saved info besides the deleted info piece
            cursor.execute(
                'UPDATE groups SET info = ? WHERE id = ?',
                (updated_info, self.group_id)
            )
        else:  # if the deleted info piece is the only saved info
            cursor.execute(  # clearing the group's saved info
                'UPDATE groups SET info = NULL WHERE id = ?',
                (self.group_id,)
            )

        connection.commit()
        cursor.close()
        connection.close()
        cut_info = a.cut(info_piece)
        l.cl.info(l.DELETES.format(self.chat_id, cut_info))

        query.message.edit_text(t.INFO_DELETED[self.language].format(cut_info))
        self.terminate()


class ClearingInfo(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'clear', t.UNAVAILABLE_CLEARING_INFO, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CLEARING_INFO, t.ALREADY_CLEARING_INFO

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)

        self.ask_polar((t.ASK_CLEARING_INFO if self.is_familiar else t.FT_ASK_CLEARING_INFO)[self.language])
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the admin is asked whether they are sure to clear
        their group's saved information. If the update is not caused by giving the answer (by clicking on one of the two
        provided inline buttons), it is ignored. Otherwise, the group's saved information is cleared.

        Args:
            update (telegram.Update): update received after the admin is asked whether they are sure to clear their
                group's saved information.
        """
        query = update.callback_query
        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by choosing the answer
            return  # no response

        if not self.is_familiar:  # if the admin is clearing the saved info for the first time
            self.update_familiarity(self.chat_id, self.familiarity, clear='1')

        if answer == 'y':  # if the answer is positive
            self.clear_info()
            query.message.edit_text(t.INFO_CLEARED[self.language])
        else:  # if the answer is negative
            l.cl.info(l.KEEPS.format(self.chat_id))
            query.message.edit_text(t.INFO_KEPT[self.language])

        self.terminate()

    def clear_info(self):
        """
        This method deletes all saved information of the admin's group by updating its record in the database.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # clearing the group's saved info
            'UPDATE groups SET info = NULL WHERE id = ?',
            (self.group_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.CLEARS.format(self.chat_id))


class NotifyingGroup(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'tell', t.UNAVAILABLE_NOTIFYING_GROUP, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_NOTIFYING_GROUP, t.ALREADY_NOTIFYING_GROUP

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)
        self.username = record.username

        self.send_message((t.ASK_MESSAGE if self.is_familiar else t.FT_ASK_MESSAGE)[self.language])
        self.next_action = self.notify

    def notify(self, update: Update):
        """
        This method is the last step of notifying the group, which the interaction is terminated after. It is called
        when the bot receives an update after the leader is asked a message to notify their group with. The provided
        message is forwarded to chats that are related to the group.

        Args:
            update (telegram.Update): update received after the leader is asked a message to notify their group with.
        """
        if not self.is_familiar:  # if the leader is notifying their group for the first time
            self.update_familiarity(self.chat_id, self.familiarity, tell='1')

        related_records = self.get_related_records()
        message = update.effective_message

        for chat_id, language in related_records:
            bot.send_message(chat_id, t.GROUP_NOTIFICATION[language].format(self.username))
            message.forward(chat_id)

        l.cl.info(l.NOTIFIES.format(self.chat_id, a.cut(message.text)))
        self.send_message(t.GROUP_NOTIFIED[self.language].format(len(related_records)))
        self.terminate()

    def get_related_records(self) -> list[tuple[int, int]]:
        """
        Returns (list[tuple[int, int]]): chats that are related to the admin's group. Namely, list of tuples containing
            the chat's id and language.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(
            'SELECT id, language FROM chats '
            'WHERE group_id = ? AND id <> ?',
            (self.group_id, self.chat_id)
        )
        related_records: list[tuple[int, int]] = cursor.fetchall()

        cursor.close()
        connection.close()

        return related_records


class AskingGroup(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'ask', t.UNAVAILABLE_ASKING_GROUP, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_ASKING_GROUP, t.ALREADY_ASKING_GROUP

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)
        self.username = record.username
        self.question_message_id: id = None
        self.cut_question: str = None
        self.group_chat: tuple[int, int] = None
        self.is_public: bool = None

        self.leader_answer_message_id: int = None
        self.group_answer_message_id: int = None

        stop = [[InlineKeyboardButton(t.STOP_ASKING_GROUP[self.language], callback_data='terminate')]]
        self.stop_markup = InlineKeyboardMarkup(stop)

        self.asked: dict[int, tuple[str, int, a.Familiarity, int]] = None
        self.answered, self.refused = list[tuple[str, str]](), list[str]()

        self.send_message((t.ASK_QUESTION if self.is_familiar else t.FT_ASK_QUESTION)[self.language])
        self.next_action = self.handle_question

    def handle_question(self, update: Update):
        """
        This method is called when the bot receives an update after the leader is asked a question to ask their group.
        It saves id of the given question's message and checks whether the group has registered their group chat. If it
        has, the leader is asked whether the future answers should be sent to the group chat, i. e., whether the
        interaction is public. Otherwise, the second part of the interaction (sending the question and displaying the
        answers) is launched.

        Args:
            update (telegram.Update): update received after the leader is asked a question to ask their group.
        """
        message = update.effective_message
        self.question_message_id = message.message_id
        self.cut_question = a.cut(message.text)

        self.group_chat = self.get_group_chat_record()

        text = (t.ASK_TO_PUBLISH if self.is_familiar else t.FT_ASK_TO_PUBLISH)[self.language]
        self.leader_answer_message_id = self.ask_polar(text).message_id
        self.next_action = self.handle_answer

    def get_group_chat_record(self) -> Union[tuple[int, int], None]:
        """
        Returns (tuple[int, int] or None): record of the group chat of the leader's group. None if the group has not
            registered one.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # group chat of the leader's group
            'SELECT id, language FROM chats '
            'WHERE group_id = ? AND type <> 0',
            (self.group_id,)
        )
        group_chat_record = cursor.fetchone()
        cursor.close()
        connection.close()

        return group_chat_record

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the leader is asked whether the interaction is
        public. If the update is not caused by giving the answer (by clicking on one of the two provided inline
        buttons), it is ignored. Otherwise, the given answer is saved and the second part of the interaction (sending
        the question and displaying the answers) is launched.

        Args:
            update (telegram.Update): update received after the leader is asked whether the interaction is public.
        """
        try:
            self.is_public = update.callback_query.data == 'y'
        except AttributeError:  # if the update is not caused by giving the answer
            return  # no response

        l.cl.info((l.MAKES_PUBLIC if self.is_public else l.MAKES_NON_PUBLIC).format(self.chat_id))
        self.launch()

    def launch(self):
        """
        This method launches the second part of the interaction, which consists of receiving the students' answers.
        It makes the bot send a message to the leader, that contains information about the answers, refusals and
        students who have yet to respond. It also makes the bot send the question to the leader's groupmates. If the
        interaction is public, the answer message is also sent to the group's group chat, and the leader is also asked
        the question.
        """
        self.ONGOING_MESSAGE = t.ONGOING_ANSWERING
        if not self.is_familiar:  # if the leader is asking their group for the first time
            self.update_familiarity(self.chat_id, self.familiarity, ask='1')

        self.asked = self.get_asked()
        usernames = self.send_answer_list()
        markup = self.send_question()

        if self.is_public:
            asked = t.ASKED[self.group_chat[1]].format(usernames)
            text = t.ANSWER_LIST.format(self.cut_question, '', '', asked)
            self.group_answer_message_id = bot.send_message(self.group_chat[0], text).message_id

            text = t.ASK_LEADER_ANSWER[self.language]
            message_id = self.send_message(text, reply_markup=markup[self.language]).message_id
            self.asked[self.chat_id] = [self.username, self.language, self.familiarity, message_id]

        else:
            del current[self.chat_id]

        current[self.group_id] = self
        self.next_action = self.handle_response

    def get_asked(self) -> dict[int, list[str, int, a.Familiarity]]:
        """
        Returns (dict[int, list[str, int, a.Familiarity]]): the leader's groupmates. Namely, dict with items with the
            student's id as the key and a list containing their username, language, and familiarity with the bot's
            interactions, as the value.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()
        cursor.execute(  # the leader's groupmates
            'SELECT id, username, language, familiarity FROM chats '
            'WHERE group_id = ? AND type = 0 AND id <> ?',
            (self.group_id, self.chat_id)
        )
        asked_records: list[tuple[int, str, int, str]] = cursor.fetchall()
        cursor.close()
        connection.close()

        return {
            user_id: [username, language, a.Familiarity(*familiarity)]
            for user_id, username, language, familiarity in asked_records
        }

    def send_answer_list(self) -> str:
        """
        This method makes the bot send a message to the leader, that contains information about the students' answers to
        the question, which students refused to answer and which have yet to respond (initially, all of the students
        are yet to have responded). Id of the sent message is saved so that its text can be changed later.

        Returns (str): usernames of the students who the question will be sent to, each on a separate line.
        """
        usernames = [r[0] for r in self.asked.values()]
        if self.is_public:
            usernames.append(self.username)
        usernames.sort(key=a.string_sort_key)
        usernames = '\n'.join(usernames)

        asked = t.ASKED[self.language].format(usernames)
        text = t.ANSWER_LIST.format(self.cut_question, '', '', asked)

        try:
            bot.edit_message_text(text, self.chat_id, self.leader_answer_message_id, reply_markup=self.stop_markup)
        except BadRequest:
            self.leader_answer_message_id = self.send_message(text, reply_markup=self.stop_markup).message_id

        return usernames

    def send_question(self) -> tuple[InlineKeyboardMarkup]:
        """
        This method makes the bot send the question. Namely, to forward the message that the leader sent the question
        in. An option to refuse to answer by clicking an inline button is also provided.

        Returns(tuple[telegram.InlineKeyboardMarkup]): inline markups with a refuse inline button in each language.
        """
        refuse = tuple(  # refuse inline button in each language
            [[InlineKeyboardButton(t.REFUSE_TO_ANSWER[index], callback_data='refuse')]]
            for index in range(len(c.LANGUAGES))
        )
        markup = tuple(InlineKeyboardMarkup(button) for button in refuse)

        for user_id, (username, language, familiarity) in self.asked.items():
            current[user_id] = self
            bot.forward_message(user_id, self.chat_id, self.question_message_id)
            text = (t.ASK_ANSWER if int(familiarity.answer) else t.FT_ASK_ANSWER)[language]
            info = (t.PUBLIC_ANSWER if self.is_public else t.PRIVATE_ANSWER)[language].format(self.username)
            message_id = bot.send_message(user_id, text.format(info), reply_markup=markup[language]).message_id
            self.asked[user_id] = (username, language, familiarity, message_id)

        l.cl.info(l.ASKED.format(self.group_id, self.cut_question))
        return markup

    def handle_response(self, update: Update):
        """
        This method is called when the bot receives an update after the student has been sent the question. If the
        update is caused by sending a text message, it is considered an answer, and a refusal to answer otherwise. In
        both cases, the response is considered and the answer message(s) is (are) updated. This method is also called
        when the leader terminates the interaction.

        Args:
            update (telegram.Update): update received after the student has been sent the question.
        """
        # if the leader has terminated the interaction
        if (query := update.callback_query) and query.data == 'terminate':
            self.terminate()
            return

        chat, message, query = update.effective_chat, update.effective_message, update.callback_query
        username, language, familiarity, message_id = self.asked[chat.id]

        # if the user is not the leader and is answering for the first time
        if familiarity and not int(familiarity.answer):
            self.update_familiarity(chat.id, familiarity, answer='1')

        if not query:  # if an answer is given
            answer = message.text.replace('\n\n', '\n')
            self.answered.append((username, answer))
            log_text, msg = l.ANSWERS.format(chat.id, a.cut(answer)), t.ANSWER_SENT
        else:  # if the student has refused to answer
            self.refused.append(username)
            log_text, msg = l.REFUSES.format(chat.id), t.REFUSAL_SENT

        l.cl.info(log_text)
        bot.edit_message_text(msg[language], chat.id, message_id)
        del self.asked[chat.id]

        usernames_answered = '\n\n'.join([f'{username}\n{answer}' for username, answer in self.answered])
        usernames_refused = '\n'.join(self.refused)
        usernames_asked = '\n'.join(tuple(r[0] for r in self.asked.values()))

        self.update_answers(self.chat_id, self.language, self.leader_answer_message_id,
                            (usernames_answered, usernames_refused, usernames_asked))
        if self.is_public:
            self.update_answers(*self.group_chat, self.group_answer_message_id,
                                (usernames_answered, usernames_refused, usernames_asked))

        if not self.asked:  # if all of the students have answered
            bot.edit_message_reply_markup(self.chat_id, self.leader_answer_message_id)
            self.send_message(t.ALL_ANSWERED[self.language].format(self.cut_question))
            if self.is_public:
                text = t.ALL_ANSWERED[self.group_chat[1]].format(self.cut_question)
                bot.send_message(self.group_chat[0], text)

            del current[self.group_id]
            l.cl.info(l.ALL_ANSWERED.format(self.group_id))

        del current[chat.id]

    def update_answers(self, chat_id: int, language: int, answer_message_id: int, usernames: tuple[str]):
        """
        This method updates the answer message by making the bot edit its texts.

        Args:
            chat_id (int): id of the chat that the answer message is in.
            language (int): language of the chat that the answer message is in, according to src.text.LANGUAGES.
            answer_message_id (int): if of the answer message.
            usernames(tuple[str]): new text for the message, based on the current information about the students'
                responses (answers, refusals, absence of a response).
        """
        answered = t.ANSWERED[language].format(usernames[0]) if usernames[0] else ''
        refused = t.REFUSED[language].format(usernames[1]) if usernames[1] else ''
        asked = t.ASKED[language].format(usernames[2]) if usernames[2] else ''

        text = t.ANSWER_LIST.format(self.cut_question, answered, refused, asked)
        markup = self.stop_markup if chat_id == self.chat_id else None
        bot.edit_message_text(text, chat_id, answer_message_id, reply_markup=markup)

    def respond(self, command: str, message: Message):
        if not self.asked:  # if the second part of the interaction has not been launched
            super().respond(command, message)
        else:  # if the second part of the interaction has been launched
            text = self.ONGOING_MESSAGE[self.asked[message.from_user.id][1]]
            message.reply_text(text, quote=message.chat.type != Chat.PRIVATE)
            l.cl.info(l.INTERRUPTS.format(message.from_user.id, command, type(self).__name__))

    def terminate(self):
        """
        This method terminates the interaction. It deletes the refuse buttons of students who have yet to respond and
        sends them a message explaining that the answer is no longer expected. The the leader's terminating button is
        also deleted.
        """
        bot.edit_message_reply_markup(self.chat_id, self.leader_answer_message_id)  # deleting the terminating button
        if self.chat_id in self.asked:  # if the interaction is public and the leader has yet to respond
            bot.edit_message_reply_markup(self.chat_id, self.asked[self.chat_id][3])  # removing the refuse button
            del self.asked[self.chat_id]  # the leader is no longer expected to respond
            del current[self.chat_id]  # the leader is no longer having the interaction

        for user_id, (_, language, _, message_id) in self.asked.items():
            bot.edit_message_reply_markup(user_id, message_id)  # removing the refuse button
            bot.send_message(user_id, t.GROUP_ASKING_TERMINATED[1][language])
            del current[user_id]  # the student is no longer having the interaction

        del current[self.group_id]  # the group is no longer having the interaction
        l.cl.info(l.TERMINATES.format(self.chat_id))
        self.send_message(t.GROUP_ASKING_TERMINATED[0][self.language])


class ChangingLeader(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'resign', t.UNAVAILABLE_CHANGING_LEADER, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_CHANGING_LEADER, t.ALREADY_CHANGING_LEADER

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)
        self.to_admin = True  # whether the authorities will be given to an admin

        self.ask_polar((t.FT_ASK_RESIGN if not self.is_familiar else t.ASK_RESIGN)[self.language])
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        query = update.callback_query

        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by giving the answer
            return  # no response

        if not self.is_familiar:  # if the user is using /resign for the first time
            self.update_familiarity(self.chat_id, self.familiarity, resign='1')

        if answer == 'y':  # if the answer is positive
            self.ask_new_leader()
            self.next_action = self.change_leader
        else:  # if the answer is negative
            query.message.edit_text(t.AUTHORITIES_KEPT[self.language])
            self.terminate()

    def ask_new_leader(self):
        """
        This method makes the bot ask the leader which of their groupmates their authorities will be given to. The
        options are the group's admins (or ordinary students) and are provided as inline buttons.
        """
        candidates = [
            [InlineKeyboardButton(username, callback_data=f'{user_id} {username} {language}')]
            for user_id, username, language in self.get_candidate_records()
        ]
        markup = InlineKeyboardMarkup(candidates)

        self.send_message(t.ASK_NEW_LEADER[self.language], reply_markup=markup)

    def get_candidate_records(self) -> list[tuple[int, str, int]]:
        """
        This method determines the leader's groupmates to let them choose the new leader from. The candidates are the
        group's admins if they are there, and the group's ordinary students otherwise.

        Returns (list[tuple[int, str, int]]): candidates for being the new leader, sorted by their usernames or other
            identifiers. Namely, list of tuples containing the candidate's telegram id, username or other identifier,
            and language.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        cursor.execute(  # the group's admins
            'SELECT id, username, language FROM chats '
            'WHERE group_id = ? AND role = 1',
            (self.group_id,)
        )
        candidate_records: list[tuple[int, str, int]] = cursor.fetchall()

        if not candidate_records:  # if the are no admins in the group
            cursor.execute(  # the leader's groupmates
                'SELECT id, username, language FROM chats '
                'WHERE group_id = ? AND role = 0 AND type = 0',
                (self.group_id,)
            )
            candidate_records: list[tuple[int, str, int]] = cursor.fetchall()
            self.to_admin = False  # the authorities will be given to an ordinary student

        cursor.close()
        connection.close()

        candidate_records.sort(key=lambda r: a.string_sort_key(r[1]))
        return candidate_records

    def change_leader(self, update: Update):
        """
        This method is the last step of changing the group's leader, which the interaction is terminated after. It is
        called when the bot receives an update after the leader is asked which of their group's students their
        authorities will be given to. If the update is not caused by choosing one (by clicking on one of the provided
        inline buttons), it is ignored. Otherwise, the chosen student is made the group's leader and the leader is made
        an admin, by updating their records in the database. The new leader is also notified about the new abilities.

        Args:
            update (telegram.Update): update received after the leader is asked which of their group's students their
                authorities will be given to
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
        cursor.execute(  # making the chosen groupmate the group's leader
            'UPDATE chats SET role = 2 WHERE id = ?',
            (new_leader_id,)
        )
        cursor.execute(  # making the leader an admin
            'UPDATE chats SET role = 1 WHERE id = ?',
            (self.chat_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.NOW_LEADER.format(new_leader_id))

        new_commands = '' if self.to_admin else t.ADMIN_COMMANDS[new_leader_language]
        new_commands += t.LEADER_COMMANDS[new_leader_language]
        bot.send_message(new_leader_id, t.YOU_NOW_LEADER[new_leader_language].format(new_commands))
        query.message.edit_text(t.NOW_LEADER[self.language].format(new_leader_username))
        self.terminate()


class SendingFeedback(Interaction):
    COMMAND, UNAVAILABLE_MESSAGE, IS_PRIVATE = 'feedback', None, True
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_SENDING_FEEDBACK, t.ALREADY_SENDING_FEEDBACK

    def __init__(self, record: a.ChatRecord):
        super().__init__(record)

        self.send_message((t.FT_ASK_FEEDBACK if not self.is_familiar else t.ASK_FEEDBACK)[self.language])
        self.next_action = self.save_feedback

    def save_feedback(self, update: Update):
        """
        This method is called when the bot receives an update after the user is asked a feedback message. It saves the
        message by updating the user's record in the database.

        Args:
            update: (telegram.Update): update received after the user is asked a feedback message.
        """
        now, new_feedback = datetime.now().strftime(l.TIME_FORMAT), update.effective_message.text

        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if not self.is_familiar:  # if the user is sending feedback for the first time
            self.update_familiarity(self.chat_id, self.familiarity, feedback='1')
            updated_feedback = f'{now}\n{new_feedback}'
        else:  # if the user is sending feedback not for the first time
            cursor.execute(
                'SELECT feedback FROM chats WHERE id = ?',
                (self.chat_id,)
            )
            updated_feedback = cursor.fetchone()[0] + f'\n\n{now}\n{new_feedback}'

        cursor.execute(
            'UPDATE chats SET feedback = ? WHERE id = ?',
            (updated_feedback, self.chat_id)
        )
        connection.commit()
        cursor.close()
        connection.close
        l.cl.info(l.SENDS_FEEDBACK.format(self.chat_id, a.cut(new_feedback)))

        self.send_message(t.FEEDBACK_SENT[self.language])
        self.terminate()


class DeletingData(Interaction):
    COMMAND, IS_PRIVATE = 'leave', False
    ONGOING_MESSAGE, ALREADY_MESSAGE = t.ONGOING_DELETING_DATA, t.ALREADY_DELETING_DATA

    def __init__(self, record: a.ChatRecord, is_last: bool):
        super().__init__(record)
        self.is_last = is_last

        self.ask_polar((t.FT_ASK_LEAVE if not self.is_familiar else t.ASK_LEAVE)[self.language])
        self.next_action = self.handle_answer

    def handle_answer(self, update: Update):
        """
        This method is called when the bot receives an update after the user is asked whether they are sure to delete
        their data. If the update is not caused by giving the answer (by clicking on one of the two provided inline
        buttons), it is ignored. Otherwise, if the answer is positive, the user's record in the database is deleted.

        Args:
            update (telegram.Update): update received after the user is asked whether they are sure to delete their
                data.
        """
        query = update.callback_query
        try:
            answer = query.data
        except AttributeError:  # if the update is not caused by choosing the answer
            return  # no response

        if not self.is_familiar:  # if the user is using /leave for the first time
            self.update_familiarity(self.chat_id, self.familiarity, leave='1')

        if answer == 'y':  # if the answer is positive
            self.delete_record()
            query.message.edit_text(t.DATA_DELETED[self.language])
        else:  # if the answer is negative
            l.cl.info(l.STAYS.format(self.chat_id))
            query.message.edit_text(t.DATA_KEPT[self.language])

        self.terminate()

    def delete_record(self):
        """
        This method is the last step of deleting the user's data, which the interaction is terminated after. It deletes
        the user's record in the database. If the user is the last registered student from their group, its record and
        records of the group's group chats are also deleted.
        """
        connection = connect(c.DATABASE)
        cursor = connection.cursor()

        if not self.is_last:  # if the chat is not the last registered one from the group
            cursor.execute(  # deleting the user's record
                'DELETE FROM chats WHERE id = ?',
                (self.chat_id,)
            )
        else:  # if the user is the last registered student from the group
            cursor.execute(  # deleting the user's record and records of the group's group chats
                'DELETE FROM chats WHERE group_id = ?',
                (self.group_id,)
            )
            cursor.execute(  # deleting the group's record
                'DELETE FROM groups WHERE id = ?',
                (self.group_id,)
            )

        connection.commit()
        cursor.close()
        connection.close()
        l.cl.info(l.LEAVES.format(self.chat_id, self.group_id))
        if self.is_last:
            l.cl.info(l.LEAVES.format(self.group_id))
        else:
            a.update_group_chat_language(self.group_id)

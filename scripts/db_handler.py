from datetime import datetime
import mysql.connector
import os
from termcolor import colored


class DbHandler:
    def __init__(self):
        """
        Initializes
        """
        print('connecting to db ... ', end='')

        self.connect = mysql.connector.connect(
            host='vps721220.ovh.net',
            user='instagram_worker_user',
            passwd=os.environ['INSTAGRAM_UNFOLLOWERS_BOT_DB_PASSWD'],
            port=3306,
            database='instagram_unfollowers',
            auth_plugin='mysql_native_password'
        )
        self.curs = self.connect.cursor(buffered=True)
        self.session_created = datetime.now()
        print(colored('DONE', 'green'))

    def check_db_session_time(func):
        """
        Decorator created to track length of db session time alive,
            and recreate db connection
        :param func: function needed to wrap
        :return: inner function which wraps function
        """
        def inner_function(self, *args):
            """
            Inner function of decorator.
            Wraps needed function, and check time when session were created.
            if time if bigger than 4.9 hrs, recreates db session.
            :param args: arguments passed to wrapping function
            :return:
            """
            now = datetime.now()
            hours = (now - self.session_created).seconds / 3600     # used it, cuz it could b more than 0 days
                                                                    # from session creating date

            if hours >= 4.9:
                self.__init__()
            if len(args) == 0:
                return func(self)
            else:
                return func(self, *args)
        return inner_function

    @check_db_session_time
    def add_account_to_whitelist(self, client_id, client_telegram_id, account_id):
        """
        Adds record to whitelist, with client ids and id of following account
        :param client_id:client instagram id
        :param client_telegram_id: client telegram id
        :param account_id: following account instagram id
        :return: None
        """
        q = f'insert into whitelist (user_telegram_id, user_instagram_id, following_acc_instagram_id) values ' \
            f'({client_telegram_id}, {client_id}, {account_id})'
        try:
            self.curs.execute(q)
            self.connect.commit()
        except mysql.connector.errors.IntegrityError as err:
            pass    # do nothing, because after user clicked,
                    # menu should refresh, so it's most likely
                    # client clicked twice too fast

    @check_db_session_time
    def get_whitelist_for_instagram_id(self, instagram_id):
        """
        Returns list of instagram ids, which user added to whitelist for specified account
        :param instagram_id: instagram account id
        :return: list with account ids, 'whitelist'
        """
        q = f'select following_acc_instagram_id from whitelist where user_instagram_id={instagram_id};'

        self.curs.execute(q)
        return self.curs.fetchall()
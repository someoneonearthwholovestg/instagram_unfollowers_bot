import config
import datetime
from math import floor
from model import Model
import telebot
from telebot import types
from termcolor import colored
import _thread

bot = telebot.TeleBot(config.TOKEN)
model = None

def init():
    """
    Initial method for bot start
    :return: None
    """
    try:
        global model
        model = Model()
        print('starting bot ... ', end='')
        print(colored('DONE', 'green'))
        bot.polling(none_stop=True)
    except Exception as err:
        print(err)


@bot.message_handler(commands=['start'])
def start_handler(message):
    """
    Handles user's 'start' command, and requests instagram username
    :param message: message instance
    :return: None
    """
    bot.send_message(chat_id=message.chat.id, text='hey, glad to see you here!')
    bot.send_message(chat_id=message.chat.id, text=f'you can check people who doesn\'t '
                                                   f'follow you back on instagram. Type instagram nickname, '
                                                   f'and we\'ll start:')

    bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, callback=get_instagram_username)


def get_instagram_username(message):
    """
    Callback for user entered his instagram nickname
    :param message: message instance
    :return: None
    """
    instagram_link = f'https://instagram.com/{message.text}'
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(types.InlineKeyboardButton(text=f'yes', callback_data=f'get_overall_account_information'),
                 types.InlineKeyboardButton(text=f'no', callback_data=f'get_instagram_username'))

    bot.send_message(chat_id=message.chat.id,
                     text=f'is this your profile?\n\n{instagram_link}',
                     reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call:call.data=='get_instagram_username')
def get_instagram_username_handler(call):
    """
    Handles query request for entering instagram username
    :param call: callback instance
    :return: None
    """
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=None)
    bot.send_message(chat_id=call.message.chat.id, text=f'type instagram nickname:')
    bot.register_next_step_handler_by_chat_id(chat_id=call.message.chat.id, callback=get_instagram_username)


@bot.callback_query_handler(func=lambda call:call.data=='get_overall_account_information')
def get_overall_information(call):
    """
    Gets overall information about clients account, calculates time of
        execution, and gives choice: continue or not
    :param call: callback instance
    :return: None
    """
    username = call.message.text.split('.com/')[1]
    user_id, followers, following = model.get_overall_account_information(username)
    msg = ''
    keyboard = types.InlineKeyboardMarkup()
    if not user_id:
        msg = 'u lied 2 me! issa isnt valid account! try again'
        keyboard.row(types.InlineKeyboardButton(text=f'Enter username again', callback_data=f'get_instagram_username'))
    else:
        time_takes = datetime.timedelta(seconds=(following + followers)/20)
        msg = f'okay, here\'s what we got\n' \
              f'{"*" * 20}\n' \
              f'your user id is {user_id}\n' \
              f'followers:{followers}\n' \
              f'following: {following}\n' \
              f'{"*" * 20}\n' \
              f'calculations will take approximately {time_takes}\n' \
              f'Continue?'
        keyboard.row(types.InlineKeyboardButton(text=f'yes', callback_data=f'get_unfollowers_id:{user_id}_username:{username}'),
                     types.InlineKeyboardButton(text=f'no', callback_data=f'get_instagram_username'))
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=msg,
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call:call.data.split('get_unfollowers_id:').__len__() > 1)
def get_unfollowers_handler(call):
    """
    Callback handler for command to get unfollowers list. Runs method which gets unfollowers list in new thread
    :param call: callback instance
    :return: None
    """
    user_id = call.data.split('get_unfollowers_id:')[1].split('_')[0]
    username = call.data.split('_username:')[1]
    bot.send_chat_action(chat_id=call.message.chat.id,
                         action='typing')
    _thread.start_new_thread(get_unfollowers_number, (call.message, user_id, username))    # starts new thread with method which
                                                                                    # fetches data abount unfollowers


def get_unfollowers_number(message, user_id, username):
    """
    Fetches data about accounts, which dont follow back user, runs in separated thread
    :param message: message instance
    :param user_id: user instagram id
    :param username: instagram username
    :return: None
    """
    doesnt_follow_back = model.get_unfollowers(user_id, username)
    bot.edit_message_reply_markup(chat_id=message.chat.id,
                                  message_id=message.message_id,
                                  reply_markup=None)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f'gimme list', callback_data=f'list_unfollowing_id:{user_id}_page:0'),
                 types.InlineKeyboardButton(text=f'another one', callback_data=f'get_instagram_username'))

    bot.send_message(chat_id=message.chat.id,
                     text=f'doesnt follow u back: {doesnt_follow_back.__len__()} users',
                     reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call:call.data.split('list_unfollowing_id:').__len__() > 1)
def send_unfollowing_links_list(call):
    """
    Sends user message with links to all users who doesn't follow him back, with paging
    :param call: callback instance
    :return: None
    """
    user_id = call.data.split('list_unfollowing_id:')[1].split('_')[0]
    page = int(call.data.split('_page:')[1])

    not_following_back = model.get_unfollowers(user_id=user_id, username='', download=False)
    pages, page_content = get_not_following_back_accounts_page(not_following_back, page)

    msg = f'Here\'s the list of accounts who doesn\'t follow u, page {page+1}:\n' \
          f'{"*" * 20}\n'

    for acc in page_content:
        msg += f'* https://instagram.com/{acc[1]}\n'

    keyboard = types.InlineKeyboardMarkup()

    next_page = types.InlineKeyboardButton(text=f'next', callback_data=f'list_unfollowing_id:{user_id}_page:{page+1}')
    previous_page = types.InlineKeyboardButton(text=f'prev', callback_data=f'list_unfollowing_id:{user_id}_page:{page-1}')
    create_exception = types.InlineKeyboardButton(text=f'create exceptions', callback_data=f'create_exceptions_for_user_id:{user_id}')

    if 0 < page < pages:
        keyboard.add(previous_page, next_page)
    if page==0 and page < pages:
        keyboard.add(next_page)
    if page > 0 and page == pages:
        keyboard.add(previous_page)
    if page==1:
        pass

    keyboard.add(create_exception)
    keyboard.add(types.InlineKeyboardButton(text=f'another one', callback_data=f'get_instagram_username'))

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=msg,
                          reply_markup=keyboard)


def get_not_following_back_accounts_page(not_following_back, page):
    """
    Returns tuple of overall number of pages of accounts who doesn't follow user,
        and list with accounts due to requested page
    :param not_following_back: list of all accounts who doesn't follow user
    :param page: number of page (0-n)
    :return: (number_of_pages, list_of_accounts)
    """
    page_start = page * config.ACCOUNTS_IN_LIST
    page_end = page_start + config.ACCOUNTS_IN_LIST

    not_following_back_page = not_following_back[page_start:page_end]
    pages = floor(not_following_back.__len__() / config.ACCOUNTS_IN_LIST)

    return pages, not_following_back_page

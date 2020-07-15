import config
import datetime
from emoji import emojize
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
    bot.send_message(chat_id=message.chat.id, text=f'hey, glad to see you here!{emojize(":relaxed:", use_aliases=True)}')
    bot.send_message(chat_id=message.chat.id, text=f'you can check people who doesn\'t '
                                                   f'follow you back on instagram. Type instagram nickname, '
                                                   f'and we\'ll start {emojize(" :point_down:", use_aliases=True)}')

    bot.register_next_step_handler_by_chat_id(chat_id=message.chat.id, callback=get_instagram_username)


def get_instagram_username(message):
    """
    Callback for user entered his instagram nickname
    :param message: message instance
    :return: None
    """
    instagram_link = f'https://instagram.com/{message.text}'
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(types.InlineKeyboardButton(text=emojize(" :white_check_mark:", use_aliases=True), callback_data=f'get_overall_account_information'),
                 types.InlineKeyboardButton(text=emojize(" :negative_squared_cross_mark:", use_aliases=True), callback_data=f'get_instagram_username'))

    bot.send_message(chat_id=message.chat.id,
                     text=f'is this your profile?{emojize(" :scream:", use_aliases=True)}\n\n{instagram_link}',
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
    bot.send_message(chat_id=call.message.chat.id, text=f'type instagram nickname {emojize(" :point_down:", use_aliases=True)}')
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
        msg = f'u lied 2 me! issa isnt valid account!{emojize(" :triumph:", use_aliases=True)} try again'
        keyboard.row(types.InlineKeyboardButton(text=f'{emojize("", use_aliases=True)}Enter username again', callback_data=f'get_instagram_username'))
    else:
        time_takes = datetime.timedelta(seconds=(following + followers)/20)
        msg = f'okay, here\'s what we got{emojize(" :collision:", use_aliases=True)}\n' \
              f'{"*" * 20}\n' \
              f'{emojize(" :bust_in_silhouette:", use_aliases=True)}your user id is {user_id}\n' \
              f'{emojize(" :busts_in_silhouette:", use_aliases=True)}followers:{followers}\n' \
              f'{emojize(" :tophat:", use_aliases=True)}following: {following}\n' \
              f'{"*" * 20}\n' \
              f'{emojize("", use_aliases=True)}calculations will take approximately {time_takes}\n' \
              f'Continue?'
        keyboard.row(types.InlineKeyboardButton(text=f'{emojize(" :white_check_mark:", use_aliases=True)}', callback_data=f'get_unfollowers_id:{user_id}_username:{username}'),
                     types.InlineKeyboardButton(text=f'{emojize(" :negative_squared_cross_mark:", use_aliases=True)}', callback_data=f'get_instagram_username'))
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

    if doesnt_follow_back.__len__() > 0:
        keyboard.add(types.InlineKeyboardButton(text=f'{emojize(" :heavy_plus_sign:", use_aliases=True)}gimme list',
                                                callback_data=f'list_unfollowing_id:{user_id}_page:0'),
                     types.InlineKeyboardButton(text=f'{emojize(" :pencil2:", use_aliases=True)}another one',
                                                callback_data=f'get_instagram_username'))
    else:
        keyboard.add(types.InlineKeyboardButton(text=f'{emojize(" :pencil2:", use_aliases=True)}another one', callback_data=f'get_instagram_username'))

    bot.send_message(chat_id=message.chat.id,
                     text=f'{emojize(" :pig_nose:", use_aliases=True)}doesnt follow u back: {doesnt_follow_back.__len__()} users',
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

    msg = f'Here\'s the list of accounts who doesn\'t follow u, page {page+1}/{pages+1}:\n' \
          f'{"*" * 20}\n'

    for acc in page_content:
        msg += f'* https://instagram.com/{acc[1]}\n'

    keyboard = types.InlineKeyboardMarkup()

    next_page_btn = types.InlineKeyboardButton(text=emojize(" :arrow_forward:", use_aliases=True),
                                               callback_data=f'list_unfollowing_id:{user_id}_page:{page+1}')
    previous_page_btn = types.InlineKeyboardButton(text=emojize(" :arrow_backward:", use_aliases=True),
                                                   callback_data=f'list_unfollowing_id:{user_id}_page:{page-1}')
    create_exception_btn = types.InlineKeyboardButton(text=f'{emojize(" :heavy_exclamation_mark:", use_aliases=True)}create exceptions',
                                                      callback_data=f'create_exceptions_for_user_id:{user_id}')
    main_menu_btn = types.InlineKeyboardButton(text=f'{emojize(" :back:", use_aliases=True)}main menu',
                                               callback_data=f'main_menu_edit:1')

    if 0 < page < pages:
        keyboard.add(previous_page_btn, next_page_btn)
    if page==0 and page < pages:
        keyboard.add(next_page_btn)
    if page > 0 and page == pages:
        keyboard.add(previous_page_btn)
    if page==1:
        pass

    keyboard.add(create_exception_btn)
    keyboard.add(types.InlineKeyboardButton(text=f'{emojize(" :pencil2:", use_aliases=True)}another one', callback_data=f'get_instagram_username'))
    keyboard.add(main_menu_btn)

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


def show_main_menu(message, edit=False):
    """
    Generates main menu for user
    :param message: message instance
    :param edit: boolean value, indicates if message need to be edited
    :return: None
    """

    msg = 'main menu'
    keyboard = types.InlineKeyboardMarkup()

    update_btn = types.InlineKeyboardButton(text=f'{emojize(" :repeat:", use_aliases=True)}update', callback_data=f'main_menu_edit:1')

    keyboard.add(update_btn)

    if not edit:
        bot.send_message(chat_id=message.chat.id,
                         text=msg,
                         reply_markup=keyboard)
    else:
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=message.message_id,
                              text=msg)
        bot.edit_message_reply_markup(chat_id=message.chat.id,
                                      message_id=message.message_id,
                                      reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call:call.data.split('main_menu_edit:').__len__() > 1)
def show_main_menu_handler(call):
    """
    Handles main menu callback query
    :param call: callback instance
    :return:None
    """
    is_edit = bool(call.data.split('main_menu_edit:')[1])

    show_main_menu(call.message, edit=is_edit)
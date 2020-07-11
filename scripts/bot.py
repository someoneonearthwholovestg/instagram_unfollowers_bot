import config
import datetime
import model
import telebot
from telebot import types
from termcolor import colored
import _thread

bot = telebot.TeleBot(config.TOKEN)


def init():
    """
    Initial method for bot start
    :return: None
    """
    try:
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

    keyboard.row(types.InlineKeyboardButton(text=f'yes', callback_data=f'get_overall_information'),
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


@bot.callback_query_handler(func=lambda call:call.data=='get_overall_information')
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
    _thread.start_new_thread(get_unfollowers, (call.message, user_id, username))    # starts new thread with method which
                                                                                    # fetches data abount unfollowers


def get_unfollowers(message, user_id, username):
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
    keyboard.add(types.InlineKeyboardButton(text=f'gimme list', callback_data=f'list_unfollowing'),
                 types.InlineKeyboardButton(text=f'another one', callback_data=f'get_instagram_username'))

    bot.send_message(chat_id=message.chat.id,
                     text=f'doesnt follow u back: {doesnt_follow_back.__len__()} users',
                     reply_markup=keyboard)
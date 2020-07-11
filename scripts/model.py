import config
import db_handler
import requests
import json
from termcolor import colored
import time
from random import randint
import pickle
import os


def get_overall_account_information(username):
    """
    Downloads overall information abount account, like user_id,
    count of followers, count of following accounts
    :param username: client instagram username
    :return: tuple with (user_id, followers_count, following_count) if account exists,
        and (None, None, None) otherwise
    """

    user_id=None
    followers_info=None
    following_info=None

    overall_info_url = f'https://instagram.com/{username}/?__a=1'
    res = requests.get(overall_info_url)

    if res.status_code == 200:
        res = res.json()
    else:
        return user_id, followers_info, following_info

    try:
        followers_info = res['graphql']['user']['edge_followed_by']['count']
        following_info = res['graphql']['user']['edge_follow']['count']
        user_id = res['graphql']['user']['id']
    except KeyError as kerr:
        pass

    return user_id, followers_info, following_info


def get_unfollowers(user_id, username):
    not_following_back = []

    print('\n')
    print('-' * 30)
    followers = get_followers(user_id, username)
    following = get_following(user_id, username)

    print(f'followers: {followers.__len__()}')
    print(f'following: {following.__len__()}')

    dump_followers(user_id, followers, following)

    print('calculating rats ... ', end='')

    for followee in following:
        if followee not in followers:
            not_following_back.append(followee)

    print(colored('DONE', 'green'))
    dump_not_following_back_list(user_id, not_following_back)

    return not_following_back


def get_followers(user_id, username):
    """
    Downloading from instagram list of client's followers
    :param user_id: client instagram id
    :param username: client username
    :return: list with tuples of client's followers i.e. (instagram_id, username)
    """
    followers = []
    end_cursor = ''
    has_next_page = True

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-CSRFToken': 'oxilfUJnqCIJteECMP6zW6O7668NiB6i',
        'X-IG-App-ID': '936619743392459',
        'X-IG-WWW-Claim': 'hmac.AR3Kny3HF-Th32yVAevSRIsFGdIwF_BK--Utv75fBqFu_g5b',
        'X-Requested-With': 'XMLHttpRequest',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': f'https://www.instagram.com/{username}/followers/',
        'Cookie': 'mid=XYiWOAAEAAHHv4QPy6ISVXw5tHG4; ig_did=2F94D643-59E3-4001-82A8-79406FEB1DF1; shbid=2646; shbts=1594310792.1391132; rur=PRN; urlgen="{\"176.98.24.9\": 49889\054 \"176.98.30.5\": 49889}:1juEUI:PYnUR1D3ZslZ7UmVNn6QUAmns_8"; csrftoken=oxilfUJnqCIJteECMP6zW6O7668NiB6i; ds_user_id=4639455363; sessionid=4639455363%3AZN7jKlAyQa26JQ%3A0',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'TE': 'Trailers'
    }

    first_page = f'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&' \
                 f'variables=%7B%22id%22%3A%22{user_id}%22%2C%22include_reel%22%3Atrue%2C%22' \
                 f'fetch_mutual%22%3Atrue%2C%22first%22%3A24%7D'

    res = requests.get(first_page, headers=headers)
    print('getting followers ... ', end='')
    while has_next_page:
        try:
            has_next_page = bool(res.json()['data']['user']['edge_followed_by']['page_info']['has_next_page'])
        except KeyError as kerr:
            pass

        for node in res.json()['data']['user']['edge_followed_by']['edges']:
            followers.append((node['node']['id'], node['node']['username']))

        if has_next_page:
            end_cursor = res.json()['data']['user']['edge_followed_by']['page_info']['end_cursor'].replace('==', '')
            next_page = f'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a' \
                        f'&variables=%7B%22id%22%3A%22{user_id}%22%2C%22' \
                        f'include_reel%22%3Atrue%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A14%2C%22' \
                        f'after%22%3A%22{end_cursor}%3D%3D%22%7D'

            # time.sleep(randint(2,5))    # delay, prevents instagram ban
            res = requests.get(next_page, headers=headers)

        else:
            print(colored('DONE', 'green'))

    return followers


def get_following(user_id, username):
    """
    Downloading from instagram list of users which client follows
    :param user_id: client instagram id
    :param username: client username
    :return: list with tuples of following users by client i.e. (instagram_id, username)
    """
    following = []
    end_cursor = ''
    has_next_page = True

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-CSRFToken': 'oxilfUJnqCIJteECMP6zW6O7668NiB6i',
        'X-IG-App-ID': '936619743392459',
        'X-IG-WWW-Claim': 'hmac.AR3Kny3HF-Th32yVAevSRIsFGdIwF_BK--Utv75fBqFu_g5b',
        'X-Requested-With': 'XMLHttpRequest',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Referer': f'https://www.instagram.com/{username}/followers/',
        'Cookie': 'mid=XYiWOAAEAAHHv4QPy6ISVXw5tHG4; ig_did=2F94D643-59E3-4001-82A8-79406FEB1DF1; shbid=2646; shbts=1594310792.1391132; rur=PRN; urlgen="{\"176.98.24.9\": 49889\054 \"176.98.30.5\": 49889}:1juEUI:PYnUR1D3ZslZ7UmVNn6QUAmns_8"; csrftoken=oxilfUJnqCIJteECMP6zW6O7668NiB6i; ds_user_id=4639455363; sessionid=4639455363%3AZN7jKlAyQa26JQ%3A0',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'TE': 'Trailers'
    }

    first_page = f'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&' \
                 f'variables=%7B%22id%22%3A%22{user_id}%22%2C%22include_reel%22%3Atrue%2C%22' \
                 f'fetch_mutual%22%3Afalse%2C%22first%22%3A24%7D'

    res = requests.get(first_page, headers=headers)
    print('getting following ... ', end='')
    while has_next_page:
        try:
            has_next_page = bool(res.json()['data']['user']['edge_follow']['page_info']['has_next_page'])
        except KeyError as kerr:
            pass

        for node in res.json()['data']['user']['edge_follow']['edges']:
            following.append((node['node']['id'], node['node']['username']))

        if has_next_page:
            end_cursor = res.json()['data']['user']['edge_follow']['page_info']['end_cursor'].replace('==', '')
            next_page = f'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076' \
                        f'&variables=%7B%22id%22%3A%22{user_id}%22%2C%22include_reel%22%3Atrue%2C%22' \
                        f'fetch_mutual%22%3Afalse%2C%22first%22%3A12%2C%22after%22%3A%22{end_cursor}%3D%3D%22%7D'
            # time.sleep(randint(2, 5))  # delay, prevents instagram ban
            res = requests.get(next_page, headers=headers)
        else:
            print(colored('DONE', 'green'))

    return following


def dump_followers(user_id, followers, following):
    """
    Dumps to disk lists with followers and following people using pickle module,
     to directory with user instagram id, which located at /client_data dir.
    :param user_id: instagram user id of client
    :param followers: list with tuples of (follower_id, follower_nickname)
    :param following: list with tuples of (following_id, following_nickname)
    :return: None
    """
    if not os.path.exists(config.WORKING_DIR.replace('scripts', f'client_data/{user_id}')):
        try:
            os.mkdir(config.WORKING_DIR.replace('scripts', f'client_data/{user_id}'))
        except OSError as oserr:
            print(colored(oserr, 'red'))

    with open(
            config.WORKING_DIR.replace("scripts", f"/client_data/{user_id}/{user_id}_followers.pickle"),
            'wb') as f:
        pickle.dump(followers, f)
    with open(config.WORKING_DIR.replace("scripts", f"/client_data/{user_id}/{user_id}_followed.pickle"),
              'wb') as f:
        pickle.dump(following, f)


def dump_not_following_back_list(user_id, not_following_back):
    """
    Dumps to disk list of people who doesn't follow back user with pickle module
    :param user_id: user instagram id
    :param not_following_back: list with tuples of (user_id, username)
    :return: None
    """
    path = config.WORKING_DIR.replace('scripts', f'client_data/{user_id}/{user_id}_not_following_back.pickle')
    with open(path,'wb') as f:
        pickle.dump(not_following_back, f)

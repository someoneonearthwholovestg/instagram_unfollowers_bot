import config
import db_handler
import requests
import json
from termcolor import colored
import time
from random import randint
import pickle
import os


class Model:
    def __init__(self):
        """
        Initializes model instance and gets needed data from instagram
        :return: None
        """
        print('starting session and getting headers ... ', end='')
        self.session = requests.Session()

        self.get_initial_headers()
        print(colored('DONE', 'green'))

    def get_initial_headers(self):
        """
        Sends to instagram initial requests to get needed http headers to session
        :return: None
        """
        q = 'https://www.instagram.com/accounts/login/ajax/'
        res = self.session.get(q)

        auth_headers = {
            'referer': 'https://www.instagram.com/accounts/login',
            'X-CSRFToken': res.cookies['csrftoken'],
        }
        auth = {
            'username': 'oleyezonme',
            'enc_password': '#PWD_INSTAGRAM_BROWSER:10:1594726296:AWlQABfIIa5xYHPSGdhR+6LpqTnJ5D5E+wpX5zdx4yM9/DF8PEURwsy8VViGsAdxdTk/uTuPovqPNHNlCZRf+SxINp1Cs7I3r1QLgW7WrpJkTrneD3A2HuZG5V9yhJqNLYVh7gEm1gkhO/D2VQ==',
            'optIntoOneTap': 'false'
        }
        self.session.post(q, data=auth, headers=auth_headers)
        self.session.headers['X-CSRFToken'] = res.cookies['csrftoken']

    def specify_needed_headers_to_session(self):
        """
        Specifies all needed http headers to session
        :return: None
        """
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'
        self.session.headers['Accept'] = '*/*'
        self.session.headers['Accept-Language'] = 'en-US,en;q=0.5'
        self.session.headers['Accept-Encoding'] = 'gzip, deflate, br'
        self.session.headers['X-IG-WWW-Claim'] = 'hmac.AR3Kny3HF-Th32yVAevSRIsFGdIwF_BK--Utv75fBqFu_g5b'
        self.session.headers['X-IG-App-ID'] = '936619743392459'
        self.session.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.session.headers['DNT'] = '1'
        self.session.headers['Connection'] = 'keep-alive'
        self.session.headers['Pragma'] = 'no-cache'
        self.session.headers['Cache-Control'] = 'no-cache'
        self.session.headers['Cookie'] = [f'{x.name}={x.value}; ' for x in self.session.cookies].__str__().replace('[', '').replace(']','').replace(',', '').replace('\'', '')

    def get_overall_account_information(self, username):
        """
        Downloads overall information abount account, like user_id,
        count of followers, count of following accounts
        :param username: client instagram username
        :return: tuple with (user_id, followers_count, following_count) if account exists,
            and (None, None, None) otherwise
        """

        user_id = None
        followers_info = None
        following_info = None

        self.session.headers['Referer']= f'https://www.instagram.com/{username}/'

        overall_account_info_url = f'https://www.instagram.com/{username}/?__a=1'
        res = self.session.get(overall_account_info_url, headers=self.session.headers)
        self.session.headers['X-CSRFToken'] = res.cookies['csrftoken']

        if res.status_code == 200:
            res = res.json()
        else:
            return user_id, followers_info, following_info

        try:
            user_id = res['graphql']['user']['id']
            followers_info = res['graphql']['user']['edge_followed_by']['count']
            following_info = res['graphql']['user']['edge_follow']['count']

        except KeyError as kerr:
            pass

        return user_id, followers_info, following_info

    def get_unfollowers(self, user_id, username, download=True):
        """
        Gets list of accounts who doesn't follow client
        :param user_id: user instagram id
        :param username: instagram username
        :param download: flag which says if its need to download data from instagram, or get from dump
        :return: list of tuples with accounts who doesn't follow user
        """
        not_following_back = []

        if download:
            print('\n')
            print('-' * 30)

            followers = self.download_followers_list(user_id, username)
            following = self.download_accounts_user_following_list(user_id, username)

            print(f'followers: {followers.__len__()}')
            print(f'following: {following.__len__()}')

            self.dump_followers(user_id, followers, following)

            print('calculating rats ... ', end='')

            for followee in following:
                if followee not in followers:
                    not_following_back.append(followee)

            print(colored('DONE', 'green'))
            self.dump_not_following_back_list(user_id, not_following_back)
        else:
            with open(f'{config.WORKING_DIR.replace("scripts", "")}client_data/{user_id}/{user_id}_not_following_back.pickle', 'rb') as f:
                not_following_back = pickle.load(f)

        return not_following_back

    def download_followers_list(self, user_id, username):
        """
        Downloading from instagram list of client's followers
        :param user_id: client instagram id
        :param username: client username
        :return: list with tuples of client's followers i.e. (instagram_id, username)
        """
        followers = []
        end_cursor = ''
        has_next_page = True

        self.session.headers['Referer']= f'https://www.instagram.com/{username}/followers'

        first_page_url = f'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&' \
                     f'variables=%7B%22id%22%3A%22{user_id}%22%2C%22include_reel%22%3Atrue%2C%22' \
                     f'fetch_mutual%22%3Atrue%2C%22first%22%3A24%7D'

        res = self.session.get(first_page_url, headers=self.session.headers)
        self.session.headers['X-CSRFToken'] = res.cookies['csrftoken']

        print('getting followers ... ', end='')
        while has_next_page:
            try:
                has_next_page = bool(
                    res.json()['data']['user']['edge_followed_by']['page_info']['has_next_page'])
            except KeyError as kerr:
                pass
            try:
                for node in res.json()['data']['user']['edge_followed_by']['edges']:
                    followers.append(
                        (node['node']['id'], node['node']['username']))
            except Exception as err:
                print()

            if has_next_page:
                end_cursor = res.json()[
                    'data']['user']['edge_followed_by']['page_info']['end_cursor'].replace('==', '')
                next_page = f'https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a' \
                            f'&variables=%7B%22id%22%3A%22{user_id}%22%2C%22' \
                            f'include_reel%22%3Atrue%2C%22fetch_mutual%22%3Afalse%2C%22first%22%3A14%2C%22' \
                            f'after%22%3A%22{end_cursor}%3D%3D%22%7D'

                # time.sleep(randint(2,5))    # delay, prevents instagram ban
                res = self.session.get(next_page, headers=self.session.headers)
                self.session.headers['X-CSRFToken'] = res.cookies['csrftoken']

            else:
                print(colored('DONE', 'green'))

        return followers

    def download_accounts_user_following_list(self, user_id, username):
        """
        Downloading from instagram list of users which client follows
        :param user_id: client instagram id
        :param username: client username
        :return: list with tuples of following users by client i.e. (instagram_id, username)
        """
        following = []
        end_cursor = ''
        has_next_page = True

        first_page = f'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&' \
                     f'variables=%7B%22id%22%3A%22{user_id}%22%2C%22include_reel%22%3Atrue%2C%22' \
                     f'fetch_mutual%22%3Afalse%2C%22first%22%3A24%7D'

        res = self.session.get(first_page, headers=self.session.headers)
        self.session.headers['X-CSRFToken'] = res.cookies['csrftoken']

        print('getting following ... ', end='')
        while has_next_page:
            try:
                has_next_page = bool(
                    res.json()['data']['user']['edge_follow']['page_info']['has_next_page'])
            except KeyError as kerr:
                pass

            for node in res.json()['data']['user']['edge_follow']['edges']:
                following.append((node['node']['id'], node['node']['username']))

            if has_next_page:
                end_cursor = res.json()[
                    'data']['user']['edge_follow']['page_info']['end_cursor'].replace('==', '')
                next_page = f'https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076' \
                            f'&variables=%7B%22id%22%3A%22{user_id}%22%2C%22include_reel%22%3Atrue%2C%22' \
                            f'fetch_mutual%22%3Afalse%2C%22first%22%3A12%2C%22after%22%3A%22{end_cursor}%3D%3D%22%7D'
                # time.sleep(randint(2, 5))  # delay, prevents instagram ban
                res = self.session.get(next_page, headers=self.session.headers)
                self.session.headers['X-CSRFToken'] = res.cookies['csrftoken']

            else:
                print(colored('DONE', 'green'))

        return following

    def dump_followers(self, user_id, followers, following):
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
                os.mkdir(config.WORKING_DIR.replace(
                    'scripts', f'client_data/{user_id}'))
            except OSError as oserr:
                print(colored(oserr, 'red'))

        with open(
                config.WORKING_DIR.replace(
                    "scripts", f"/client_data/{user_id}/{user_id}_followers.pickle"),
                'wb') as f:
            pickle.dump(followers, f)
        with open(config.WORKING_DIR.replace("scripts", f"/client_data/{user_id}/{user_id}_followed.pickle"),
                  'wb') as f:
            pickle.dump(following, f)

    def dump_not_following_back_list(self, user_id, not_following_back):
        """
        Dumps to disk list of people who doesn't follow back user with pickle module
        :param user_id: user instagram id
        :param not_following_back: list with tuples of (user_id, username)
        :return: None
        """
        path = config.WORKING_DIR.replace(
            'scripts', f'client_data/{user_id}/{user_id}_not_following_back.pickle')
        with open(path, 'wb') as f:
            pickle.dump(not_following_back, f)


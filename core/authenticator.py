
import time
from typing import Dict

from core.utils import log, random_str

from .exceptions import (AuthenticationError, ParamsInValidError,
                         PasswordError, UserAlreadyExistsError,
                         UserAlreadyLoginError, UserNotExistsError)
from .utils import get_time

TOKEN_TTL = 30


class Authenticator:
    '''Handler user login/register/logout'''
    file_path: str

    user_dict: Dict[str, str] = {}

    user2token_dict: Dict[str, str] = {}

    token2user_dict: Dict[str, str] = {}

    token_ttl_dict: Dict[str, int] = {}

    def __init__(self, file_path: str):
        self.file_path = file_path

        self.__load_users()
        self.__save_users()

    def __load_users(self):
        try:
            self.user_dict = {}

            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    if not line:
                        continue

                    seps = line.strip().split(' ')
                    if len(seps) == 2:
                        user, passwd = seps
                        self.user_dict[user] = passwd

        except Exception as e:
            print(e)

    def __save_users(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                for user, passwd in self.user_dict.items():
                    f.write(f'{user} {passwd}\n')

        except Exception as e:
            print(e)

    def __generate_token(self, user: str) -> str:
        token = random_str()
        self.user2token_dict[user] = token
        self.token2user_dict[token] = user
        self.token_ttl_dict[token] = get_time() + TOKEN_TTL
        return token

    def login(self, user: str, passwd: str) -> str:
        '''user login, return token if success'''
        if not user:
            raise ParamsInValidError(400, 'Username can not be empty')
        
        if len(user) < 3:
            raise ParamsInValidError(400, 'Username too short')

        elif user not in self.user_dict:
            raise UserNotExistsError(403, f'User {user} not exists')

        elif user in self.user2token_dict:
            raise UserAlreadyLoginError(403, f'User {user} already login')

        elif self.user_dict[user] != passwd:
            if not passwd:
                raise PasswordError(
                    200, f'User {user} exists, please enter the password')
            else:
                raise PasswordError(403, f'Password error for user {user}')

        else:
            token = self.__generate_token(user)
            return token

    def register(self, user: str, passwd: str) -> str:
        '''user register, return token if success'''
        if not user:
            raise ParamsInValidError(400, 'Username can not be empty')

        if len(user) < 3:
            raise ParamsInValidError(400, 'Username too short')

        elif user in self.user_dict:
            raise UserAlreadyExistsError(403, f'User {user} already exists')

        elif len(passwd) < 3:
            if not passwd:
                raise PasswordError(
                    200, f'Username {user} avilable, please enter the password')
            else:
                raise ParamsInValidError(400, 'Password too short')

        else:
            self.user_dict[user] = passwd
            self.__save_users()

            token = self.__generate_token(user)
            return token

    def logout(self, token: str) -> bool:
        '''user logout, return True if success'''
        user = self.auth(token)

        self.token2user_dict.pop(token, None)
        self.user2token_dict.pop(user, None)
        self.token_ttl_dict.pop(token, None)
        return True

    def auth(self, token: str) -> str:
        '''user auth, return user if success'''
        if not token or token not in self.token2user_dict:
            raise AuthenticationError(401, 'Unauthorized')

        else:
            user = self.token2user_dict[token]

            if user not in self.user_dict:
                self.logout(token)
                log(f'User {user} nolonger exists, logout.', None, True)
                raise UserNotExistsError(403, f'User {user} not exists')

            return user

    def count_online(self) -> int:
        count = len(self.token2user_dict.keys())
        return count

    def renewal_token(self, token):
        if not token or token not in self.token_ttl_dict:
            raise AuthenticationError(401, 'Unauthorized')

        self.token_ttl_dict[token] = get_time() + TOKEN_TTL

    def check_ttl(self):
        while True:
            expired = []
            now = get_time()

            for token, ttl in self.token_ttl_dict.items():
                if now > ttl:
                    expired.append(token)

            for token in expired:
                user = self.auth(token)
                self.logout(token)
                log(f'{user} \'s session expressed, auto logout!', None, True)

            if expired:
                count = self.count_online()
                log(f'Online users: {count}', None, False)

            time.sleep(TOKEN_TTL)

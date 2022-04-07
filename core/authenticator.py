'''
# @Author       : Chr_
# @Date         : 2022-04-07 00:06:04
# @LastEditors  : Chr_
# @LastEditTime : 2022-04-07 13:36:13
# @Description  : 
'''

from typing import Dict

from core.utils import log, random_str

from .exceptions import (AuthenticationError, ParamsInValidError,
                         PasswordError, UserAlreadyExistsError,
                         UserAlreadyLoginError, UserNotExistsError)


class Authenticator:
    '''Handler user login/register/logout'''
    file_path: str

    user_dict: Dict[str, str] = {}

    user2token_dict: Dict[str, str] = {}
    token2user_dict: Dict[str, str] = {}

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
        token = random_str(20)
        self.user2token_dict[user] = token
        self.token2user_dict[token] = user
        return token

    def login(self, user: str, passwd: str) -> str:
        '''user login, return token if success'''
        if not user or not passwd:
            raise ParamsInValidError(
                400, 'Username or password can not be empty')

        elif user not in self.user_dict:
            raise UserNotExistsError(403, f'User {user} not exists')

        elif self.user_dict[user] != passwd:
            raise PasswordError(403, f'Password error for user {user}')

        elif user in self.user2token_dict:
            raise UserAlreadyLoginError(403, f'User {user} already login')

        else:
            token = self.__generate_token(user)
            return token

    def register(self, user: str, passwd: str) -> str:
        '''user register, return token if success'''
        if not user or not passwd:
            raise ParamsInValidError(
                400, 'Username or password can not be empty')

        elif user in self.user_dict:
            raise UserAlreadyExistsError(403, f'User {user} already exists')

        else:
            self.user_dict[user] = passwd
            self.__save_users()

            token = self.__generate_token(user)
            return token

    def logout(self, token: str) -> bool:
        '''user logout, return True if success'''
        user = self.auth(token)

        self.token2user_dict.pop(token)
        self.user2token_dict.pop(user)
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

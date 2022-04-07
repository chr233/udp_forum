'''
# @Author       : Chr_
# @Date         : 2022-04-06 16:10:34
# @LastEditors  : Chr_
# @LastEditTime : 2022-04-07 11:30:30
# @Description  : 
'''


class ForumBaseException(Exception):

    def __init__(self, code: int, msg: str) -> None:
        super().__init__(code, msg)
        self._m = msg
        self._c = code

    @property
    def msg(self):
        return self._m

    @property
    def code(self):
        return self._c


class PayloadError(ForumBaseException):
    ...


class AuthenticationError(ForumBaseException):
    ...


class UserNotExistsError(AuthenticationError):
    ...


class UserAlreadyExistsError(AuthenticationError):
    ...


class UserAlreadyLoginError(AuthenticationError):
    ...


class PasswordError(AuthenticationError):
    ...


class ParamsInValidError(ForumBaseException):
    ...


class PostBaseException(ForumBaseException):
    ...


class PostNotExitsError(PostBaseException):
    ...


class PostTitleDuplicateError(PostBaseException):
    ...

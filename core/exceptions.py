'''
# @Author       : Chr_
# @Date         : 2022-04-06 16:10:34
# @LastEditors  : Chr_
# @LastEditTime : 2022-04-07 22:07:43
# @Description  : 
'''


class ForumBaseException(Exception):
    '''ForumBaseException'''

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


class PayloadBaseError(ForumBaseException):
    '''PayloadBaseError'''
    ...


class PayloadInvlidError(PayloadBaseError):
    '''PayloadInvlidError'''
    ...


class MissingParamsError(PayloadBaseError):
    '''MissingParamsError'''
    ...


class UnrecognizedCmdError(PayloadBaseError):
    '''UnrecognizedCmdError'''
    ...


class AuthenticationError(ForumBaseException):
    '''AuthenticationError'''
    ...


class UserNotExistsError(AuthenticationError):
    '''UserNotExistsError'''
    ...


class UserAlreadyExistsError(AuthenticationError):
    '''UserAlreadyExistsError'''
    ...


class UserAlreadyLoginError(AuthenticationError):
    '''UserAlreadyLoginError'''
    ...


class PasswordError(AuthenticationError):
    '''PasswordError'''
    ...


class ParamsInValidError(ForumBaseException):
    '''ParamsInValidError'''
    ...


class PostBaseException(ForumBaseException):
    '''PostBaseException'''
    ...


class PostNotExitsError(PostBaseException):
    '''PostNotExitsError'''
    ...


class PostTitleDuplicateError(PostBaseException):
    '''PostTitleDuplicateError'''
    ...

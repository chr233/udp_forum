
from .exceptions import ForumBaseException
from .utils import json_serializer


class PayloadHelper:
    @staticmethod
    def request_auth(user: str, passwd: str, login: bool = True, echo: str = ''):
        '''Authentication request'''
        jd = {'cmd': 'LOG' if login else 'REG',
              'user': user, 'passwd': passwd, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_auth(code: int, token: str, msg: str = 'OK', echo: str = ''):
        '''Authentication response'''
        jd = {'code': code, 'msg': msg, 'token': token,
              'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def request_command(cmd: str, token: str, args: str = None, echo: str = ''):
        '''Command request'''
        jd = {'cmd': cmd, 'args': args or '', 'token': token, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_command(code: int, data: str = None, msg: str = 'OK', echo: str = ''):
        '''Command response'''
        jd = {'code': code, 'msg': msg, 'data': data, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_error(err: ForumBaseException, echo: str = ''):
        '''Error response'''
        name = err.__doc__ or str(err.__class__)
        jd = {'code': err.code, 'msg': err.msg, 'error': name, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def request_meta(echo: str = '', reply: bool = False):
        '''Metadata request'''
        jd = {'meta': True, 'echo': echo, 'reply': reply}
        data = json_serializer(jd)
        return data

    @staticmethod
    def request_file(name: str, body: str, title: str, token: str,  upload: bool = True, echo: str = ''):
        jd = {'cmd': 'UPD' if upload else 'DWN',
              'title': title,
              'name': name, 'body': body,
              'token': token, 'echo': echo}
        data = json_serializer(jd)
        return data

    @staticmethod
    def response_file(code: int = 200, msg: str = 'OK', name: str = '', body: str = '', echo: str = ''):
        jd = {'code': code, 'msg': msg, 'name': name,
              'body': body,  'echo': echo}
        data = json_serializer(jd)
        return data

'''
# @Author       : Chr_
# @Date         : 2022-04-06 21:13:45
# @LastEditors  : Chr_
# @LastEditTime : 2022-04-07 11:03:07
# @Description  : 工具类
'''

import random
import json
from json import JSONDecodeError
from typing import Tuple

from .exceptions import PayloadError


ASCIIS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'


def random_str(length: int = 6):
    strs = random.sample(ASCIIS, length)
    return ''.join(strs)


def log(msg: str, addr: Tuple[str, int] = None, error: bool = False):
    if not error:
        if addr:
            print(f'[\033[0;32;40m{addr[0]}:{addr[1]}\033[0m] {msg}')

        else:
            print(f'[\033[0;34;40mServer\033[0m] {msg}')
    else:
        if addr:
            print(f'[\033[0;31;40m{addr[0]}:{addr[1]}\033[0m] {msg}')

        else:
            print(f'[\033[0;35;40mServer\033[0m] {msg}')


def json_serializer(obj: object):
    jd = json.dumps(obj)
    raw = jd.encode('utf-8')
    return raw


def json_deserializer(data: bytes):

    try:
        raw = data.decode('utf-8')
        jd = json.loads(raw)
        if not isinstance(jd, dict):
            raise PayloadError(422, 'Payload invalid')
        return jd
    except UnicodeDecodeError:
        raise PayloadError(422, 'Payload can not decode to UTF-8')

    except JSONDecodeError:
        raise PayloadError(422, 'Payload can not decode to JSON')

    except Exception:
        raise PayloadError(422, 'Payload parse error')

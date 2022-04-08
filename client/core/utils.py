
import json
from base64 import b64encode
from json import JSONDecodeError
from os import path
from time import time
from typing import Dict, Tuple
from uuid import uuid1

from .exceptions import (FileTooLargeError, ForumBaseException, PayloadInvlidError)


def random_str():
    return uuid1().hex


def get_time():
    return int(time())


def package_file(file_path: str) -> Tuple[str, str]:
    name = path.basename(file_path)

    with open(file_path, 'rb') as f:
        data = f.read()
        if len(data) >8000:
            raise FileTooLargeError(413, 'File too large')

    body = b64encode(data).decode('utf-8')
    return (name, body)


def log(msg: str, addr: Tuple[str, int] = None, error: bool = False):
    if addr:
        title = f'{addr[0]}:{addr[1]}'
        color = 32 if not error else 31
    else:
        title = 'Server'
        color = 34 if not error else 35

    print(f'[\033[{color}m{title.center(8)}\033[0m] {msg}')


def json_serializer(obj: dict) -> bytes:
    jd = json.dumps(obj)
    raw = jd.encode('utf-8')
    return raw


def json_deserializer(data: bytes) -> Dict[str, str]:

    try:
        raw = data.decode('utf-8')
        jd = json.loads(raw)
        if not isinstance(jd, dict):
            raise PayloadInvlidError(422, 'Payload invalid')
        elif 'echo' not in jd:
            raise PayloadInvlidError(400, 'Missing echo in the payload')
        return jd
    except UnicodeDecodeError:
        raise PayloadInvlidError(422, 'Payload can not decode to UTF-8')

    except JSONDecodeError:
        raise PayloadInvlidError(422, 'Payload can not decode to JSON')

    except Exception as e:
        if isinstance(e, ForumBaseException):
            raise e
        else:
            raise PayloadInvlidError(422, 'Payload parse error')

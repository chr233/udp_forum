
import asyncio
import json
import random
import select
import socket
import sys
import time
from socket import socket as Socket
from threading import Thread
from typing import Dict, Tuple
from uuid import uuid1

from aioredis import AuthenticationError
from core.exceptions import ForumBaseException, PayloadBaseError


from core.payload_helper import PayloadHelper
from core.utils import json_deserializer, random_str

CMDs = {'CRT', 'LST', 'MSG', 'DLT', 'RDT',
        'UPD', 'DWN', 'RMV', 'XIT', 'HLP', }

SUDP = Socket(socket.AF_INET, socket.SOCK_DGRAM)
STCP = Socket(socket.AF_INET, socket.SOCK_STREAM)

TOKEN = ''

RETRIES = 3

ServerAddr = ''

EchoDict: Dict[str, bytes] = {}


def thread_heartbeat():
    '''Thread sending heartbeat to server'''

    while True:
        if TOKEN:
            echo = random_str()
            payload = PayloadHelper.request_command('HEART', TOKEN, None, echo)
            SUDP.sendto(payload, ServerAddr)

        time.sleep(10)


def thread_network_send(echo, payload):
    '''Thread sending data'''
    for _ in range(RETRIES + 1):
        SUDP.sendto(payload, ServerAddr)
        time.sleep(5)

        if EchoDict.get(echo, None) or echo not in EchoDict:
            break


def thread_network_recv():
    '''Thread receiving data'''
    inputs = [SUDP]

    while True:
        rlist, _, _ = select.select(inputs, [], [], 1)
        for event in rlist:
            if event == SUDP:
                # UDP message
                data, _ = event.recvfrom(8192)
                udp_handler(data)


def udp_handler(raw: bytes):
    '''Handle UDP message'''
    global TOKEN
    try:
        payload = json_deserializer(raw)
        echo = payload['echo']

        if 'code' in payload and 'msg' in payload:
            reply = True
            if 'error' in payload:  # error message
                if payload['error'] == 'AuthenticationError':
                    TOKEN = ''
            elif 'token' in payload:  # login message
                ...
            elif 'data' in payload:  # normal message
                ...

        elif 'meta' in payload:  # meta
            reply = payload.get('reply', False)

        else:
            log(f'Unrecognized payload: {payload}', True)
            return

        if echo in EchoDict:
            EchoDict[echo] = payload

        if reply:
            payload = PayloadHelper.request_meta(echo, False)
            SUDP.sendto(payload, ServerAddr)

    except KeyError as e:
        log(f'Bad payload: {payload}', True)

    except ForumBaseException as e:
        log(f'{e.msg}', True)

    # except Exception as e:
    #     err = PayloadError(500, 'Internal Server Error')
    #     response = PayloadHelper.response_error(err, echo)


def waiting_screen(key: str, timeout: int = 10):
    '''Waiting for response'''
    ascii = ['|', '/', '-', '\\']

    i = 0
    end = time.time() + timeout

    while time.time() < end:
        if EchoDict.get(key, None):
            print('\r', end='')
            return

        char = ascii[i]
        if i < 3:
            i += 1
        else:
            i = 0

        print(f'\rWating {char}', end='')

        time.sleep(0.1)

    print('\r \033[31mProcess Timeout!\033[0m\n')
    raise TimeoutError("Timeout!")


def log(msg: str,  error: bool = False):
    '''Logging'''
    title = 'Client'
    color = 32 if not error else 31
    print(f'[\033[{color}m{title}\033[0m] {msg}')


def ipt(user: str):
    '''Input text'''
    while True:
        txt = input(f'\033[32m$ {user.center(6)}\033[0m > ')
        if txt:
            return txt


def call_with_retries(payload: bytes, echo: str, timeout: int = 10):
    '''Call server with retries'''
    EchoDict[echo] = None
    Thread(target=thread_network_send, args=(
        echo, payload), daemon=True).start()
    waiting_screen(echo, timeout)
    result = EchoDict.pop(echo)
    return result


def test_server_connection():
    '''Test server connection'''
    while True:
        try:
            log(f'Connecting to {ServerAddr[0]}:{ServerAddr[1]} ...', False)

            echo = random_str()
            payload = PayloadHelper.request_meta(echo, True)
            call_with_retries(payload, echo)

            log('Connected!', False)
            break

        except TimeoutError:
            pass


def interactive_login() -> str:
    '''Interactive login'''
    global TOKEN

    log('Login', False)

    while True:
        username = ipt('Enter your username:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, "", True, echo)
        data = call_with_retries(payload, echo)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if data.get('error', None) == 'UserNotExistsError':
            print()
            log('Do you want to register?', False)
            choice = ipt('Y: regiser, [N]: login')

            if choice.upper() == 'Y':
                return interactive_register()

        if not succ:
            continue

        passwd = ipt('Enter your password:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, passwd, True, echo)
        data = call_with_retries(payload, echo)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if succ and 'token' in data:
            TOKEN = data['token']
            return username


def interactive_register() -> str:
    '''Interactive register'''
    global TOKEN

    log('Register', False)

    while True:
        username = ipt('Enter your username:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, "", False, echo)
        data = call_with_retries(payload, echo)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if not succ:
            continue

        passwd = ipt('Enter your password:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, passwd, False, echo)
        data = call_with_retries(payload, echo)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if succ and 'token' in data:
            TOKEN = data['token']
            break

    return username


def main():
    test_server_connection()
    user = interactive_login()

    print()

    while TOKEN:
        ipt(user=user)

    # RH = RequestHelper(address)

    try:
        # RH.meta()
        ...
    except KeyboardInterrupt:
        ...

    # 登陆鉴权
    try:
        ...

    except KeyboardInterrupt:
        pass

    # 业务流程
    try:

        ...
    except KeyboardInterrupt:
        pass

    return


if __name__ == '__main__':
    try:
        try:
            args = sys.argv[1:] or ['9999', 'localhost']

            length = len(args)

            if length == 0:
                host = 'locaohost'
                port = 9999
            elif length == 1:
                host = 'localhost'
                port = int(args[0])
            else:
                port = int(args[0])
                host = args[1]

            if port < 0 or port > 65535:
                raise ValueError

        except ValueError:
            log('Usage: python3 client.py [port] [server host]', True)
            log('Default port is 9999', True)
            log('Default server host is localhost', True)
            print('Press enter to exit...')
            input()
            exit(1)

        Thread(target=thread_heartbeat, daemon=True).start()
        Thread(target=thread_network_recv, daemon=True).start()

        ServerAddr = (host, port)

        while True:
            try:
                main()
            except TimeoutError:
                log('Reset client ...', True)

    except KeyboardInterrupt:
        print()
        log('Client shutdown ...', False)
        exit()

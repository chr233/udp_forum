
import select
import socket
import sys
import time
from base64 import b64decode
from socket import socket as Socket
from threading import Thread
from typing import Dict

from core.exceptions import FileTooLargeError, ForumBaseException
from core.payload_helper import PayloadHelper
from core.utils import json_deserializer, random_str, package_file

CMDS = ('CRT', 'LST', 'MSG', 'EDT', 'DLT',
        'RDT', 'UPD', 'DWN', 'RMV', 'XIT', 'HLP')

SUDP = Socket(socket.AF_INET, socket.SOCK_DGRAM)


RECV_BYTES = 8192
RETRIES = 3

Token = ''
ServerAddr = ''

EchoDict: Dict[str, bytes] = {}


def thread_heartbeat():
    '''Thread sending heartbeat to server'''

    while True:
        if Token:
            echo = random_str()
            payload = PayloadHelper.request_command('HEART', Token, None, echo)
            SUDP.sendto(payload, ServerAddr)

        time.sleep(10)


def thread_network_send_udp(echo, payload):
    '''Thread sending data via UDP'''
    for _ in range(RETRIES + 1):
        SUDP.sendto(payload, ServerAddr)
        time.sleep(5)

        if EchoDict.get(echo, None) or echo not in EchoDict:
            break


def thread_network_send_tcp(echo, payload):
    '''Thread sending data via TCP'''
    STCP = Socket(socket.AF_INET, socket.SOCK_STREAM)
    STCP.setblocking(True)

    for _ in range(RETRIES + 1):
        try:
            STCP.connect(ServerAddr)
            STCP.send(payload)
            raw = STCP.recv(RECV_BYTES)
            response_handler(raw)
            STCP.close()
            time.sleep(2)

            if EchoDict.get(echo, None) or echo not in EchoDict:
                break
        except OSError as e:
            log(f'TCP send error: {e}', True)


def thread_network_recv():
    '''Thread receiving data'''
    inputs = [SUDP]

    while True:
        rlist, _, _ = select.select(inputs, [], [], 1)
        for event in rlist:
            try:
                if event == SUDP:
                    # UDP message
                    data, _ = event.recvfrom(RECV_BYTES)
                    response_handler(data)
            except ConnectionResetError as e:
                log(e, True)


def response_handler(raw: bytes):
    '''Handle UDP message'''
    global Token
    try:
        payload = json_deserializer(raw)
        echo = payload['echo']

        if 'code' in payload and 'msg' in payload:
            reply = True
            if 'error' in payload:  # error message
                if payload['error'] == 'AuthenticationError':
                    Token = ''

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
        log(e.msg, True)

    except Exception as e:
        log(f'Unknown error: {e}', True)


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
    raise TimeoutError('Timeout!')


def log(msg: str,  error: bool = False):
    '''Logging'''
    title = 'Client'
    color = 32 if not error else 31
    print(f'\r[\033[{color}m {title} \033[0m] {msg}')


def logcmd(msg: str, error: bool = False):
    '''Logging cmd result'''
    color = 34 if not error else 31
    title = 'Result' if not error else 'Error'
    sep = '<'
    for line in msg.split('\n'):
        print(f'\033[{color}m$ {title.center(6)}\033[0m {sep} {line}')
        title = ''
        sep = ' '


def ipt(user: str):
    '''Input text'''
    while True:
        txt = input(f'\033[32m$ {user.center(6) }\033[0m> ')
        if txt:
            return txt


def call_with_retries(payload: bytes, echo: str, upd: bool = True, timeout: int = 10):
    '''Call server with retries'''
    EchoDict[echo] = None
    target = thread_network_send_udp if upd else thread_network_send_tcp
    Thread(target=target, args=(echo, payload), daemon=True).start()
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
            call_with_retries(payload, echo, True, 10)

            log('Connected!', False)
            break

        except TimeoutError:
            pass


def interactive_login() -> str:
    '''Interactive login'''
    global Token

    print()

    log('Login', False)

    while True:
        username = ipt('Enter username:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, '', True, echo)
        data = call_with_retries(payload, echo, True, 10)

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

        passwd = ipt('Enter password:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, passwd, True, echo)
        data = call_with_retries(payload, echo, True, 10)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if succ and 'token' in data:
            Token = data['token']
            return username


def interactive_register() -> str:
    '''Interactive register'''
    global Token

    print()

    log('Register', False)

    while True:
        username = ipt('Enter username:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, '', False, echo)
        data = call_with_retries(payload, echo, True, 10)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if not succ:
            continue

        passwd = ipt('Enter password:')

        echo = random_str()
        payload = PayloadHelper.request_auth(username, passwd, False, echo)
        data = call_with_retries(payload, echo, True, 10)

        code = data['code']
        succ = code == 200
        log(data['msg'], not succ)

        if succ and 'token' in data:
            Token = data['token']
            break

    return username


def interactive_commdline(user: str) -> str:
    '''Interactive register'''

    while Token:
        argv = ipt(user)

        args = argv.split(' ')

        if len(args) == 0:
            continue

        cmd = args[0]
        argv = ' '.join(args[1:])

        echo = random_str()

        if cmd == 'UPD':
            title = ' '.join(args[1:-1])
            try:
                f_name, f_body = package_file(args[-1])
            except FileTooLargeError:
                logcmd(f'File {f_name} too large!', True)
                continue
            except IOError:
                logcmd(f'File {f_name} not found!', True)
                continue
            except Exception as e:
                logcmd(f'Unknown error: {e}', True)
                continue

            payload = PayloadHelper.request_file(
                f_name, f_body, title, Token, True, echo)
            data = call_with_retries(payload, echo, False, 10)

        elif cmd == 'DWN':
            title = ' '.join(args[1:-1])
            f_name = args[-1]

            payload = PayloadHelper.request_file(
                f_name, "", title, Token, False, echo)
            data = call_with_retries(payload, echo, False, 10)

            try:
                with open(f_name, 'wb') as f:
                    body = data['body']
                    raw = b64decode(body.encode('utf-8'))
                    f.write(raw)
            except IOError:
                logcmd(f'Download file {f_name} error!', True)
                continue
            except Exception as e:
                logcmd(f'Unknown error: {e}', True)
                continue
        else:
            payload = PayloadHelper.request_command(cmd, Token, argv, echo)
            data = call_with_retries(payload, echo, True, 10)

        code = data['code']
        msg = data.get('data', None) or data.get(
            'msg', None) or 'Unknown Error'
        if code == 200:
            logcmd(msg, False)
        elif code == 201:
            log(msg, True)
            return

        else:
            logcmd(msg, True)


def main():
    test_server_connection()
    
    user = interactive_login()

    print()

    log('Avilable commands:', False)
    log(', '.join(CMDS), False)

    print()

    interactive_commdline(user)


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


from socket import socket as Socket
from threading import Thread
from typing import Tuple

from .authenticator import Authenticator
from .exceptions import (ArgumentError, AuthenticationError,
                         ForumBaseException, MissingParamsError,
                         PayloadInvlidError, UnrecognizedCmdError,
                         UnsupportedMethod)
from .forum_handler import ForumHandler
from .payload_helper import PayloadHelper
from .utils import json_deserializer, log

CMD_USAGE = {
    'CRT': 'Usage: CRT threadtitle',
    'LST': 'Usage: LST',
    'MSG': 'Usage: MSG threadtitle message',
    'EDT': 'Usage: EDT threadtitle messagenumber message',
    'DLT': 'Usage: DLT threadtitle messagenumber',
    'RDT': 'Usage: RDT threadtitle',
    'UPD': 'Usage: UPD threadtitle filename',
    'DWN': 'Usage: DWN threadtitle filename',
    'RMV': 'Usage: RMV threadtitle',
    'XIT': 'Usage: XIT',
    'HLP': 'Usage: HLP [command]',
    # 'REG': None,
    # 'LOG': None,
    # 'HEART': None
}

CMDS = CMD_USAGE.keys()


class UDPHandler():
    sock: Socket
    auth: Authenticator
    forum: ForumHandler

    def __init__(self, auth: Authenticator, forum: ForumHandler, sock: Socket):
        self.sock = sock
        self.auth = auth
        self.forum = forum

        Thread(target=auth.check_ttl, daemon=True).start()

    def handle_message(self, raw: bytes, addr: Tuple[str, int]):
        try:
            response = None

            payload = json_deserializer(raw)

            # log(f'U IN  <-- {payload}', None, False)

            echo = payload['echo']

            if 'cmd' in payload:

                cmd = payload['cmd']

                if 'token' in payload and 'args' in payload:
                    # normal command
                    token = payload['token']
                    user = self.auth.auth(token)

                    args = (payload['args'] or '').split()

                    msg = 'OK'

                    if cmd == 'HEART':  # Heartbeat
                        self.auth.renewal_token(token)
                        response = None

                    elif cmd == 'CRT':  # Create Thread, CRT <title>
                        if len(args) < 1:
                            raise ArgumentError(400, CMD_USAGE[cmd])

                        title = ' '.join(args)
                        new_post = self.forum.create_thread(title, user)

                        result = f'{new_post.pid} {new_post.title}'

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)

                    elif cmd == 'LST':  # List Threads, LST
                        result = self.forum.list_threads()

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)
                    elif cmd == 'MSG':  # Post Message, MSG <title> <message>
                        if len(args) < 2:
                            raise ArgumentError(400, CMD_USAGE[cmd])

                        title = args[0]
                        message = ' '.join(args[1:])
                        result = self.forum.post_message(title, message, user)

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)
                    elif cmd == 'EDT':  # Edit Message, EDT <title> <messagenumber> <message>
                        if len(args) < 3:
                            raise ArgumentError(400, CMD_USAGE[cmd])

                        title = args[0]
                        message = ' '.join(args[2:])
                        try:
                            messagenum = int(args[1])
                        except ValueError:
                            raise ArgumentError(
                                400, f'Messagenumber must be integer!')

                        result = self.forum.edit_message(
                            title, messagenum, message, user)

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)
                    elif cmd == 'DLT':  # Delete Message, DLT <title> <messagenumber>
                        if len(args) < 2:
                            raise ArgumentError(400, CMD_USAGE[cmd])

                        title = args[0]
                        try:
                            messagenum = int(args[1])
                        except ValueError:
                            raise ArgumentError(
                                400, f'Messagenumber must be integer!')

                        result = self.forum.delete_message(
                            title, messagenum,  user)

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)
                    elif cmd == 'RDT':  # Read Thread, RDT <title>
                        if len(args) < 1:
                            raise ArgumentError(400, CMD_USAGE[cmd])

                        title = ' '.join(args)

                        result = self.forum.read_thread(title)

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)
                    elif cmd == 'UPD':  # Upload file, UPD <title> <filename>
                        err = UnsupportedMethod(
                            400, 'UDP command must send using TCP')
                        
                        response = PayloadHelper.response_error(err, echo=echo)                        
                    elif cmd == 'DWN':  # Download file, DWN <title> <filename>
                        err = UnsupportedMethod(
                            400, 'UDP command must send using TCP')
                        
                        response = PayloadHelper.response_error(err, echo=echo)                        
                    elif cmd == 'RMV':  # Remove Thread, RMV <title>
                        if len(args) < 1:
                            raise ArgumentError(400, CMD_USAGE[cmd])

                        title = ' '.join(args)

                        result = self.forum.delete_thread(title, user)

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)

                    elif cmd == 'HLP':  # Help, HLP [command]
                        lines = []

                        if args:
                            for arg in args:
                                if arg in CMDS:
                                    lines.append(CMD_USAGE[arg])

                        if not lines:
                            lines.append('Avilable commands:')
                            lines.append(', '.join(CMDS))

                        result = '\n'.join(lines)

                        response = PayloadHelper.response_command(
                            200, result, msg, echo=echo)

                    elif cmd == 'XIT':  # Exit
                        self.auth.logout(payload['token'])
                        log(f'User {user} successful logout!', addr, False)

                        count = self.auth.count_online()
                        log(f'Online users: {count}', None, False)

                        result = f'Bye {user} !'

                        response = PayloadHelper.response_command(
                            201, result, msg, echo=echo)

                    else:
                        raise UnrecognizedCmdError(400, f'Unrecognized cmd {cmd}')

                elif 'user' in payload and 'passwd' in payload:
                    # login/register
                    user = payload['user']
                    passwd = payload['passwd']

                    if cmd == 'REG':
                        token = self.auth.register(user, passwd)
                        msg = f'Welcome new user {user} !'
                        log(f'User {user} successful register!', addr, False)

                    elif cmd == 'LOG':
                        token = self.auth.login(user, passwd)
                        msg = f'Welcome user {user} !'
                        log(f'User {user} successful login!', addr, False)

                    count = self.auth.count_online()
                    log(f'Online users: {count}', None, False)

                    response = PayloadHelper.response_auth(
                        200, token, msg, echo=echo
                    )

                else:
                    raise MissingParamsError(400, 'Bad Request')

            elif 'meta' in payload:
                # meta
                reply = payload.get('reply', False)

                if reply:
                    log('New client connected', addr, False)
                    response = PayloadHelper.request_meta(echo, False)
                else:
                    response = None

            else:
                raise MissingParamsError(400, 'Bad Request')

        except PayloadInvlidError as e:
            response = PayloadHelper.response_error(e, 'FAULT')

        except AuthenticationError as e:
            err = e.code != 200
            log(e.msg, addr, err)
            response = PayloadHelper.response_error(e, echo)

        except KeyError as e:
            err = MissingParamsError(400, f'Missing {e} in the payload')
            response = PayloadHelper.response_error(err, echo)

        except ForumBaseException as e:
            response = PayloadHelper.response_error(e, echo)

        except Exception as e:
            err = ForumBaseException(500, 'Internal Server Error')
            response = PayloadHelper.response_error(err, echo)

        finally:
            if response:
                # log(f'U OUT --> {response.decode("utf-8")}', None, False)
                self.sock.sendto(response, addr)


from threading import Thread

from socket import socket as Socket
from typing import Tuple

from .authenticator import Authenticator
from .exceptions import AuthenticationError, ForumBaseException, MissingParamsError, PayloadInvlidError, UnrecognizedCmdError
from .forum_handler import ForumHandler
from .payload_helper import PayloadHelper
from .utils import json_deserializer, log

CMDs = {'CRT', 'LST', 'MSG', 'DLT', 'RDT',
        'UPD', 'DWN', 'RMV', 'XIT', 'HLP',
        'REG', 'LOG', 'HEART'}


class UDPHandler():
    sock: Socket
    auth: Authenticator

    def __init__(self, auth: Authenticator, forum: ForumHandler, sock: Socket):
        self.sock = sock
        self.auth = auth
        self.forum = forum

        Thread(target=auth.check_ttl, daemon=True).start()

    def handler_message(self, raw: bytes, addr: Tuple[str, int]):
        try:
            payload = json_deserializer(raw)

            log(f'IN  <-- {payload}', None, False)

            echo = payload['echo']

            if 'cmd' in payload:

                cmd = payload['cmd']

                if cmd not in CMDs:
                    raise UnrecognizedCmdError(400, 'Unrecognized cmd')

                if 'token' in payload:
                    # normal command

                    user = self.auth.auth(payload['token'])

                    msg = 'OK'

                    if cmd == 'HEART':  # Heartbeat
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)

                    elif cmd == 'CRT':  # Create Thread
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'LST':  # List Threads
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'MSG':  # Post Message
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'DLT':  # Delete Message
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'RDT':  # Read Thread
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'UPD':  # Upload file
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'DWN':  # Download file
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'RMV':  # Remove Thread
                        ...
                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)
                    elif cmd == 'XIT':  # Exit
                        self.auth.logout(payload['token'])
                        log(f'User {user} successful logout!', addr, False)

                        count = self.auth.count_online()
                        log(f'Online users: {count}', None, False)

                        msg = f'Bye {user} !'

                        response = PayloadHelper.response_command(
                            200, None, msg, echo=echo)

                    else:
                        response = PayloadHelper.response_command(
                            200, payload, msg, echo=echo)

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
                    response = PayloadHelper.request_meta(echo, False)
                else:
                    response = None

            else:
                raise MissingParamsError(400, 'Bad Request')

        except PayloadInvlidError as e:
            response = PayloadHelper.response_error(e, "FAULT")

        except KeyError as e:
            err = MissingParamsError(400, f'Missing {e} in the payload')
            response = PayloadHelper.response_error(err, echo)

        except AuthenticationError as e:
            log(f'AuthenticationError: {e.msg}', addr, True)
            response = PayloadHelper.response_error(e, echo)

        except ForumBaseException as e:
            response = PayloadHelper.response_error(e, echo)

        # except Exception as e:
        #     err = PayloadError(500, 'Internal Server Error')

        #     response = PayloadHelper.response_error(err, echo)

        finally:
            if response:
                log(f'OUT --> {response.decode("utf-8")}', None, False)
                self.sock.sendto(response, addr)

        # except Exception as e:
        #     print(e)

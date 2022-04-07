'''
# @Author       : Chr_
# @Date         : 2022-04-06 13:22:07
# @LastEditors  : Chr_
# @LastEditTime : 2022-04-07 15:19:09
# @Description  :
'''

from typing import Tuple

from socket import socket as Socket

from .forum_handler import ForumHandler
from .authenticator import Authenticator
from .exceptions import PayloadError, ForumBaseException, AuthenticationError
from .payload_helper import PayloadHelper
from .utils import json_deserializer, log


CMDs = ['CRT', 'LST', 'MSG', 'DLT', 'RDT',
        'UPD', 'DWN', 'RMV', 'XIT',
        'REG', 'LOG', 'HEART']


class UDPHandler():
    sock: Socket
    auth: Authenticator

    def __init__(self, auth: Authenticator, forum: ForumHandler, sock: Socket):
        self.sock = sock
        self.auth = auth
        self.forum = forum

    def handler_message(self, raw: bytes, addr: Tuple[str, int]):
        try:
            payload = json_deserializer(raw)

            echo = payload.get('echo', '')

            if 'cmd' in payload:

                cmd = payload['cmd']

                if cmd not in CMDs:
                    raise PayloadError(400, 'Unrecognized cmd')

                if 'token' in payload:
                    # normal command

                    user = self.auth.auth(payload['token'])

                    msg = 'OK'

                    if cmd == 'CRT':  # Create Thread

                        ...
                    elif cmd == 'LST':  # List Threads
                        ...
                    elif cmd == 'MSG':  # Post Message
                        ...
                    elif cmd == 'DLT':  # Delete Message
                        ...
                    elif cmd == 'RDT':  # Read Thread
                        ...
                    elif cmd == 'UPD':  # Upload file
                        ...
                    elif cmd == 'DWN':  # Download file
                        ...
                    elif cmd == 'RMV':  # Remove Thread
                        ...
                    elif cmd == 'XIT':  # Exit
                        self.auth.logout(payload['token'])
                        log(f'{user} successful logout!', addr, False)

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
                        log(f'{user} successful register!', addr, False)

                    elif cmd == 'LOG':
                        token = self.auth.login(user, passwd)
                        msg = f'Welcome user {user} !'
                        log(f'{user} successful login!', addr, False)

                    count = self.auth.count_online()
                    log(f'Online users: {count}', None, False)

                    response = PayloadHelper.response_auth(
                        200, token, msg, echo=echo
                    )

                else:
                    raise PayloadError(400, 'Bad Request')

            elif 'meta' in payload:
                # meta
                reply = payload.get('reply', False)

                if reply:
                    response = PayloadHelper.request_meta(echo, False)
                else:
                    response = None

            else:
                raise PayloadError(400, 'Bad Request')

        except KeyError as e:
            err = PayloadError(400, 'Bad Request')
            response = PayloadHelper.response_error(err, echo)

        except AuthenticationError as e:
            log(f'AuthenticationError: {e.msg}', addr, True)
            response = PayloadHelper.response_error(e, echo)

        except ForumBaseException as e:
            response = PayloadHelper.response_error(e, "")

        # except Exception as e:
        #     err = PayloadError(500, 'Internal Server Error')

        #     response = PayloadHelper.response_error(err, echo)

        finally:
            if response:
                self.sock.sendto(response, addr)

        # except Exception as e:
        #     print(e)

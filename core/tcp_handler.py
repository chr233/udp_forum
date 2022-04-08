
from queue import Queue
from socket import socket as Socket
from typing import Dict, Tuple

from .authenticator import Authenticator
from .exceptions import (AuthenticationError, ForumBaseException,
                         MissingParamsError, PayloadInvlidError,
                         UnrecognizedCmdError)
from .forum_handler import ForumHandler
from .payload_helper import PayloadHelper
from .utils import json_deserializer, log


class TCPHandler():
    auth: Authenticator
    forum: ForumHandler

    def __init__(self, auth: Authenticator, forum: ForumHandler):
        self.auth = auth
        self.forum = forum

    def handle_message(self, raw: bytes, addr: Tuple[str, int]):
        try:
            response = None
            # addr = sock.getpeername()
            payload = json_deserializer(raw)

            # log(f'T IN  <-- {payload}', None, False)

            echo = payload['echo']

            if 'cmd' in payload and 'title' in payload and 'name' in payload and 'token' in payload:
                cmd = payload['cmd']
                title = payload['title']
                token = payload['token']
                name = payload['name']
                user = self.auth.auth(token)

                if cmd == 'UPD':
                    if 'body' not in payload:
                        raise MissingParamsError(
                            400, 'Missing body in the payload')
                    body = payload['body']
                    result = self.forum.upload_file(title, name, body, user)

                    response = PayloadHelper.response_file(
                        200, result, '', '', echo)

                    log(f'{user} uploaded file {name} to {title} thread', addr, False)

                elif cmd == 'DWN':
                    body = self.forum.download_file(title, name)
                    result = f'Successfully download file {name}'

                    response = PayloadHelper.response_file(
                        200, result, name, body, echo)

                    log(f'{user} downloaded file {name} from {title} thread', addr, False)
                    
                else:
                    raise UnrecognizedCmdError(400, f'Unrecognized cmd {cmd}')

            else:
                raise MissingParamsError(400, 'Bad Request')

        except PayloadInvlidError as e:
            response = PayloadHelper.response_error(e, 'FAULT')

        except AuthenticationError as e:
            err = e.code != 200
            log(e.msg, None, err)
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
            if not response:
                err = ForumBaseException(500, 'Internal Server Error')
                response = PayloadHelper.response_error(err, echo)

            # log(f'T OUT --> {response.decode("utf-8")}', addr, False)
            return response

    @staticmethod
    def close_socket(sock: Socket):
        try:
            sock.close()
        except OSError:
            pass

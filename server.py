
import os
import select
import socket
import sys
from socket import socket as Socket

from core.authenticator import Authenticator
from core.forum_handler import ForumHandler
from core.udp_handler import UDPHandler
from core.utils import log

LISTEN_ON = '0.0.0.0'


def main(host, port):
    # Init user authenticator
    auth_file = os.path.abspath('./credentials.txt')
    auth = Authenticator(auth_file)

    # Init forum handler
    db_path = os.path.abspath('./db.json')
    data_path = os.path.abspath('./data/')
    forum = ForumHandler(db_path, data_path)

    # Init UDP server
    udp_socket = Socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.bind((host, port))
        log(f'UDP server listening on {host}:{port}', None, False)
    except OSError as e:
        log(f'UDP server start error: {e}', None, True)
        return

    # Init TCP server
    tcp_socket = Socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.setblocking(False)
    try:
        tcp_socket.bind((host, port))
        tcp_socket.listen()
        log(f'TCP server listening on {host}:{port}', None, False)
    except OSError as e:
        log(f'TCP server start error: {e}', None, True)
        return

    # Init UDPHandler
    udp_handler = UDPHandler(auth, forum, udp_socket)

    log('Wating for clients ...', None, False)

    # Event loop
    try:
        inputs = [tcp_socket, udp_socket]
        outputs = []
        message_queues = {}

        while True:

            rlist, wlist, _ = select.select(inputs, outputs, [], 1)
            for event in rlist:
                if event == tcp_socket:
                    # TCP incoming connection
                    log("新的客户端连接", None, False)
                    new_sock, addr = event.accept()
                    inputs.append(new_sock)

                elif event == udp_socket:
                    # UDP message
                    data, addr = event.recvfrom(8192)
                    udp_handler.handler_message(data, addr)

                else:
                    # TCP message
                    data = event.recv(8192)
                    if data:
                        log("接收到客户端信息", None, False)
                        log(data)
                        event.send(b'\x31')
                    else:
                        log("客户端断开连接", None, False)
                        inputs.remove(event)

    except KeyboardInterrupt:
        pass
    finally:
        udp_socket.close()
        tcp_socket.close()
        log('Server shutdown ...', None, True)


if __name__ == '__main__':

    try:
        port = int((sys.argv[1:] or ['9999'])[0])
        if port < 0 or port > 65535:
            raise ValueError
    except ValueError:
        log('Usage: python3 server.py [port]', None, True)
        log('Default port is 9999', None, True)
        input('Press enter to exit...')
        exit(1)

    main(LISTEN_ON, port)

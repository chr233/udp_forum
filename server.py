
import os
import select
import socket
import sys
from queue import Empty, Queue
from socket import socket as Socket

from core.authenticator import Authenticator
from core.forum_handler import ForumHandler
from core.tcp_handler import TCPHandler
from core.udp_handler import UDPHandler
from core.utils import log

LISTEN_ON = '0.0.0.0'

RECV_BYTES = 8192


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
    except OSError as s:
        log(f'UDP server start error: {s}', None, True)
        return

    # Init TCP server
    tcp_socket = Socket(socket.AF_INET, socket.SOCK_STREAM)
    # tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.setblocking(False)
    try:
        tcp_socket.bind((host, port))
        tcp_socket.listen(10)
        log(f'TCP server listening on {host}:{port}', None, False)
    except OSError as s:
        log(f'TCP server start error: {s}', None, True)
        return

    # Init UDPHandler
    udp_handler = UDPHandler(auth, forum, udp_socket)

    # Init TCPHandler
    tcp_handler = TCPHandler(auth, forum)

    log('Wating for clients ...', None, False)

    # Event loop
    try:
        inputs = [tcp_socket, udp_socket]
        outputs = []
        msg_queue = {}
        while True:

            rlist, wlist, elist = select.select(inputs, outputs, inputs, 1)
            for s in rlist:
                if s == tcp_socket:
                    # TCP incoming connection
                    conn, addr = s.accept()
                    conn.setblocking(False)

                    inputs.append(conn)
                    msg_queue[conn] = Queue()
                    log('TCP connection established', addr, False)

                elif s == udp_socket:
                    # UDP message
                    data, addr = s.recvfrom(RECV_BYTES)
                    udp_handler.handle_message(data, addr)

                else:
                    data = s.recv(RECV_BYTES)
                    addr = s.getpeername()
                    if data:
                        # TCP message
                        response = tcp_handler.handle_message(data,addr)
                        msg_queue[s].put(response)
                        if s not in outputs:
                            outputs.append(s)

                    else:
                        # TCP close
                        log('TCP connection closed', addr, True)

                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        msg_queue.pop(s, None)

            for s in wlist:
                try:
                    payload = msg_queue[s].get_nowait()
                    s.send(payload)
                    outputs.remove(s)
                    msg_queue.pop(s, None)
                except Empty:
                    pass

            for s in elist:
                if s != udp_socket:

                    log(f'TCP connection error {s}', None, True)

                    inputs.remove(s)
                    if s in outputs:
                        outputs.remove(s)

                    msg_queue.pop(s, None)

                    s.close()

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

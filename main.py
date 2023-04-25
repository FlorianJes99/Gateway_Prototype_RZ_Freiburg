#!/usr/bin/env python3

import socket
import logging
import threading  # may use asyncio for multiple connections

HOST = 'localhost'
SERVER_HOST = 'localhost'
LISTENING_PORT = 1234
SERVER_PORT = 5900

logging.basicConfig(level=logging.DEBUG)


def handle(buffer: bytes, src_address: str, src_port: int, dst_address: str, dst_port: int) -> bytes:
    '''
    can read in- and outgoing data. Returns buffer
    '''
    logging.debug(f'{src_address, src_port} -> {dst_address, dst_port} {len(buffer)} bytes on thread {threading.current_thread()}')
    logging.info(f'Number of running threads: {threading.active_count()}')
    return buffer


def send_data_to_server(src: socket.socket, dst: socket.socket):
    '''
    function for handling traffic from client to server
    '''
    src_address, src_port = src.getsockname()
    dst_address, dst_port = dst.getsockname()

    while True:
        try:
            data_buffer = src.recv(4096)
            if len(data_buffer) > 0:
                dst.send(handle(data_buffer, src_address, src_port,
                                dst_address, dst_port))
        except Exception as e:
            logging.error(repr(e))
            break
    src.close()
    dst.close()
    logging.info(f'Connection terminated, closed Sockets: {src, dst}')


def send_data_to_client(src: socket.socket, dst: socket.socket):
    '''
    function for handling traffic from server to client
    '''
    src_address, src_port = src.getsockname()
    dst_address, dst_port = dst.getsockname()

    while True:
        try:
            data_buffer = src.recv(4096)
            if len(data_buffer) > 0:
                dst.send(handle(data_buffer, src_address, src_port,
                                dst_address, dst_port))
        except Exception as e:
            logging.error(repr(e))
            break
    src.close()
    dst.close()
    logging.info(f'Connection terminated, closed Sockets: {src, dst}')


def run_gateway(local_host: str, local_port: int,
                remote_host: str, remote_port: int):
    '''
    starts gateway and creates two seperate thread for bidirectional connection
    '''
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gateway_socket.bind((local_host, local_port))
    gateway_socket.listen(1)
    logging.info(f'Gateway server started {local_host, local_port}')

    known_addresses = set()  # keep clients in view

    while True:
        client_socket, client_address = gateway_socket.accept()  # TODO how to leave this state???
        logging.info(f'Connecting {client_address, client_socket} to {remote_host, remote_port}')
        if client_address not in known_addresses:
            known_addresses.add(client_address)
        try:
            socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_to_server.connect((remote_host, remote_port))
            logging.info('Connection is running')
            server_to_client_thread = threading.Thread(target=send_data_to_client, args=(socket_to_server, client_socket))
            client_to_server_thread = threading.Thread(target=send_data_to_server, args=(client_socket, socket_to_server))
            server_to_client_thread.start()  # TODO instead of a simple while loop implement a thread pool or thread factory
            client_to_server_thread.start()
        except Exception as e:
            logging.error(repr(e))
            break


def main():
    run_gateway(HOST, LISTENING_PORT, SERVER_HOST, SERVER_PORT)


if __name__ == "__main__":
    main()

#!usr/bin/python3
import asyncio
import logging
import time

HOST = ''
SERVER_HOST = 'localhost'
LISTENING_PORT = 1234
SERVER_PORT = 5900
logging.basicConfig(level=logging.DEBUG)


async def send_data(reader: asyncio.StreamReader,
                    writer: asyncio.StreamWriter):
    try:
        while not reader.at_eof():
            writer.write(await reader.read(4096))
    finally:
        writer.close


init_block = True


async def handle_i_o(client_reader: asyncio.StreamReader,
                     client_writer: asyncio.StreamWriter,
                     server_host: str, server_port: int):
    server_reader, server_writer = await asyncio.open_connection(server_host, server_port)
    to_server = send_data(client_reader, server_writer)
    global init_block
    if init_block is True:
        print('Blocking for 60s')
        time.sleep(60)
        print('Blocking done')
        init_block = False
    to_client = send_data(server_reader, client_writer)
    await asyncio.gather(to_server, to_client)


async def gateway_connection(proxy_port: int, server_host: str,
                             server_port: int):
    server = await asyncio.start_server(
        lambda client_reader, client_writer: handle_i_o(client_reader, client_writer, server_host, server_port),
        host='localhost',
        port=proxy_port)
    async with server:
        await server.serve_forever()


def main():
    asyncio.run(gateway_connection(LISTENING_PORT, SERVER_HOST, SERVER_PORT))


if __name__ == "__main__":
    main()

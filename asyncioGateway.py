#!usr/bin/python3
import asyncio
import logging

HOST = 'localhost'
SERVER_HOST = 'localhost'
LISTENING_PORT = 1234
SERVER_PORT = 5900
logging.basicConfig(level=logging.DEBUG)


async def handle_client(client_reader, client_writer, server_host, server_port):
    server_reader, server_writer = await asyncio.open_connection(server_host, server_port)
    while True:
        # Wait for data from the client or server
        client_data = await client_reader.read(4096)
        logging.info(f'Reading from {client_reader}')
        if not client_data:
            break
        server_data = await server_reader.read(4096)
        logging.info(f'Reading from {server_reader}')
        if not server_data:
            break

        # Send data to the other side
        server_writer.write(client_data)
        client_writer.write(server_data)

        await asyncio.gather(client_writer.drain(), server_writer.drain())

    # Close both connections when one is closed
    client_writer.close()
    server_writer.close()


async def run_proxy(proxy_port, server_host, server_port):
    server = await asyncio.start_server(
        lambda client_reader, client_writer: handle_client(client_reader, client_writer, server_host, server_port),
        host='localhost',
        port=proxy_port)
    async with server:
        await server.serve_forever()


def main():
    asyncio.run(run_proxy(LISTENING_PORT, SERVER_HOST, SERVER_PORT))


if __name__ == "__main__":
    main()
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)


class Gateway:
    def __init__(self, host: str, listening_port: int):
        self.host = host
        self.listening_port = listening_port
        self.channels = []

    async def start(self):
        logging.info('Starting gateway...')
        server = await asyncio.start_server(
          self.handle_connection,
          self.host,
          self.listening_port
        )

        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_ip = writer.get_extra_info('peername')[0]
        logging.debug(f'Client ip: {client_ip}')
        server_reader, server_writer = await asyncio.open_connection('localhost', 5900)
        channel = SpiceChannel(reader, writer, server_reader, server_writer)
        to_server = asyncio.create_task(channel.send_to_server())
        to_client = asyncio.create_task(channel.send_to_client())
        # await waits for ever due to server and client streams never ending
        await asyncio.gather(to_server, to_client)


class SpiceChannel:
    def __init__(self, client_reader, client_writer, server_reader, server_writer):
        self.client_reader = client_reader
        self.client_writer = client_writer
        self.server_reader = server_reader
        self.server_writer = server_writer
        self.channel_number = None

    async def send_to_server(self):
        await self.process_data(self.client_reader, self.server_writer)

    async def send_to_client(self):
        await self.process_data(self.server_reader, self.client_writer)

    async def process_data(self, reader, writer):
        try:
            while not reader.at_eof():
                data = await reader.read(1024)
                if self.channel_number is None:
                    self.channel_number = data[20]
                    logging.debug(f'Channel number is: {self.channel_number}')
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logging.error(repr(e))
        finally:
            logging.info('Closing writer')
            writer.close()

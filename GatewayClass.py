import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)


class Gateway:
    def __init__(self, host: str, listening_port: int):
        self.host = host
        self.listening_port = listening_port
        self.client_groups: dict[str:ClientConnection] = {}

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_ip = writer.get_extra_info('peername')

        if client_ip in self.client_groups:
            group: ChannelsClientServer = self.client_groups[client_ip]
        else:
            group = ChannelsClientServer(client_ip)
            self.client_groups[client_ip] = group

        connection = ClientConnection(reader, writer)
        group.add_channel(connection)

        logging.info(f'Creating task for group of channels: {group}')
        asyncio.create_task(group.handle_channel_data('localhost', 5900))

    async def start(self):
        logging.info('Starting gateway...')
        server = await asyncio.start_server(
          self.handle_connection,
          self.host,
          self.listening_port
        )

        async with server:
            await server.serve_forever()


class ChannelsClientServer:
    def __init__(self, ip_adress: str):
        self.ip_adress = ip_adress
        self.channels: list[ClientConnection] = []

    def add_channel(self, channel):
        self.channels.append(channel)

    async def handle_channel_data(self, server_host: str, server_port: int):
        while True:
            for channel in self.channels:
                server_reader, server_writer = await asyncio.open_connection(server_host, server_port)
                logging.debug('Sending to Server...')
                send_to_server = SendData.send_data(channel.reader, server_writer)
                logging.debug('Sending to client...')
                send_to_client = SendData.send_data(server_reader, channel.writer)
                await asyncio.gather(send_to_server, send_to_client)


class ClientConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer


class SendData:
    async def send_data(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while not reader.at_eof():
                writer.write(await reader.read(4096))
        finally:
            writer.close()

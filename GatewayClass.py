from concurrent.futures import ProcessPoolExecutor
from websockets.server import serve
from websockets.client import connect
import asyncio
import time
import logging
logging.basicConfig(level=logging.DEBUG)

INIT_BLOCK = True
BUFFER_SIZE = 2048  # in bytes
SLEEP_TIME = 300  # seconds
WS_MAX_SIZE = None  # keine MAX_SIZE
# read_limit, max_queue und write_limit veraendern fuer performance tests


class GatewayWebsockets(object):
    def __init__(self, host: str, listening_port: int, pool_executor: ProcessPoolExecutor):
        self.host = host
        self.listening_port = listening_port
        self.process_pool_executor = pool_executor

    async def start(self):
        logging.info('Starting gateway...')
        async with serve(self.handle_connection, self.host, self.listening_port, max_size=WS_MAX_SIZE):
            await asyncio.Future()

    async def handle_connection(self, ws_client):
        args = {
                'max_size': WS_MAX_SIZE,
        }
        async with connect('ws://localhost:5900', **args) as ws_server:
            to_server = asyncio.create_task(self.proxy(ws_client, ws_server))
            to_client = asyncio.create_task(self.proxy(ws_server, ws_client))
            await asyncio.gather(to_server, to_client)

    async def proxy(self, ws_in, ws_out):
        async for msg in ws_in:
            await ws_out.send(msg)


class GatewaySockets(object):
    def __init__(self, host: str, listening_port: int, pool_executor: ProcessPoolExecutor):
        self.host = host
        self.listening_port = listening_port
        self.channels = []
        self.process_pool_executor = pool_executor

    async def start(self):
        server = await asyncio.start_server(
          self.handle_connection_,
          self.host,
          self.listening_port,
        )
        await server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_ip = writer.get_extra_info('peername')[0]
        logging.debug(f'Client ip: {client_ip}')
        server_reader, server_writer = await asyncio.open_connection('localhost', 5900)
        channel = SpiceChannel(reader, writer, server_reader, server_writer)
        global INIT_BLOCK
        to_server = asyncio.create_task(channel.send_to_server())
        if INIT_BLOCK is True:
            logging.info(f'Sleeping for {SLEEP_TIME}s')
            time.sleep(SLEEP_TIME)  # simulate api request, which return location of server
            logging.info('Done sleeping')
            INIT_BLOCK = False
        to_client = asyncio.create_task(channel.send_to_client())
        # await waits for ever due to server and client streams never ending
        await asyncio.gather(to_server, to_client)

    async def handle_connection_(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.process_pool_executor, loop.run_until_complete(await self.handle_connection(reader, writer)))


class SpiceChannel(object):
    def __init__(self, client_reader, client_writer, server_reader, server_writer):
        self.client_reader = client_reader
        self.client_writer = client_writer
        self.server_reader = server_reader
        self.server_writer = server_writer
        self.channel_number = None
        self.channel_id = None

    async def send_to_server(self):
        await self.process_data(self.client_reader, self.server_writer)

    async def send_to_client(self):
        await self.process_data(self.server_reader, self.client_writer)

    async def process_data(self, reader, writer):
        try:
            while not reader.at_eof():
                data = await reader.read(BUFFER_SIZE)
                if self.channel_number is None:
                    self.channel_number = data[20]
                    self.channel_id = data[21]
                    logging.debug(f'Channel number, id is: {self.channel_number, self.channel_id}')
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logging.error(repr(e))
        finally:
            logging.info('Closing writer')
            writer.close()
            await writer.wait_closed()

from concurrent.futures import ProcessPoolExecutor
import logging
import GatewayClass
import asyncio
import argparse

HOST = 'localhost'
LISTENING_PORT = 1234
logging.basicConfig(level=logging.INFO)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--websockets', action='store_true', help='Enable websocket support for the gateway')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debugging logs')
    args = parser.parse_args()
    p = ProcessPoolExecutor(10)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.websockets:
        logging.info('Started gateway in websockets mode')
        gateway = GatewayClass.GatewayWebsockets(HOST, LISTENING_PORT, p)
        await gateway.start()
    else:
        logging.info('Started gateway in sockets mode')
        gateway = GatewayClass.GatewaySockets(HOST, LISTENING_PORT, p)
        await gateway.start()


if __name__ == '__main__':
    asyncio.run(main())
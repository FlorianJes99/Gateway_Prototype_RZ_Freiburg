from concurrent.futures import ProcessPoolExecutor
import logging
import GatewayClass
import asyncio
import argparse

HOST = ''
LISTENING_PORT = 1234
logging.basicConfig(level=logging.DEBUG)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--websockets', action='store_true', help='Enable websocket support for the gateway')
    args = parser.parse_args()
    if args.websockets:
        logging.info('Started gateway in websockets mode')
    p = ProcessPoolExecutor(10)
    gateway = GatewayClass.Gateway(HOST, LISTENING_PORT, p, args)
    await gateway.start()


if __name__ == '__main__':
    asyncio.run(main())
import logging
import GatewayClass
import asyncio

HOST = ''
LISTENING_PORT = 1234
logging.basicConfig(level=logging.DEBUG)


async def main():
    gateway = GatewayClass.Gateway(HOST, LISTENING_PORT)
    await gateway.start()


if __name__ == '__main__':
    asyncio.run(main())
#!/usr/bin/env python3

import sys
import asyncio
import argparse
from brutasse.tftp.protocol import Client


async def get(client: Client, filename: str):
    data = await client.get_file(filename)
    sys.stdout.buffer.write(data)


async def put(client: Client, filename: str):
    data = sys.stdin.buffer.read()
    await client.put_file(filename, data)

ACTIONS = {
    'get': get,
    'put': put
}


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=69)
    parser.add_argument('action', choices=ACTIONS)
    parser.add_argument('host', type=str)
    parser.add_argument('filename', type=str)
    return parser.parse_args()


async def main():
    args = get_args()
    async with Client.create(args.host, args.port) as client:
        await ACTIONS[args.action](client, args.filename)

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3

import asyncio
import argparse
import ipaddress
from typing import TextIO
from termcolor import colored
from .proto import BgpStream, Open
from ..utils import tcp_connect, ConnectionFailed
from ..parallel import progressbar_execute


def get_ips(file: TextIO) -> set[str]:
    return {l.strip() for l in file}


async def bgp_open_info(ip: str) -> str:
    reader, writer = await tcp_connect(ip, 179, timeout=2)
    stream = BgpStream(reader, writer)
    try:
        await stream.write_msg(Open(version=4, asn=65000, hold_time=90, bgp_id=ipaddress.IPv4Address('10.10.10.10'), opts=b''))
        msg = await asyncio.wait_for(stream.read_msg(), 1)
        match msg:
            case Open(asn=asn, bgp_id=bgp_id):
                return f'asn={asn} id={bgp_id}'
            case _:
                raise ValueError(f'Unexpected message {msg}')
    finally:
        await stream.close()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('r'))
    args = parser.parse_args()
    coros = [bgp_open_info(ip) for ip in get_ips(args.infile)]
    async for fut in progressbar_execute(coros, 500):
        try:
            res = fut.result()
            print(res)
        except ConnectionFailed:
            pass
        except (asyncio.IncompleteReadError, ConnectionResetError, TimeoutError):
            pass
        except Exception as e:
            print(colored(repr(e), 'red'))

asyncio.run(main())

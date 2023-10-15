#!/usr/bin/env python3

import logging
import asyncio
import argparse
from typing import AsyncGenerator
from ipaddress import IPv4Network, IPv4Address
from .proto import make_v2c_request, make_v3_request, parse_v3_vendor
from ..scan import zmap


async def scan_v2c(ranges: list[IPv4Network], rate: int, community: str) -> AsyncGenerator[IPv4Address, None]:
    payload = make_v2c_request(community)
    async for saddr, _ in zmap.udp_scan(ranges, rate, port=161, payload=payload):
        yield saddr


async def scan_v3(ranges: list[IPv4Network], rate: int) -> AsyncGenerator[tuple[IPv4Address, str], None]:
    payload = make_v3_request()
    async for saddr, data in zmap.udp_scan(ranges, rate, port=161, payload=payload):
        try:
            vendor_num = parse_v3_vendor(data)
            yield saddr, f'1.3.6.1.4.1.{vendor_num}'
        except Exception as e:
            logging.error(e, exc_info=True)


async def main():
    from ..msf.db import Metasploit
    parser = argparse.ArgumentParser()
    parser.add_argument('network', nargs='+', type=IPv4Network)
    parser.add_argument('--msf')
    args = parser.parse_args()
    assert args.msf
    msfdb = Metasploit(args.msf)
    with msfdb.session() as session:
        async for addr, _ in scan_v3(args.network, 10000):
            print(addr)
            host = msfdb.get_or_create_host(session, str(addr))
            _ = msfdb.get_or_create_service(session, host, 'udp', 161)
            session.commit()

asyncio.run(main())

#!/usr/bin/env python3

import logging
from typing import AsyncGenerator
from ipaddress import IPv4Network, IPv4Address
from .proto import make_v2c_request, make_v3_request, parse_v3_vendor, get_v2c_community
from ..scan import zmap


async def scan_v2c(ranges: list[IPv4Network], rate: int, community: str) -> AsyncGenerator[tuple[IPv4Address, str], None]:
    payload = make_v2c_request(community)
    async for saddr, data in zmap.udp_scan(ranges, rate, port=161, payload=payload):
        yield saddr, get_v2c_community(data)


async def scan_v3(ranges: list[IPv4Network], rate: int) -> AsyncGenerator[tuple[IPv4Address, str], None]:
    payload = make_v3_request()
    async for saddr, data in zmap.udp_scan(ranges, rate, port=161, payload=payload):
        try:
            vendor_num = parse_v3_vendor(data)
            yield saddr, f'1.3.6.1.4.1.{vendor_num}'
        except Exception as e:
            logging.error(e, exc_info=True)

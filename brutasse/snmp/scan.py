#!/usr/bin/env python3

import logging
from typing import TypeVar, Optional
from ipaddress import IPv4Network, IPv4Address
from collections.abc import Callable, AsyncIterator
from .proto import (make_v1_request, get_v1_community,
                    make_v2c_request, get_v2c_community,
                    make_v3_request, parse_v3_vendor)
from ..scan import zmap

T = TypeVar('T')


async def snmp_scan_common(ranges: list[IPv4Network], rate: int,
                           payload: bytes, decoder: Callable[[bytes], T]
                           ) -> AsyncIterator[tuple[IPv4Address, T]]:
    scan = zmap.udp_scan(ranges, rate, port=161, payload=payload)
    async for saddr, data in scan:
        try:
            decoded = decoder(data)
            yield saddr, decoded
        except Exception as e:
            logging.error(e, exc_info=True)


def scan_v1(ranges: list[IPv4Network], rate: int, community: str
            ) -> AsyncIterator[tuple[IPv4Address, str]]:
    return snmp_scan_common(ranges, rate,
                            make_v1_request(community), get_v1_community)


def scan_v2c(ranges: list[IPv4Network], rate: int, community: str
             ) -> AsyncIterator[tuple[IPv4Address, str]]:
    return snmp_scan_common(ranges, rate,
                            make_v2c_request(community), get_v2c_community)


def scan_v3(ranges: list[IPv4Network], rate: int
            ) -> AsyncIterator[tuple[IPv4Address, Optional[int]]]:
    return snmp_scan_common(ranges, rate,
                            make_v3_request(), parse_v3_vendor)

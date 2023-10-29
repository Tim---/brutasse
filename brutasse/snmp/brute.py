#!/usr/bin/env python3

from ipaddress import IPv4Address
from typing import AsyncIterable
from ..utils import IPAddress
from ..scan.ip import udp_scan
from .proto import make_v2c_request, get_v2c_community


def pkt_gen(ips: list[IPv4Address], communities: list[str]):
    for community in communities:
        pkt = make_v2c_request(community)
        for ip in ips:
            yield (ip, 161, pkt)


async def brute(ips: list[IPv4Address], communities: list[str]) -> AsyncIterable[tuple[IPAddress, int, str]]:
    async for ip, port, data in udp_scan(pkt_gen(ips, communities)):
        community = get_v2c_community(data)
        yield ip, port, community

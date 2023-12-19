#!/usr/bin/env python3

from typing import AsyncIterable
from ..utils import IPAddress
from ..scan.ip import udp_scan
from .scan import make_v2c_request, get_v2c_community
import progressbar


def pkt_gen(ips: list[IPAddress], communities: list[str]):
    n = len(ips) * len(communities)
    with progressbar.ProgressBar(max_value=n, redirect_stdout=True) as bar:
        i = 0
        for community in communities:
            pkt = make_v2c_request(community)
            for ip in ips:
                yield (ip, 161, pkt)
                i += 1
                bar.update(i)


async def brute(
    ips: list[IPAddress], communities: list[str]
) -> AsyncIterable[tuple[IPAddress, int, str]]:
    async for ip, port, data in udp_scan(pkt_gen(ips, communities)):
        community = get_v2c_community(data)
        yield ip, port, community

#!/usr/bin/env python3

from typing import AsyncIterable

import progressbar

from ..scan import ip_udp_scan
from ..utils import IPAddress
from .scan import get_v2c_community, make_v2c_request


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
    async for ip, port, data in ip_udp_scan(pkt_gen(ips, communities)):
        community = get_v2c_community(data)
        yield ip, port, community

#!/usr/bin/env python3

from typing import AsyncIterable

import progressbar

from brutasse.scan import ip_udp_scan
from brutasse.snmp.scan import get_v2c_community, make_v2c_request
from brutasse.utils import IPAddress


def pkt_gen(addresses: list[IPAddress], communities: list[str]):
    n = len(addresses) * len(communities)
    with progressbar.ProgressBar(max_value=n, redirect_stdout=True) as bar:
        i = 0
        for community in communities:
            pkt = make_v2c_request(community)
            for addr in addresses:
                yield (addr, 161, pkt)
                i += 1
                bar.update(i)


async def bruteforce_communities_v2c(
    addresses: list[IPAddress], communities: list[str]
) -> AsyncIterable[tuple[IPAddress, int, str]]:
    """Bruteforce the communities for the given IPs.

    :param addresses: IP addresses to scan
    :param communities: SNMP communities to try
    :return: an iterator of (IP, port, community)"""
    async for ip, port, data in ip_udp_scan(pkt_gen(addresses, communities)):
        community = get_v2c_community(data)
        yield ip, port, community

#!/usr/bin/env python3

import logging
from ipaddress import IPv4Address, IPv4Network
from typing import AsyncIterator

from brutasse.scan import net_udp_scan
from brutasse.tftp.packet import Msg, ReadRequest


async def tftp_scan(
    ranges: list[IPv4Network], rate: int
) -> AsyncIterator[tuple[IPv4Address, Msg]]:
    req = ReadRequest(filename="iamafilename", mode="octet").build()
    async for saddr, data in net_udp_scan(ranges, rate, port=69, payload=req):
        try:
            pkt = Msg.parse(data)
            yield saddr, pkt
        except Exception as e:
            logging.error(e, exc_info=True)

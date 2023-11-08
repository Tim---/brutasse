#!/usr/bin/env python3

import logging
from typing import AsyncIterator
from ipaddress import IPv4Network, IPv4Address
from .proto import Msg, ReadRequest
from ..scan import zmap


async def tftp_scan(ranges: list[IPv4Network], rate: int
                    ) -> AsyncIterator[tuple[IPv4Address, Msg]]:
    req = ReadRequest(filename='iamafilename', mode='octet').build()
    async for saddr, data in zmap.udp_scan(ranges, rate, port=69, payload=req):
        try:
            pkt = Msg.parse(data)
            yield saddr, pkt
        except Exception as e:
            logging.error(e, exc_info=True)

#!/usr/bin/env python3

import asyncio
import ipaddress

from ..utils import IPAddress, tcp_connect
from .proto import Msg, Notification, Open


async def bgp_open_info(ip: IPAddress, port: int, timeout: int = 2) -> str:
    stream = await tcp_connect(ip, port, timeout=timeout)
    try:
        req = Open(
            version=4,
            asn=65000,
            hold_time=90,
            bgp_id=ipaddress.IPv4Address("10.10.10.10"),
            opts=b"",
        )
        await req.write_stream(stream)

        resp = await asyncio.wait_for(Msg.parse_stream(stream), timeout)
        match resp:
            case Open(asn=asn, bgp_id=bgp_id):
                return f"{ip} asn={asn} id={bgp_id}"
            case Notification(code=6, subcode=5, data=b""):
                raise ConnectionRefusedError(
                    "Peer returned Cease / Connection Rejected"
                )
            case _:
                raise ValueError(f"Unexpected message {resp}")
    finally:
        await stream.close()

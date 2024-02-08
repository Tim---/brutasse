#!/usr/bin/env python3

import asyncio
import ipaddress

from ..utils import IPAddress, tcp_connect
from .proto import BgpStream, Notification, Open


async def bgp_open_info(ip: IPAddress, port: int, timeout: int = 2) -> str:
    reader, writer = await tcp_connect(ip, port, timeout=timeout)
    stream = BgpStream(reader, writer)
    try:
        req = Open(
            version=4,
            asn=65000,
            hold_time=90,
            bgp_id=ipaddress.IPv4Address("10.10.10.10"),
            opts=b"",
        )
        await stream.write_msg(req)

        resp = await asyncio.wait_for(stream.read_msg(), timeout)
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

#!/usr/bin/env python3

import asyncio
import ipaddress
from .proto import BgpStream, Notification, Open
from ..utils import tcp_connect


async def bgp_open_info(ip: str, port: int, timeout: int = 2) -> str:
    reader, writer = await tcp_connect(ip, port, timeout=timeout)
    stream = BgpStream(reader, writer)
    try:
        await stream.write_msg(Open(version=4, asn=65000, hold_time=90, bgp_id=ipaddress.IPv4Address('10.10.10.10'), opts=b''))
        msg = await asyncio.wait_for(stream.read_msg(), timeout)
        match msg:
            case Open(asn=asn, bgp_id=bgp_id):
                return f'asn={asn} id={bgp_id}'
            case Notification(code=6, subcode=5, data=b''):
                raise ConnectionRefusedError(
                    'Peer returned Cease / Connection Rejected')
            case _:
                raise ValueError(f'Unexpected message {msg}')
    finally:
        await stream.close()

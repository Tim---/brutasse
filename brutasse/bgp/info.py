#!/usr/bin/env python3

import asyncio
from ipaddress import IPv4Address

from brutasse.bgp.proto import Msg, Notification, Open
from brutasse.utils import IPAddress, tcp_connect


async def bgp_open_info(
    address: IPAddress, port: int, timeout: int = 2
) -> tuple[int, IPv4Address]:
    """Get the ASN info of a BGP peer.

    :param address: address of the host
    :param port: TCP port
    :param timeout: timeout for TCP connect/packet read
    :return: a tuple of (asn, bgp_id) from the Open message"""
    stream = await tcp_connect(address, port, timeout=timeout)
    try:
        req = Open(
            version=4,
            asn=65000,
            hold_time=90,
            bgp_id=IPv4Address("10.10.10.10"),
            opts=b"",
        )
        await req.write_stream(stream)

        resp = await asyncio.wait_for(Msg.parse_stream(stream), timeout)
        match resp:
            case Open(asn=asn, bgp_id=bgp_id):
                return asn, bgp_id
            case Notification(code=6, subcode=5, data=b""):
                raise ConnectionRefusedError(
                    "Peer returned Cease / Connection Rejected"
                )
            case _:
                raise ValueError(f"Unexpected message {resp}")
    finally:
        await stream.close()

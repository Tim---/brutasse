#!/usr/bin/env python3

import asyncio
from typing import Optional, AsyncGenerator
from collections.abc import Iterable
from typing import Any
from ..utils import IPAddress
import ipaddress

Addr = tuple[IPAddress, int]
Pkt = tuple[IPAddress, int, bytes]


class UdpScanProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue[Optional[Pkt]]):
        self.queue = queue

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        ip, port = addr
        ip = ipaddress.ip_address(ip)
        self.queue.put_nowait((ip, port, data))

    def connection_lost(self, exc: Exception | None) -> None:
        pass


async def producer(transport: asyncio.DatagramTransport, queue: asyncio.Queue[Optional[Pkt]], pkt_gen: Iterable[Pkt], cooldown: float, delay: float = 0.001) -> None:
    for ip, port, data in pkt_gen:
        transport.sendto(data, (str(ip), port))
        await asyncio.sleep(delay)
    await asyncio.sleep(cooldown)
    await queue.put(None)


async def scan(pkt_gen: Iterable[Pkt], cooldown: float = 1) -> AsyncGenerator[Pkt, None]:
    queue: asyncio.Queue[Optional[Pkt]] = asyncio.Queue()

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: UdpScanProtocol(queue),
        local_addr=('0.0.0.0', 0))

    try:
        task = asyncio.create_task(
            producer(transport, queue, pkt_gen, cooldown)
        )
        while item := await queue.get():
            yield item
        await task
    finally:
        transport.close()

#!/usr/bin/env python3

import asyncio
from typing import Optional, Any
from collections.abc import Generator


Addr = tuple[str | Any, int]
Pkt = tuple[str | Any, int, bytes]


class UdpScanProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue[Optional[Pkt]]):
        self.queue = queue

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Addr) -> None:
        ip, port = addr
        self.queue.put_nowait((ip, port, data))

    def connection_lost(self, exc: Exception | None) -> None:
        pass


async def producer(transport: asyncio.DatagramTransport, queue: asyncio.Queue[Optional[Pkt]], pkt_gen: Generator[Pkt, None, None], cooldown: float, delay: float = 0.001) -> None:
    for ip, port, data in pkt_gen:
        transport.sendto(data, (ip, port))
        await asyncio.sleep(delay)
    await asyncio.sleep(cooldown)
    await queue.put(None)


async def scan(pkt_gen: Generator[Pkt, None, None], cooldown: float = 1):
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

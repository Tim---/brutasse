#!/usr/bin/env python3

import asyncio
from typing import Any, Optional

Addr = tuple[str, int]

# TODO: subclassing these classes is really ugly


class ConnectedUdpServerHandler:
    def __init__(self, server: 'ConnectedUdpServerProtocol', addr: Addr,
                 queue: asyncio.Queue[bytes]):
        self.server = server
        self.addr = addr
        self.queue = queue

    async def send_datagram(self, data: bytes) -> None:
        self.server.send_datagram(data, self.addr)

    async def recv_datagram(self) -> bytes:
        return await self.queue.get()

    def datagram_received(self, data: bytes) -> None:
        self.queue.put_nowait(data)

    async def run(self) -> None:
        raise NotImplementedError()


class ConnectedUdpServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.handlers: dict[Addr, ConnectedUdpServerHandler] = {}
        self.queues: dict[Addr, asyncio.Queue[bytes]] = {}

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes,
                          addr: tuple[str | Any, int, int, int]) -> None:
        host, port = addr[0], addr[1]
        assert isinstance(host, str)
        endpoint = (host, port)
        if endpoint not in self.handlers:
            queue: asyncio.Queue[bytes] = asyncio.Queue()
            self.create_handler(endpoint, queue)

        self.handlers[endpoint].datagram_received(data)

    def send_datagram(self, data: bytes, addr: Addr) -> None:
        self.transport.sendto(data, (addr[0], addr[1], 0, 0))

    def remove_handler(self, addr: Addr) -> None:
        handler = self.handlers.pop(addr)
        if not handler.queue.empty():
            # If the client reuses the socket, we may have pending packets
            # in the queue. Create a new handler with the same queue.
            self.create_handler(addr, handler.queue)

    def create_handler(self, addr: Addr, queue: asyncio.Queue[bytes]) -> None:
        handler = self.create_server_handler(addr, queue)
        task = asyncio.create_task(handler.run())
        task.add_done_callback(lambda task: self.remove_handler(addr))
        self.handlers[addr] = handler

    def connection_lost(self, exc: Optional[Exception]):
        # TODO: clean up, wait for handlers ?
        pass

    def create_server_handler(self, addr: Addr, queue: asyncio.Queue[bytes]
                              ) -> ConnectedUdpServerHandler:
        raise NotImplementedError

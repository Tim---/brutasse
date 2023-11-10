#!/usr/bin/env python3

import asyncio
import itertools
import anyio
import contextlib
from collections.abc import Iterator
from anyio.abc import UDPSocket, ConnectedUDPSocket
from .packet import Msg, ReadRequest, WriteRequest, Ack, Error, Data


class Common:
    timeout: float = 1
    retries: int = 1
    block_size: int = 512

    async def send_msg(self, msg: Msg) -> None:
        raise NotImplementedError

    async def recv_msg(self) -> Msg:
        raise NotImplementedError

    async def send_receive(self, msg: Msg) -> Msg:
        for _ in range(self.retries + 1):
            await self.send_msg(msg)

            try:
                resp = await asyncio.wait_for(self.recv_msg(), self.timeout)
                return resp
            except TimeoutError:
                continue
        raise TimeoutError('Max retries exceeded')

    def check_resp_data(self, resp: Msg, expected_block: int) -> bytes:
        match resp:
            case Error(code, msg):
                raise Exception(f'Peer returned tftp error {code}: {msg}')
            case Data(block_num, data) if block_num == expected_block:
                return data
            case _:
                raise NotImplementedError(
                    f'Unexpected response {resp}')

    def check_resp_ack(self, resp: Msg, expected_block: int) -> None:
        match resp:
            case Error(code, msg):
                raise Exception(f'Peer returned tftp error {code}: {msg}')
            case Ack(block_num) if block_num == expected_block:
                pass
            case _:
                raise NotImplementedError(
                    f'Unexpected response {resp}')

    async def recv_data(self, first_resp: Msg) -> bytes:
        res = bytearray()
        resp = first_resp

        for expected_block in itertools.count(1):
            data = self.check_resp_data(resp, expected_block)
            res += data

            if len(data) == self.block_size:
                resp = await self.send_receive(Ack(block_num=expected_block))
            else:
                await self.send_msg(Ack(block_num=expected_block))
                break

        return bytes(res)

    def chunkify(self, data: bytes) -> Iterator[bytes]:
        for i in range(0, len(data)+1, self.block_size):
            yield data[i:i+self.block_size]

    async def send_data(self, data: bytes) -> None:
        for send_block, block in zip(itertools.count(1), self.chunkify(data)):
            req = Data(send_block, block)
            resp = await self.send_receive(req)
            self.check_resp_ack(resp, send_block)


class Client(Common):
    def __init__(self, udp: ConnectedUDPSocket):
        self.udp = udp

    async def send_msg(self, msg: Msg) -> None:
        raw = msg.build()
        return await self.udp.send(raw)

    async def recv_msg(self) -> Msg:
        raw = await self.udp.receive()
        return Msg.parse(raw)

    async def get_file(self, filename: str, mode: str = 'netascii') -> bytes:
        req = ReadRequest(filename=filename, mode=mode)
        resp = await self.send_receive(req)
        return await self.recv_data(resp)

    async def put_file(self, filename: str, data: bytes,
                       mode: str = 'netascii') -> None:
        req = WriteRequest(filename=filename, mode=mode)
        resp = await self.send_receive(req)
        self.check_resp_ack(resp, 0)
        await self.send_data(data)

    @classmethod
    @contextlib.asynccontextmanager
    async def create(cls, host: str, port: int = 69):
        async with await anyio.create_connected_udp_socket(host, port) as udp:
            yield cls(udp)


Addr = tuple[str, int]


class ServerHandler(Common):
    def __init__(self, server: 'Server', addr: Addr,
                 queue: asyncio.Queue[bytes]):
        self.server = server
        self.addr = addr
        self.queue = queue

    async def send_msg(self, msg: Msg) -> None:
        await self.server.send_datagram(msg.build(), self.addr)

    async def recv_msg(self) -> Msg:
        return Msg.parse(await self.queue.get())

    async def datagram_received(self, data: bytes) -> None:
        await self.queue.put(data)

    async def run(self) -> None:
        msg = await self.recv_msg()
        match msg:
            case ReadRequest():
                dummy_data = b'A' * 4096
                await self.send_data(dummy_data)
            case WriteRequest():
                resp = await self.send_receive(Ack(0))
                await self.recv_data(resp)
            case _:
                raise ValueError(f'Unexpected message {msg}')


class Server:
    def __init__(self, udp: UDPSocket):
        self.udp = udp
        self.handlers: dict[Addr, ServerHandler] = {}
        self.queues: dict[Addr, asyncio.Queue[Msg]] = {}

    async def send_datagram(self, data: bytes, addr: Addr) -> None:
        await self.udp.sendto(data, addr[0], addr[1])

    def remove_handler(self, addr: Addr) -> None:
        handler = self.handlers.pop(addr)
        if not handler.queue.empty():
            # If the client reuses the socket, we may have pending packets
            # in the queue. Create a new handler with the same queue.
            self.create_handler(addr, handler.queue)

    def create_handler(self, addr: Addr, queue: asyncio.Queue[bytes]) -> None:
        handler = ServerHandler(self, addr, queue)
        task = asyncio.create_task(handler.run())
        task.add_done_callback(lambda task: self.remove_handler(addr))
        self.handlers[addr] = handler

    async def datagram_received(self, data: bytes, addr: Addr) -> None:
        if addr not in self.handlers:
            queue: asyncio.Queue[bytes] = asyncio.Queue()
            self.create_handler(addr, queue)

        await self.handlers[addr].datagram_received(data)

    async def run(self) -> None:
        async for raw, addr in self.udp:
            await self.datagram_received(raw, addr)

    @classmethod
    @contextlib.asynccontextmanager
    async def create(cls, host: str = '::', port: int = 69):
        async with await anyio.create_udp_socket(local_host=host,
                                                 local_port=port,
                                                 reuse_port=True) as udp:
            yield cls(udp)

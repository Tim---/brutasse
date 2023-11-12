#!/usr/bin/env python3

import asyncio
import itertools
import contextlib
import anyio
from collections.abc import Iterator
from anyio.abc import ConnectedUDPSocket
from .packet import Msg, ReadRequest, WriteRequest, Ack, Error, Data, ErrorCode
from ..udp import ConnectedUdpServerProtocol, ConnectedUdpServerHandler, Addr


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


class TftpRequest:
    def __init__(self, filename: str, mode: str):
        self.filename = filename
        self.mode = mode
        self.accepted: asyncio.Future[bool] = asyncio.Future()

    async def refuse(self) -> None:
        self.accepted.set_result(False)

    async def is_accepted(self):
        return await self.accepted


class TftpReadRequest(TftpRequest):
    async def accept(self, data: bytes) -> None:
        self.data = data
        self.accepted.set_result(True)

    def get_data(self) -> bytes:
        return self.data


class TftpWriteRequest(TftpRequest):
    def __init__(self, filename: str, mode: str):
        super().__init__(filename, mode)
        self.data: asyncio.Future[bytes] = asyncio.Future()

    async def accept(self) -> bytes:
        self.accepted.set_result(True)
        return await self.data

    def set_data(self, data: bytes) -> None:
        self.data.set_result(data)


class RequestHandler:
    async def on_read_request(self, req: TftpReadRequest) -> None:
        raise NotImplementedError

    async def on_write_request(self, req: TftpWriteRequest) -> None:
        raise NotImplementedError


class TftpServerHandler(ConnectedUdpServerHandler, Common):
    def __init__(self, server: 'ConnectedUdpServerProtocol', addr: Addr,
                 queue: asyncio.Queue[bytes],
                 request_handler: RequestHandler):
        super().__init__(server, addr, queue)
        self.request_handler = request_handler

    async def send_msg(self, msg: Msg) -> None:
        await self.send_datagram(msg.build())

    async def recv_msg(self) -> Msg:
        return Msg.parse(await self.recv_datagram())

    async def handle_read_request(self, filename: str, mode: str) -> None:
        req = TftpReadRequest(filename, mode)
        task = asyncio.create_task(self.request_handler.on_read_request(req))
        if await req.is_accepted():
            data = req.get_data()
            await self.send_data(data)
        else:
            await self.send_msg(Error(ErrorCode.NOT_DEFINED, 'oh noes'))
        await task

    async def handle_write_request(self, filename: str, mode: str) -> None:
        req = TftpWriteRequest(filename, mode)
        task = asyncio.create_task(self.request_handler.on_write_request(req))
        if await req.is_accepted():
            resp = await self.send_receive(Ack(0))
            data = await self.recv_data(resp)
            req.set_data(data)
        else:
            await self.send_msg(Error(ErrorCode.NOT_DEFINED, 'oh noes'))
        await task

    async def run(self) -> None:
        msg = await self.recv_msg()
        match msg:
            case ReadRequest(filename, mode):
                await self.handle_read_request(filename, mode)
            case WriteRequest(filename, mode):
                await self.handle_write_request(filename, mode)
            case _:
                raise ValueError(f'Unexpected message {msg}')


class TftpServerProtocol(ConnectedUdpServerProtocol):
    def __init__(self, request_handler: RequestHandler):
        super().__init__()
        self.request_handler = request_handler

    def create_server_handler(self, addr: Addr, queue: asyncio.Queue[bytes]
                              ) -> ConnectedUdpServerHandler:
        return TftpServerHandler(self, addr, queue, self.request_handler)

#!/usr/bin/env python3

import asyncio
import itertools
from collections.abc import Iterator
from anyio.abc import ConnectedUDPSocket
from .packet import Msg, ReadRequest, WriteRequest, Error, Data, Ack


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

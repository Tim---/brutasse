#!/usr/bin/env python3

import asyncio
import itertools
from collections.abc import AsyncIterator
from anyio.abc import ConnectedUDPSocket
from .proto import Msg, ReadRequest, Error, Data, Ack


class Client:
    def __init__(self, udp: ConnectedUDPSocket,
                 timeout: float = 1, retries: int = 1):
        self.udp = udp
        self.timeout = timeout
        self.retries = retries

    async def send_msg(self, msg: Msg) -> None:
        raw = msg.build()
        return await self.udp.send(raw)

    async def recv_msg(self) -> Msg:
        raw = await self.udp.receive()
        return Msg.parse(raw)

    async def send_receive(self, msg: Msg):
        for _ in range(self.retries + 1):
            await self.send_msg(msg)

            try:
                resp = await asyncio.wait_for(self.recv_msg(), self.timeout)
                return resp
            except TimeoutError:
                continue
        raise TimeoutError('Max retries exceeded')

    async def get_file_blocks(self, filename: str, mode: str = 'netascii'
                              ) -> AsyncIterator[bytes]:
        req = ReadRequest(filename=filename, mode=mode)
        resp = await self.send_receive(req)

        for expected_block in itertools.count(1):
            match resp:
                case Error(code, msg):
                    raise Exception(f'Peer returned tftp error {code}: {msg}')
                case Data(block_num, data) if block_num == expected_block:
                    pass
                case _:
                    raise NotImplementedError(
                        f'Unexpected response {resp}')

            yield data
            if len(data) == 512:
                resp = await self.send_receive(Ack(block_num=expected_block))
            else:
                await self.send_msg(Ack(block_num=expected_block))
                return

    async def get_file(self, filename: str, mode: str = 'netascii') -> bytes:
        return b''.join([block async for block
                         in self.get_file_blocks(filename, mode)])

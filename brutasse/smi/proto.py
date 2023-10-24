#!/usr/bin/env python3

import struct
import asyncio
from dataclasses import dataclass
from typing import Self, Any
import enum


class From(enum.IntEnum):
    IBD_CLI = 1
    IBD_SERV = 2
    IBC_CLI = 3
    IBC_SERV = 4


class Msg:
    repo: dict[tuple[From, int], type['Msg']] = {}
    from_: From
    type_id: int

    def __init_subclass__(cls, /, from_: From, type_id: int, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        Msg.repo[from_, type_id] = cls
        cls.from_ = from_
        cls.type_id = type_id

    def build(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        raise NotImplementedError


# Messages from Director


@dataclass
class CapabilitiesReq(Msg, from_=From.IBD_CLI, type_id=4):
    a: int
    b: int

    def build(self) -> bytes:
        return struct.pack('!II', self.a, self.b)

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        a, b = struct.unpack('!II', raw)
        return cls(a, b)


# Messages from Client

@dataclass
class CapabilitiesResp(Msg, from_=From.IBC_SERV, type_id=3):
    a: int  # constant 1 ?
    b: int  # constant 0 ?

    def build(self) -> bytes:
        return struct.pack('!II', self.a, self.b)

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        a, b = struct.unpack('!II', raw)
        return cls(a, b)


@dataclass
class Pkt:
    version: int
    body: Msg

    @classmethod
    async def parse_stream(cls, reader: asyncio.StreamReader) -> Self:
        raw_hdr = await reader.readexactly(0x10)
        from_, version, type_, size = struct.unpack('!IIII', raw_hdr)
        raw_body = await reader.readexactly(size)

        body = Msg.repo[From(from_), type_].parse(raw_body)
        return cls(version, body)

    async def build_stream(self, writer: asyncio.StreamWriter) -> None:
        raw_body = self.body.build()
        raw_hdr = struct.pack('!IIII', int(self.body.from_),
                              self.version, self.body.type_id, len(raw_body))
        writer.write(raw_hdr + raw_body)
        await writer.drain()


class SmiStream:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read_msg(self) -> Pkt:
        return await Pkt.parse_stream(self.reader)

    async def write_msg(self, msg: Pkt) -> None:
        return await msg.build_stream(self.writer)

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()

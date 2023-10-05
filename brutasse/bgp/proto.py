#!/usr/bin/env python3

import asyncio
import struct
import ipaddress
from dataclasses import dataclass
from typing import Self, Any


class Msg:
    repo: dict[int, type['Msg']] = {}
    type_id: int

    def __init_subclass__(cls, /, type_id: int, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        Msg.repo[type_id] = cls
        cls.type_id = type_id

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        raise NotImplementedError

    def build(self) -> bytes:
        raise NotImplementedError

    @classmethod
    async def parse_stream(cls, reader: asyncio.StreamReader) -> 'Msg':
        raw_hdr = await reader.readexactly(0x13)
        marker, length, type_ = struct.unpack('!16sHB', raw_hdr)
        assert marker == b'\xff' * 16
        raw_body = await reader.readexactly(length - 0x13)
        msg = Msg.repo[type_].parse(raw_body)
        return msg

    async def write_stream(self, writer: asyncio.StreamWriter) -> None:
        marker = b'\xff' * 16
        body = self.build()
        raw = struct.pack('!16sHB', marker, 0x13 + len(body), self.type_id)
        writer.write(raw + body)
        await writer.drain()


@dataclass
class Open(Msg, type_id=1):
    version: int
    asn: int
    hold_time: int
    bgp_id: ipaddress.IPv4Address
    opts: bytes  # TODO

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        version, asn, hold_time, bgp_id, opt_parm_len = struct.unpack(
            '!BHHIB', raw[:10]
        )
        raw_opts = raw[10:]
        assert len(raw_opts) == opt_parm_len
        return cls(version, asn, hold_time, ipaddress.IPv4Address(bgp_id), raw_opts)

    def build(self) -> bytes:
        hdr = struct.pack('!BHHIB', self.version, self.asn,
                          self.hold_time, int(self.bgp_id), 0)
        return hdr


@dataclass
class Update(Msg, type_id=2):
    data: bytes  # TODO

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        return cls(raw)

    def build(self) -> bytes:
        return self.data


@dataclass
class Notification(Msg, type_id=3):
    code: int
    subcode: int
    data: bytes  # TODO

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        code, subcode = struct.unpack('!BB', raw[:2])
        data = raw[2:]
        return cls(code, subcode, data)

    def build(self) -> bytes:
        hdr = struct.pack('!BB', self.code, self.subcode)
        return hdr + self.data


@dataclass
class Keepalive(Msg, type_id=4):
    @classmethod
    def parse(cls, raw: bytes) -> Self:
        assert not raw
        return cls()

    def build(self) -> bytes:
        return b''


class BgpStream:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read_msg(self) -> Msg:
        return await Msg.parse_stream(self.reader)

    async def write_msg(self, msg: Msg) -> None:
        return await msg.write_stream(self.writer)

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()

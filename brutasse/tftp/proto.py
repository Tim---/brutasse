#!/usr/bin/env python3

import struct
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
        op, = struct.unpack('!H', raw[:2])
        return cls.repo[op].parse_msg(raw[2:])

    def build(self) -> bytes:
        return struct.pack('!H', self.type_id) + self.build_msg()

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        raise NotImplementedError

    def build_msg(self) -> bytes:
        raise NotImplementedError


@dataclass
class ReadRequest(Msg, type_id=1):
    filename: str
    mode: str

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        filename, mode, rest = raw.split(b'\0')
        assert not rest
        return cls(filename.decode(), mode.decode())

    def build_msg(self) -> bytes:
        return f'{self.filename}\0{self.mode}\0'.encode()


@dataclass
class WriteRequest(Msg, type_id=2):
    filename: str
    mode: str

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        filename, mode, rest = raw.split(b'\0')
        assert not rest
        return cls(filename.decode(), mode.decode())

    def build_msg(self) -> bytes:
        return f'{self.filename}\0{self.mode}\0'.encode()


@dataclass
class Data(Msg, type_id=3):
    block_num: int
    data: bytes

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        block_num, = struct.unpack('!H', raw[:2])
        return cls(block_num, raw[2:])

    def build_msg(self) -> bytes:
        return struct.pack('!H', self.block_num) + self.data


@dataclass
class Ack(Msg, type_id=4):
    block_num: int

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        block_num, = struct.unpack('!H', raw)
        return cls(block_num)

    def build_msg(self) -> bytes:
        return struct.pack('!H', self.block_num)


@dataclass
class Error(Msg, type_id=5):
    code: int
    msg: str

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        code, = struct.unpack('!H', raw[:2])
        msg = raw[2:]
        assert msg[-1] == 0
        return cls(code, msg[:-1].decode())

    def build_msg(self) -> bytes:
        return struct.pack('!H', self.code) + f'{self.msg}\0'.encode()

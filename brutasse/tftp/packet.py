#!/usr/bin/env python3

import struct
import enum
from dataclasses import dataclass
from typing import Self, Any


class Msg:
    repo: dict[int, type["Msg"]] = {}
    type_id: int

    def __init_subclass__(cls, /, type_id: int, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        Msg.repo[type_id] = cls
        cls.type_id = type_id

    @classmethod
    def parse(cls, raw: bytes) -> "Msg":
        (op,) = struct.unpack("!H", raw[:2])
        return cls.repo[op].parse_msg(raw[2:])

    def build(self) -> bytes:
        return struct.pack("!H", self.type_id) + self.build_msg()

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        raise NotImplementedError

    def build_msg(self) -> bytes:
        raise NotImplementedError


@dataclass
class _Request:
    filename: str
    mode: str

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        filename, mode, opts = raw.split(b"\0", 2)
        assert not opts  # TODO: options
        return cls(filename.decode(), mode.decode())

    def build_msg(self) -> bytes:
        return f"{self.filename}\0{self.mode}\0".encode()


class ReadRequest(_Request, Msg, type_id=1):
    pass


class WriteRequest(_Request, Msg, type_id=2):
    pass


@dataclass
class Data(Msg, type_id=3):
    block_num: int
    data: bytes

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        (block_num,) = struct.unpack("!H", raw[:2])
        return cls(block_num, raw[2:])

    def build_msg(self) -> bytes:
        return struct.pack("!H", self.block_num) + self.data


@dataclass
class Ack(Msg, type_id=4):
    block_num: int

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        (block_num,) = struct.unpack("!H", raw)
        return cls(block_num)

    def build_msg(self) -> bytes:
        return struct.pack("!H", self.block_num)


class ErrorCode(enum.IntEnum):
    NOT_DEFINED = 0
    FILE_NOT_FOUND = 1
    ACCESS_VIOLATION = 2
    DISK_FULL = 3
    ILLEGAL_OPERATION = 4
    UNKNOWN_TRANSFER_ID = 5
    FILE_EXISTS = 6
    NO_SUCH_USER = 7


@dataclass
class Error(Msg, type_id=5):
    code: ErrorCode
    msg: str

    @classmethod
    def parse_msg(cls, raw: bytes) -> Self:
        (code,) = struct.unpack("!H", raw[:2])
        msg = raw[2:]
        assert msg[-1] == 0
        return cls(ErrorCode(code), msg[:-1].decode())

    def build_msg(self) -> bytes:
        return struct.pack("!H", self.code) + f"{self.msg}\0".encode()

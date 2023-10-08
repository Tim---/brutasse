#!/usr/bin/env python3

import struct
from dataclasses import dataclass
from typing import Self


@dataclass
class Pkt:
    seq: int
    msg_cls: int
    body: bytes

    @classmethod
    def parse(cls, raw: bytes) -> Self:
        version, reserved, seq, msg_cls = struct.unpack('!BBBB', raw[:4])
        body = raw[4:]
        assert version == 6
        assert reserved == 0
        return cls(seq, msg_cls, body)

    def build(self) -> bytes:
        return struct.pack('!BBBB', 6, 0, self.seq, self.msg_cls) + self.body

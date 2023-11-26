#!/usr/bin/env python3

from typing import Optional
from ..common import Tag, TagClass, Identifier


class InStream:
    def __init__(self, data: bytes):
        self.cursor = 0
        self.data = data

    def read_bytes(self, size: int) -> bytes:
        res = self.data[self.cursor:self.cursor+size]
        assert len(res) == size
        self.cursor += size
        return res

    def is_eof(self) -> bool:
        return self.cursor == len(self.data)

    def read_byte(self) -> int:
        b, = self.read_bytes(1)
        return b

    def read_integer(self, size: int):
        return int.from_bytes(self.read_bytes(size), 'big')

    def read_base128(self) -> int:
        n = 0
        while True:
            b = self.read_byte()
            n = (n * 0x80) + (b & 0x7f)
            if not b & 0x80:
                return b

    def parse_identifier(self) -> Identifier:
        identifier = self.read_byte()

        tag_number = identifier & 0x1f
        if tag_number == 0x1f:
            tag_number = self.read_base128()

        id_ = Identifier(TagClass(identifier >> 6), bool(
            identifier & 0x20), tag_number)

        return id_

    def parse_length(self, constructed: bool) -> Optional[int]:
        length = self.read_byte()

        if constructed and length == 0x80:
            return None

        if length & 0x80:
            length_length = length & 0x7f
            length = self.read_integer(length_length)
        return length

    def parse_tags(self) -> list[Tag]:
        res: list[Tag] = []
        while not self.is_eof():
            id_ = self.parse_identifier()

            length = self.parse_length(id_.constructed)

            if length is None:
                data = self.parse_tags()
            elif id_.constructed:
                data = parse_ber_tags(self.read_bytes(length))
            else:
                data = self.read_bytes(length)

            if id_ == Identifier(TagClass.UNIVERSAL, False, 0) and data == b'':
                break

            res.append((id_, data))
        return res


class OutStream:
    def __init__(self):
        self.buffer = bytearray()

    def write_bytes(self, raw: bytes) -> None:
        self.buffer.extend(raw)

    def write_byte(self, b: int) -> None:
        self.write_bytes(bytes([b]))

    def write_base128(self, n: int) -> None:
        l: list[int] = []
        high_bit = 0
        while n or not high_bit:
            n, mod = divmod(n, 0x80)
            l.append(high_bit | mod)
            high_bit = 0x80
        self.write_bytes(bytes(l[::-1]))

    def build_identifier(self, identifier: Identifier) -> None:
        tag_number = identifier.number
        if tag_number >= 0x20:
            tag_number = 0x1f

        b = ((identifier.class_ << 6)
             + identifier.constructed * 0x20
             + tag_number)

        self.write_byte(b)
        if tag_number == 0x1f:
            self.write_base128(identifier.number)

    def build_length(self, length: int) -> None:
        if length >= 0x80:
            length_length = (length.bit_length() + 7) // 8
            self.write_bytes(length.to_bytes(length_length, 'big'))
        else:
            self.write_byte(length)

    def build_stream(self, tags: list[Tag]) -> None:
        for identifier, content in tags:
            self.build_identifier(identifier)
            match content:
                case bytes():
                    data = content
                case list():
                    data = build_ber_tags(content)
            self.build_length(len(data))
            self.write_bytes(data)


def build_ber_tags(tags: list[Tag]) -> bytes:
    stream = OutStream()
    stream.build_stream(tags)
    return bytes(stream.buffer)


def parse_ber_tags(raw: bytes) -> list[Tag]:
    stream = InStream(raw)
    res = stream.parse_tags()
    assert stream.is_eof()
    return res

#!/usr/bin/env python3

from typing import Optional
from typing import overload, TypeVar
from types import UnionType, GenericAlias
from .base import (Tag, TagClass, Identifier,
                   Sequence, ObjectIdentifier, Integer,
                   OctetString, Null, BaseType)

# Framing


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

# Encoding


T = BaseType | list['T']


def build_oid(obj: ObjectIdentifier) -> bytes:
    stream = OutStream()
    first, second, *rest = obj
    stream.write_byte(first * 40 + second)
    for suboid in rest:
        stream.write_base128(suboid)
    return bytes(stream.buffer)


def parse_oid(raw: bytes) -> ObjectIdentifier:
    stream = InStream(raw)
    first_two = stream.read_byte()
    first, second = divmod(first_two, 0x40)  # TODO: nope !
    l: list[int] = [first, second]
    while not stream.is_eof():
        l.append(stream.read_base128())
    assert stream.is_eof()
    return ObjectIdentifier(l)


def parse(tag: Tag, cls: UnionType | GenericAlias | type[T]) -> T:
    identifier, data = tag

    if isinstance(cls, UnionType):
        # Union
        for subcls in cls.__args__:
            assert issubclass(subcls, BaseType)
            if subcls.identifier == identifier:
                return parse(tag, subcls)
        else:
            raise NotImplementedError()
    elif isinstance(cls, GenericAlias):
        # Sequence Of
        assert isinstance(data, list)
        assert cls.__origin__ == list
        subcls, = cls.__args__
        return [parse(subtag, subcls) for subtag in data]

    assert identifier == cls.identifier
    if issubclass(cls, Sequence):
        assert isinstance(data, list)
        return cls(**{
            name: parse(subtag, field.type)
            for (name, field), subtag
            in zip(cls.__dataclass_fields__.items(), data)
        })

    assert isinstance(data, bytes)
    if issubclass(cls, ObjectIdentifier):
        return parse_oid(data)
    elif issubclass(cls, Integer):
        n = int.from_bytes(data, 'big', signed=True)
        return cls(n)
    elif issubclass(cls, OctetString):
        return cls(data)
    elif issubclass(cls, Null):
        assert data == b''
        return cls()

    raise NotImplementedError(f'{cls}')


A = Sequence | ObjectIdentifier | Integer | OctetString | Null
U = A | list['U']


def build_univ(obj: A) -> bytes | list['Tag']:
    match obj:
        case Sequence():
            return list(map(build, obj.__dict__.values()))
        case ObjectIdentifier():
            return build_oid(obj)
        case Integer():
            length = (obj + (obj < 0)).bit_length() // 8 + 1
            return obj.to_bytes(length, 'big')
        case OctetString():
            return bytes(obj)
        case Null():
            return b''
    raise NotImplementedError()


def build(obj: U) -> Tag:
    if isinstance(obj, list):
        return (
            Identifier(TagClass.UNIVERSAL, True, 16),
            [build(sub) for sub in obj],
        )
    return obj.identifier, build_univ(obj)


# Public API

Q = TypeVar('Q', bound=BaseType)
@overload
def ber_parse(raw: bytes, cls: type[Q]) -> Q: ...


def ber_parse(raw: bytes, cls: UnionType | GenericAlias | type[T]) -> T:
    tag, = parse_ber_tags(raw)
    return parse(tag, cls)


def ber_build(obj: U) -> bytes:
    tag = build(obj)
    return build_ber_tags([tag])

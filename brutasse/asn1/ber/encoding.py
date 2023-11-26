#!/usr/bin/env python3

from types import UnionType, GenericAlias
from ..common import Tag, Identifier, TagClass
from ..univ import (Sequence, ObjectIdentifier, Integer,
                    OctetString, Null, Asn1Type)
from .framing import InStream, OutStream

T = Asn1Type | list['T']


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
            assert issubclass(subcls, Asn1Type)
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
            name: parse(subtag, subcls)
            for (name, subcls), subtag
            in zip(cls.__annotations__.items(), data)
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

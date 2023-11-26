#!/usr/bin/env python3

from typing import Self
from .common import Identifier, TagClass


class Asn1Type:
    pass


class Sequence(Asn1Type):
    identifier = Identifier(TagClass.UNIVERSAL, True, 16)


class ObjectIdentifier(tuple[int, ...], Asn1Type):
    identifier = Identifier(TagClass.UNIVERSAL, False, 6)

    @classmethod
    def from_string(cls, s: str) -> Self:
        return cls(list(map(int, s.split('.'))))


class Integer(int, Asn1Type):
    identifier = Identifier(TagClass.UNIVERSAL, False, 2)


class OctetString(bytes, Asn1Type):
    identifier = Identifier(TagClass.UNIVERSAL, False, 4)


class Null(Asn1Type):
    identifier = Identifier(TagClass.UNIVERSAL, False, 5)

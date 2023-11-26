#!/usr/bin/env python3

from . import univ
from .common import Identifier, TagClass


Integer = univ.Integer
Integer32 = univ.Integer
OctetString = univ.OctetString


class IpAddress(univ.OctetString):
    identifier = Identifier(TagClass.APPLICATION, False, 0)


class Counter32(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 1)


class Unsigned32(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 2)


class TimeTicks(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 3)


class Opaque(univ.OctetString):
    identifier = Identifier(TagClass.APPLICATION, False, 4)


class Counter64(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 6)


class Bits(univ.OctetString):
    pass


class ObjectName(univ.ObjectIdentifier):
    pass


SimpleSyntax = Integer | OctetString | univ.ObjectIdentifier

ApplicationSyntax = (IpAddress | Counter32 | TimeTicks |
                     Opaque | Counter64 | Unsigned32)

ObjectSyntax = SimpleSyntax | ApplicationSyntax

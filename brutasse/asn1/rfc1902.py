#!/usr/bin/env python3

from .base import TagClass, identifier, Integer, OctetString, ObjectIdentifier

Integer32 = Integer
OctetString = OctetString


@identifier(TagClass.APPLICATION, 0)
class IpAddress(OctetString):
    pass


@identifier(TagClass.APPLICATION, 1)
class Counter32(Integer):
    pass


@identifier(TagClass.APPLICATION, 2)
class Unsigned32(Integer):
    pass


@identifier(TagClass.APPLICATION, 3)
class TimeTicks(Integer):
    pass


@identifier(TagClass.APPLICATION, 4)
class Opaque(OctetString):
    pass


@identifier(TagClass.APPLICATION, 6)
class Counter64(Integer):
    pass


ObjectName = ObjectIdentifier

SimpleSyntax = Integer | OctetString | ObjectIdentifier

ApplicationSyntax = (IpAddress | Counter32 | TimeTicks |
                     Opaque | Counter64 | Unsigned32)

ObjectSyntax = SimpleSyntax | ApplicationSyntax

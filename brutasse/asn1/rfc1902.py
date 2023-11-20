#!/usr/bin/env python3

from . import univ


Integer = univ.Integer
Integer32 = univ.Integer
OctetString = univ.OctetString


class IpAddress(univ.OctetString):
    pass


class Counter32(univ.Integer):
    pass


class Gauge32(univ.Integer):
    pass


class Unsigned32(univ.Integer):
    pass


class TimeTicks(univ.Integer):
    pass


class Opaque(univ.OctetString):
    pass


class Counter64(univ.Integer):
    pass


class Bits(univ.OctetString):
    pass


class ObjectName(univ.ObjectIdentifier):
    pass


SimpleSyntax = Integer | OctetString | univ.ObjectIdentifier

ApplicationSyntax = (IpAddress | Counter32 | TimeTicks |
                     Opaque | Counter64 | Gauge32)

ObjectSyntax = SimpleSyntax | ApplicationSyntax

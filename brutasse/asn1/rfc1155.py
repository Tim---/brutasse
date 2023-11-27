#!/usr/bin/env python3

from .base import (TagClass, ObjectIdentifier, Integer,
                   OctetString, Null, identifier)

ObjectName = ObjectIdentifier

SimpleSyntax = Integer | OctetString | ObjectIdentifier | Null


@identifier(TagClass.APPLICATION, 0)
class IpAddress(OctetString):
    pass


NetworkAddress = IpAddress


@identifier(TagClass.APPLICATION, 1)
class Counter(Integer):
    pass


@identifier(TagClass.APPLICATION, 2)
class Gauge(Integer):
    pass


@identifier(TagClass.APPLICATION, 3)
class TimeTicks(Integer):
    pass


@identifier(TagClass.APPLICATION, 4)
class Opaque(OctetString):
    pass


ApplicationSyntax = NetworkAddress | Counter | Gauge | TimeTicks | Opaque

ObjectSyntax = SimpleSyntax | ApplicationSyntax

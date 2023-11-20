#!/usr/bin/env python3

from . import univ

ObjectName = univ.ObjectIdentifier

SimpleSyntax = (univ.Integer | univ.OctetString |
                univ.ObjectIdentifier | univ.Null)


class IpAddress(univ.OctetString):
    pass


NetworkAddress = IpAddress


class Counter(univ.Integer):
    pass


class Gauge(univ.Integer):
    pass


class TimeTicks(univ.Integer):
    pass


class Opaque(univ.OctetString):
    pass


ApplicationSyntax = NetworkAddress | Counter | Gauge | TimeTicks | Opaque

ObjectSyntax = SimpleSyntax | ApplicationSyntax

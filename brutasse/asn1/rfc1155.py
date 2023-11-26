#!/usr/bin/env python3

from . import univ
from .common import Identifier, TagClass

ObjectName = univ.ObjectIdentifier

SimpleSyntax = (univ.Integer | univ.OctetString |
                univ.ObjectIdentifier | univ.Null)


class IpAddress(univ.OctetString):
    identifier = Identifier(TagClass.APPLICATION, False, 0)


NetworkAddress = IpAddress


class Counter(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 1)


class Gauge(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 2)


class TimeTicks(univ.Integer):
    identifier = Identifier(TagClass.APPLICATION, False, 3)


class Opaque(univ.OctetString):
    identifier = Identifier(TagClass.APPLICATION, False, 4)


ApplicationSyntax = NetworkAddress | Counter | Gauge | TimeTicks | Opaque

ObjectSyntax = SimpleSyntax | ApplicationSyntax

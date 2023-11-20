#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ, rfc1905


@dataclass
class ScopedPDU(univ.Sequence):
    contextEngineId: univ.OctetString
    contextName: univ.OctetString
    data: rfc1905.PDUs


ScopedPduData = ScopedPDU | univ.OctetString


@dataclass
class HeaderData(univ.Sequence):
    msgID: univ.Integer
    msgMaxSize: univ.Integer
    msgFlags: univ.OctetString
    msgSecurityModel: univ.Integer


@dataclass
class SNMPv3Message(univ.Sequence):
    msgVersion: univ.Integer
    msgGlobalData: HeaderData
    msgSecurityParameters: univ.OctetString
    msgData: ScopedPduData

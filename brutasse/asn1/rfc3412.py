#!/usr/bin/env python3

from dataclasses import dataclass
from .base import Sequence, OctetString, Integer
from .rfc1905 import PDUs


@dataclass
class ScopedPDU(Sequence):
    contextEngineId: OctetString
    contextName: OctetString
    data: PDUs


ScopedPduData = ScopedPDU | OctetString


@dataclass
class HeaderData(Sequence):
    msgID: Integer
    msgMaxSize: Integer
    msgFlags: OctetString
    msgSecurityModel: Integer


@dataclass
class SNMPv3Message(Sequence):
    msgVersion: Integer
    msgGlobalData: HeaderData
    msgSecurityParameters: OctetString
    msgData: ScopedPduData

#!/usr/bin/env python3

import enum
from dataclasses import dataclass
from .base import Sequence, OctetString, Integer
from .rfc1905 import PDUs


class Version(Integer, enum.Enum):
    V3 = 3


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
    msgVersion: Version
    msgGlobalData: HeaderData
    msgSecurityParameters: OctetString
    msgData: ScopedPduData

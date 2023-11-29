#!/usr/bin/env python3

import enum
from dataclasses import dataclass
from .base import Sequence, Integer, OctetString
from .rfc1905 import PDUs


class Version(Integer, enum.Enum):
    V2C = 1


@dataclass
class Message(Sequence):
    version: Version
    community: OctetString
    data: PDUs

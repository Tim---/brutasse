#!/usr/bin/env python3

from dataclasses import dataclass
from .base import Sequence, Integer, OctetString
from .rfc1905 import PDUs


@dataclass
class Message(Sequence):
    version: Integer
    community: OctetString
    data: PDUs

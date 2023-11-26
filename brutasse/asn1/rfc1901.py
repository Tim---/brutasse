#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ, rfc1905


@dataclass
class Message(univ.Sequence):
    version: univ.Integer
    community: univ.OctetString
    # data: univ.Any
    data: rfc1905.PDUs

#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ


@dataclass
class Message(univ.Sequence):
    version: univ.Integer
    community: univ.OctetString
    data: univ.Any

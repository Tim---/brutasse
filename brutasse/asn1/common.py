#!/usr/bin/env python3

from dataclasses import dataclass
import enum


class TagClass(enum.IntEnum):
    UNIVERSAL = 0
    APPLICATION = 1
    CONTEXT = 2
    PRIVATE = 3


@dataclass(frozen=True)
class Identifier:
    class_: TagClass
    constructed: bool
    number: int


Tag = tuple[Identifier, bytes | list['Tag']]

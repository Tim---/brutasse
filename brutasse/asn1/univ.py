#!/usr/bin/env python3

import typing


class Sequence:
    pass


class ObjectIdentifier(str):
    pass


class Integer(int):
    pass


class OctetString(bytes):
    pass


class Null:
    pass


Any = typing.Any

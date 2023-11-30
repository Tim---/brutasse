#!/usr/bin/env python3

import enum
from dataclasses import dataclass
from .base import (TagClass, identifier, Sequence,
                   Integer, ObjectIdentifier, OctetString)
from .rfc1155 import ObjectName, ObjectSyntax, NetworkAddress, TimeTicks


class Version(Integer, enum.Enum):
    V1 = 0


class ErrorStatus(Integer, enum.Enum):
    NO_ERROR = 0
    TOO_BIG = 1
    NO_SUCH_NAME = 2
    BAD_VALUE = 3
    READ_ONLY = 4
    GEN_ERR = 5


@dataclass
class VarBind(Sequence):
    name: ObjectName
    value: ObjectSyntax


VarBindList = list[VarBind]


@dataclass
class _RequestBase(Sequence):
    request_id: Integer
    error_status: ErrorStatus
    error_index: Integer
    variable_bindings: VarBindList


@dataclass
@identifier(TagClass.CONTEXT, 0)
class GetRequestPDU(_RequestBase):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 1)
class GetNextRequestPDU(_RequestBase):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 2)
class GetResponsePDU(_RequestBase):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 3)
class SetRequestPDU(_RequestBase):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 4)
class TrapPDU(Sequence):
    enterprise: ObjectIdentifier
    agent_addr: NetworkAddress
    generic_trap: Integer
    specific_trap: Integer
    time_stamp: TimeTicks
    variable_bindings: VarBindList


Pdus = (GetRequestPDU | GetNextRequestPDU |
        GetResponsePDU | SetRequestPDU | TrapPDU)


@dataclass
class Message(Sequence):
    version: Version
    community: OctetString
    data: Pdus

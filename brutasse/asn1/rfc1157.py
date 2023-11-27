#!/usr/bin/env python3

from dataclasses import dataclass
from .base import (TagClass, identifier, Sequence,
                   Integer, ObjectIdentifier, OctetString)
from .rfc1155 import ObjectName, ObjectSyntax, NetworkAddress, TimeTicks


@dataclass
class VarBind(Sequence):
    name: ObjectName
    value: ObjectSyntax


VarBindList = list[VarBind]


@dataclass
class _RequestBase(Sequence):
    request_id: Integer
    error_status: Integer
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
    version: Integer
    community: OctetString
    data: Pdus

#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ, rfc1155


@dataclass
class VarBind(univ.Sequence):
    name: rfc1155.ObjectName
    value: rfc1155.ObjectSyntax


VarBindList = list[VarBind]


@dataclass
class GetRequestPDU(univ.Sequence):
    request_id: univ.Integer
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class GetNextRequestPDU(univ.Sequence):
    request_id: univ.Integer
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class GetResponsePDU(univ.Sequence):
    request_id: univ.Integer
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class SetRequestPDU(univ.Sequence):
    request_id: univ.Integer
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class TrapPDU(univ.Sequence):
    enterprise: univ.ObjectIdentifier
    agent_addr: rfc1155.NetworkAddress
    generic_trap: univ.Integer
    specific_trap: univ.Integer
    time_stamp: rfc1155.TimeTicks
    variable_bindings: VarBindList


Pdus = (GetRequestPDU | GetNextRequestPDU |
        GetResponsePDU | SetRequestPDU | TrapPDU)


@dataclass
class Message(univ.Sequence):
    version: univ.Integer
    community: univ.OctetString
    data: Pdus

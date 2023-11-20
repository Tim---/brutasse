#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ, rfc1902


class noSuchObject(univ.Null):
    pass


class noSuchInstance(univ.Null):
    pass


class endOfMibView(univ.Null):
    pass


_BindValue = (rfc1902.ObjectSyntax | univ.Null |
              noSuchObject | noSuchInstance | endOfMibView)


@dataclass
class VarBind(univ.Sequence):
    name: rfc1902.ObjectName
    value: _BindValue


VarBindList = list[VarBind]


@dataclass
class GetRequestPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class GetNextRequestPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class ResponsePDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class SetRequestPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class GetBulkRequestPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    non_repeaters: univ.Integer
    max_repetitions: univ.Integer
    variable_bindings: VarBindList


@dataclass
class InformRequestPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class SNMPv2TrapPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class ReportPDU(univ.Sequence):
    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


PDUs = (GetRequestPDU | GetNextRequestPDU | GetBulkRequestPDU | ResponsePDU |
        SetRequestPDU | InformRequestPDU | SNMPv2TrapPDU | ReportPDU)

#!/usr/bin/env python3

from dataclasses import dataclass
from . import univ, rfc1902
from .common import Identifier, TagClass


class noSuchObject(univ.Null):
    identifier = Identifier(TagClass.CONTEXT, False, 0)


class noSuchInstance(univ.Null):
    identifier = Identifier(TagClass.CONTEXT, False, 1)


class endOfMibView(univ.Null):
    identifier = Identifier(TagClass.CONTEXT, False, 2)


_BindValue = (rfc1902.ObjectSyntax | univ.Null |
              noSuchObject | noSuchInstance | endOfMibView)


@dataclass
class VarBind(univ.Sequence):
    name: rfc1902.ObjectName
    value: _BindValue


VarBindList = list[VarBind]


@dataclass
class GetRequestPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 0)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class GetNextRequestPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 1)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class ResponsePDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 2)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class SetRequestPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 3)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class GetBulkRequestPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 5)

    request_id: rfc1902.Integer32
    non_repeaters: univ.Integer
    max_repetitions: univ.Integer
    variable_bindings: VarBindList


@dataclass
class InformRequestPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 6)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class SNMPv2TrapPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 7)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


@dataclass
class ReportPDU(univ.Sequence):
    identifier = Identifier(TagClass.CONTEXT, True, 8)

    request_id: rfc1902.Integer32
    error_status: univ.Integer
    error_index: univ.Integer
    variable_bindings: VarBindList


PDUs = (GetRequestPDU | GetNextRequestPDU | GetBulkRequestPDU | ResponsePDU |
        SetRequestPDU | InformRequestPDU | SNMPv2TrapPDU | ReportPDU)

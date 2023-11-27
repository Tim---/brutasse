#!/usr/bin/env python3

from dataclasses import dataclass
from .base import TagClass, identifier, Null, Sequence, Integer
from .rfc1902 import ObjectSyntax, ObjectName, Integer32


@identifier(TagClass.CONTEXT, 0)
class noSuchObject(Null):
    pass


@identifier(TagClass.CONTEXT, 1)
class noSuchInstance(Null):
    pass


@identifier(TagClass.CONTEXT, 2)
class endOfMibView(Null):
    pass


_BindValue = (ObjectSyntax | Null |
              noSuchObject | noSuchInstance | endOfMibView)


@dataclass
class VarBind(Sequence):
    name: ObjectName
    value: _BindValue


VarBindList = list[VarBind]


@dataclass
class PDU(Sequence):
    request_id: Integer32
    error_status: Integer
    error_index: Integer
    variable_bindings: VarBindList


@dataclass
class BulkPDU(Sequence):
    request_id: Integer32
    non_repeaters: Integer
    max_repetitions: Integer
    variable_bindings: VarBindList


@dataclass
@identifier(TagClass.CONTEXT, 0)
class GetRequestPDU(PDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 1)
class GetNextRequestPDU(PDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 2)
class ResponsePDU(PDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 3)
class SetRequestPDU(PDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 5)
class GetBulkRequestPDU(BulkPDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 6)
class InformRequestPDU(PDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 7)
class SNMPv2TrapPDU(PDU):
    pass


@dataclass
@identifier(TagClass.CONTEXT, 8)
class ReportPDU(PDU):
    pass


PDUs = (GetRequestPDU | GetNextRequestPDU | GetBulkRequestPDU | ResponsePDU |
        SetRequestPDU | InformRequestPDU | SNMPv2TrapPDU | ReportPDU)

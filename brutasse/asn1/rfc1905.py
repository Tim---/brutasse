#!/usr/bin/env python3

import enum
from dataclasses import dataclass
from .base import TagClass, identifier, Null, Sequence, Integer
from .rfc1902 import ObjectSyntax, ObjectName, Integer32


class ErrorStatus(Integer, enum.Enum):
    NO_ERROR = 0
    TOO_BIG = 1
    NO_SUCH_NAME = 2
    BAD_VALUE = 3
    READ_ONLY = 4
    GEN_ERR = 5
    NO_ACCESS = 6
    WRONG_TYPE = 7
    WRONG_LENGTH = 8
    WRONG_ENCODING = 9
    WRONG_VALUE = 10
    NO_CREATION = 11
    INCONSISTENT_VALUE = 12
    RESOURCE_UNAVAILABLE = 13
    COMMIT_FAILED = 14
    UNDO_FAILED = 15
    AUTHORIZATION_ERROR = 16
    NOT_WRITABLE = 17
    INCONSISTENT_NAME = 18


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
    error_status: ErrorStatus
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

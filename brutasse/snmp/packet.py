#!/usr/bin/env python3

import enum
from dataclasses import dataclass

from brutasse.asn1.base import (
    Integer,
    Null,
    ObjectIdentifier,
    OctetString,
    Sequence,
    TagClass,
    identifier,
)

SimpleSyntax = Integer | OctetString | ObjectIdentifier | Null


@identifier(TagClass.APPLICATION, 0)
class IpAddress(OctetString):
    pass


@identifier(TagClass.APPLICATION, 1)
class Counter32(Integer):
    pass


@identifier(TagClass.APPLICATION, 2)
class Gauge32(Integer):
    pass


Unsigned32 = Gauge32


@identifier(TagClass.APPLICATION, 3)
class TimeTicks(Integer):
    pass


@identifier(TagClass.APPLICATION, 4)
class Opaque(OctetString):
    pass


@identifier(TagClass.APPLICATION, 6)
class Counter64(Integer):
    pass


ApplicationSyntax = IpAddress | Counter32 | Gauge32 | TimeTicks | Opaque | Counter64

ObjectSyntax = SimpleSyntax | ApplicationSyntax


class Version(Integer, enum.Enum):
    V1 = 0
    V2C = 1
    V3 = 3


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


BindValue = ObjectSyntax | noSuchObject | noSuchInstance | endOfMibView


@dataclass
class VarBind(Sequence):
    name: ObjectIdentifier
    value: BindValue


@dataclass
class PDU(Sequence):
    request_id: Integer
    error_status: ErrorStatus
    error_index: Integer
    variable_bindings: list[VarBind]


@dataclass
class BulkPDU(Sequence):
    request_id: Integer
    non_repeaters: Integer
    max_repetitions: Integer
    variable_bindings: list[VarBind]


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
@identifier(TagClass.CONTEXT, 4)
class TrapPDU(Sequence):
    enterprise: ObjectIdentifier
    agent_addr: IpAddress
    generic_trap: Integer
    specific_trap: Integer
    time_stamp: TimeTicks
    variable_bindings: list[VarBind]


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


PDUs = (
    GetRequestPDU
    | GetNextRequestPDU
    | ResponsePDU
    | SetRequestPDU
    | TrapPDU
    | GetBulkRequestPDU
    | InformRequestPDU
    | SNMPv2TrapPDU
    | ReportPDU
)


@dataclass
class Message(Sequence):
    version: Version
    community: OctetString
    data: PDUs


@dataclass
class ScopedPDU(Sequence):
    contextEngineId: OctetString
    contextName: OctetString
    data: PDUs


ScopedPduData = ScopedPDU | OctetString


class SecurityModel(Integer, enum.Enum):
    USM = 3


class MsgFlags(Integer, enum.Flag):
    AUTH = 1
    PRIV = 2
    REPORTABLE = 4


@dataclass
class HeaderData(Sequence):
    msgID: Integer
    msgMaxSize: Integer
    msgFlags: OctetString
    msgSecurityModel: SecurityModel


@dataclass
class SNMPv3Message(Sequence):
    msgVersion: Version
    msgGlobalData: HeaderData
    msgSecurityParameters: OctetString
    msgData: ScopedPduData


@dataclass
class UsmSecurityParameters(Sequence):
    msgAuthoritativeEngineID: OctetString
    msgAuthoritativeEngineBoots: Integer
    msgAuthoritativeEngineTime: Integer
    msgUserName: OctetString
    msgAuthenticationParameters: OctetString
    msgPrivacyParameters: OctetString

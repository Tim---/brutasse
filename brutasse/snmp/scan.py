#!/usr/bin/env python3

import logging
from typing import TypeVar, Optional
from ipaddress import IPv4Network, IPv4Address
from collections.abc import Callable, AsyncIterator
from ..scan import zmap
from ..asn1.ber import ber_build, ber_parse
from ..asn1.base import Integer, OctetString, ObjectIdentifier, Null
from ..asn1.snmp import (
    Message, VarBind, GetRequestPDU, Version, ErrorStatus, SNMPv3Message,
    HeaderData, ScopedPDU, UsmSecurityParameters, SecurityModel, MsgFlags
)

T = TypeVar('T')


def make_v1_request(community: str) -> bytes:
    return ber_build(Message(
        version=Version.V1,
        community=OctetString(community.encode()),
        data=GetRequestPDU(
            request_id=Integer(1278453590),
            error_status=ErrorStatus.NO_ERROR,
            error_index=Integer(0),
            variable_bindings=[VarBind(
                name=ObjectIdentifier.from_string('1.3.6.1.2.1.1.5.0'),
                value=Null()
            )]
        )
    ))


def get_v1_community(raw: bytes) -> str:
    msg = ber_parse(raw, Message)
    return msg.community.decode()


def make_v2c_request(community: str) -> bytes:
    return ber_build(Message(
        version=Version.V2C,
        community=OctetString(community.encode()),
        data=GetRequestPDU(
            request_id=Integer(1278453590),
            error_status=ErrorStatus.NO_ERROR,
            error_index=Integer(0),
            variable_bindings=[VarBind(
                name=ObjectIdentifier.from_string('1.3.6.1.2.1.1.5.0'),
                value=Null()
            )]
        )
    ))


def get_v2c_community(raw: bytes) -> str:
    msg = ber_parse(raw, Message)
    return msg.community.decode()


def make_v3_request() -> bytes:
    return ber_build(SNMPv3Message(
        msgVersion=Version.V3,
        msgGlobalData=HeaderData(
            msgID=Integer(19049),
            msgMaxSize=Integer(65507),
            msgFlags=OctetString([MsgFlags.REPORTABLE]),
            msgSecurityModel=SecurityModel.USM,
        ),
        msgSecurityParameters=OctetString(ber_build(
            UsmSecurityParameters(
                msgAuthoritativeEngineID=OctetString(b''),
                msgAuthoritativeEngineBoots=Integer(0),
                msgAuthoritativeEngineTime=Integer(0),
                msgUserName=OctetString(b''),
                msgAuthenticationParameters=OctetString(b''),
                msgPrivacyParameters=OctetString(b''),
            )
        )),
        msgData=ScopedPDU(
            contextEngineId=OctetString(b''),
            contextName=OctetString(b''),
            data=GetRequestPDU(
                request_id=Integer(14320),
                error_status=ErrorStatus.NO_ERROR,
                error_index=Integer(0),
                variable_bindings=[]
            )
        )
    ))


def parse_v3_vendor(raw: bytes) -> Optional[int]:
    msg = ber_parse(raw, SNMPv3Message)

    # We can find the engine_id in two places:
    msg_data = msg.msgData
    assert isinstance(msg_data, ScopedPDU)

    engine_id = bytes(msg_data.contextEngineId)

    if not engine_id:
        sec = ber_parse(msg.msgSecurityParameters, UsmSecurityParameters)
        engine_id = bytes(sec.msgAuthoritativeEngineID)

    if not engine_id:
        return None

    assert len(engine_id) >= 4
    enterprise_num = int.from_bytes(engine_id[:4], 'big') & 0x7fffffff
    return enterprise_num


async def snmp_scan_common(ranges: list[IPv4Network], rate: int,
                           payload: bytes, decoder: Callable[[bytes], T]
                           ) -> AsyncIterator[tuple[IPv4Address, T]]:
    scan = zmap.udp_scan(ranges, rate, port=161, payload=payload)
    async for saddr, data in scan:
        try:
            decoded = decoder(data)
            yield saddr, decoded
        except Exception as e:
            logging.error(e, exc_info=True)


def scan_v1(ranges: list[IPv4Network], rate: int, community: str
            ) -> AsyncIterator[tuple[IPv4Address, str]]:
    return snmp_scan_common(ranges, rate,
                            make_v1_request(community), get_v1_community)


def scan_v2c(ranges: list[IPv4Network], rate: int, community: str
             ) -> AsyncIterator[tuple[IPv4Address, str]]:
    return snmp_scan_common(ranges, rate,
                            make_v2c_request(community), get_v2c_community)


def scan_v3(ranges: list[IPv4Network], rate: int
            ) -> AsyncIterator[tuple[IPv4Address, Optional[int]]]:
    return snmp_scan_common(ranges, rate,
                            make_v3_request(), parse_v3_vendor)

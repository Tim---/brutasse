#!/usr/bin/env python3

from typing import Optional
from ..asn1.ber import ber_build, ber_parse
from ..asn1.base import Integer, OctetString
from ..asn1.rfc1905 import GetRequestPDU, ErrorStatus
from ..asn1.rfc3412 import SNMPv3Message, HeaderData, ScopedPDU, Version
from ..asn1.rfc3414 import UsmSecurityParameters


def make_v3_request() -> bytes:
    return ber_build(SNMPv3Message(
        msgVersion=Version.V3,
        msgGlobalData=HeaderData(
            msgID=Integer(19049),
            msgMaxSize=Integer(65507),
            msgFlags=OctetString([4]),
            msgSecurityModel=Integer(3),
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

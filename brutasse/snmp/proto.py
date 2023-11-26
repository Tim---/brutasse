#!/usr/bin/env python3

from typing import Optional
from ..asn1.ber import ber_build, ber_parse
from ..asn1 import univ, rfc3412, rfc3414, rfc1157, rfc1901, rfc1902, rfc1905


def make_v1_request(community: str) -> bytes:
    return ber_build(rfc1157.Message(
        version=univ.Integer(0),
        community=univ.OctetString(community.encode()),
        data=rfc1157.GetRequestPDU(
            request_id=univ.Integer(1278453590),
            error_status=univ.Integer(0),
            error_index=univ.Integer(0),
            variable_bindings=[rfc1157.VarBind(
                name=univ.ObjectIdentifier.from_string('1.3.6.1.2.1.1.5.0'),
                value=univ.Null()
            )]
        )
    ))


def get_v1_community(raw: bytes) -> str:
    msg = ber_parse(raw, rfc1157.Message)
    return msg.community.decode()


def make_v2c_request(community: str) -> bytes:
    return ber_build(rfc1901.Message(
        version=univ.Integer(1),
        community=univ.OctetString(community.encode()),
        data=rfc1905.GetRequestPDU(
            request_id=univ.Integer(1278453590),
            error_status=univ.Integer(0),
            error_index=univ.Integer(0),
            variable_bindings=[rfc1905.VarBind(
                name=rfc1902.ObjectName.from_string('1.3.6.1.2.1.1.5.0'),
                value=univ.Null()
            )]
        )
    ))


def get_v2c_community(raw: bytes) -> str:
    msg = ber_parse(raw, rfc1901.Message)
    return msg.community.decode()


def make_v3_request() -> bytes:
    return ber_build(rfc3412.SNMPv3Message(
        msgVersion=univ.Integer(3),
        msgGlobalData=rfc3412.HeaderData(
            msgID=univ.Integer(19049),
            msgMaxSize=univ.Integer(65507),
            msgFlags=univ.OctetString([4]),
            msgSecurityModel=univ.Integer(3),
        ),
        msgSecurityParameters=univ.OctetString(ber_build(
            rfc3414.UsmSecurityParameters(
                msgAuthoritativeEngineID=univ.OctetString(b''),
                msgAuthoritativeEngineBoots=univ.Integer(0),
                msgAuthoritativeEngineTime=univ.Integer(0),
                msgUserName=univ.OctetString(b''),
                msgAuthenticationParameters=univ.OctetString(b''),
                msgPrivacyParameters=univ.OctetString(b''),
            )
        )),
        msgData=rfc3412.ScopedPDU(
            contextEngineId=univ.OctetString(b''),
            contextName=univ.OctetString(b''),
            data=rfc1905.GetRequestPDU(
                request_id=univ.Integer(14320),
                error_status=univ.Integer(0),
                error_index=univ.Integer(0),
                variable_bindings=[]
            )
        )
    ))


def parse_v3_vendor(raw: bytes) -> Optional[int]:
    msg = ber_parse(raw, rfc3412.SNMPv3Message)

    # We can find the engine_id in two places:
    msg_data = msg.msgData
    assert isinstance(msg_data, rfc3412.ScopedPDU)

    engine_id = bytes(msg_data.contextEngineId)

    if not engine_id:
        sec = ber_parse(msg.msgSecurityParameters,
                        rfc3414.UsmSecurityParameters)
        engine_id = bytes(sec.msgAuthoritativeEngineID)

    if not engine_id:
        return None

    assert len(engine_id) >= 4
    enterprise_num = int.from_bytes(engine_id[:4], 'big') & 0x7fffffff
    return enterprise_num

#!/usr/bin/env python3

from typing import Optional
from ..asn1.ber import ber_build, ber_parse
from ..asn1 import base, rfc3412, rfc3414, rfc1157, rfc1901, rfc1902, rfc1905


def make_v1_request(community: str) -> bytes:
    return ber_build(rfc1157.Message(
        version=base.Integer(0),
        community=base.OctetString(community.encode()),
        data=rfc1157.GetRequestPDU(
            request_id=base.Integer(1278453590),
            error_status=base.Integer(0),
            error_index=base.Integer(0),
            variable_bindings=[rfc1157.VarBind(
                name=base.ObjectIdentifier.from_string('1.3.6.1.2.1.1.5.0'),
                value=base.Null()
            )]
        )
    ))


def get_v1_community(raw: bytes) -> str:
    msg = ber_parse(raw, rfc1157.Message)
    return msg.community.decode()


def make_v2c_request(community: str) -> bytes:
    return ber_build(rfc1901.Message(
        version=base.Integer(1),
        community=base.OctetString(community.encode()),
        data=rfc1905.GetRequestPDU(
            request_id=base.Integer(1278453590),
            error_status=base.Integer(0),
            error_index=base.Integer(0),
            variable_bindings=[rfc1905.VarBind(
                name=rfc1902.ObjectName.from_string('1.3.6.1.2.1.1.5.0'),
                value=base.Null()
            )]
        )
    ))


def get_v2c_community(raw: bytes) -> str:
    msg = ber_parse(raw, rfc1901.Message)
    return msg.community.decode()


def make_v3_request() -> bytes:
    return ber_build(rfc3412.SNMPv3Message(
        msgVersion=base.Integer(3),
        msgGlobalData=rfc3412.HeaderData(
            msgID=base.Integer(19049),
            msgMaxSize=base.Integer(65507),
            msgFlags=base.OctetString([4]),
            msgSecurityModel=base.Integer(3),
        ),
        msgSecurityParameters=base.OctetString(ber_build(
            rfc3414.UsmSecurityParameters(
                msgAuthoritativeEngineID=base.OctetString(b''),
                msgAuthoritativeEngineBoots=base.Integer(0),
                msgAuthoritativeEngineTime=base.Integer(0),
                msgUserName=base.OctetString(b''),
                msgAuthenticationParameters=base.OctetString(b''),
                msgPrivacyParameters=base.OctetString(b''),
            )
        )),
        msgData=rfc3412.ScopedPDU(
            contextEngineId=base.OctetString(b''),
            contextName=base.OctetString(b''),
            data=rfc1905.GetRequestPDU(
                request_id=base.Integer(14320),
                error_status=base.Integer(0),
                error_index=base.Integer(0),
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

#!/usr/bin/env python3

from ..asn1 import univ, rfc3412, rfc3414, rfc1157, rfc1901, rfc1902, rfc1905


def make_varbind() -> rfc1157.VarBind:
    return rfc1157.VarBind(
        name=univ.ObjectIdentifier('1.3.6.1.2.1.1.5.0'),
        value=univ.Null()
    )


def make_v1_request(community: str) -> rfc1157.Message:
    return rfc1157.Message(
        version=univ.Integer(0),
        community=univ.OctetString(community.encode()),
        data=rfc1157.GetRequestPDU(
            request_id=univ.Integer(1278453590),
            error_status=univ.Integer(0),
            error_index=univ.Integer(0),
            variable_bindings=[rfc1157.VarBind(
                name=univ.ObjectIdentifier('1.3.6.1.2.1.1.5.0'),
                value=univ.Null()
            )]
        )
    )


def get_v1_community(msg: rfc1157.Message) -> str:
    return msg.community.decode()


def make_v2c_request(community: str) -> rfc1901.Message:
    return rfc1901.Message(
        version=univ.Integer(1),
        community=univ.OctetString(community.encode()),
        data=rfc1905.GetRequestPDU(
            request_id=univ.Integer(1278453590),
            error_status=univ.Integer(0),
            error_index=univ.Integer(0),
            variable_bindings=[rfc1905.VarBind(
                name=rfc1902.ObjectName('1.3.6.1.2.1.1.5.0'),
                value=univ.Null()
            )]
        )
    )


def get_v2c_community(msg: rfc1901.Message) -> str:
    return msg.community.decode()


def make_v3_request() -> rfc3412.SNMPv3Message:
    return rfc3412.SNMPv3Message(
        msgVersion=3,
        msgGlobalData=rfc3412.HeaderData(
            msgID=univ.Integer(19049),
            msgMaxSize=univ.Integer(65507),
            msgFlags=univ.OctetString([4]),
            msgSecurityModel=univ.Integer(3),
        ),
        msgSecurityParameters=encoder.encode(rfc3414.UsmSecurityParameters(
            msgAuthoritativeEngineID=univ.OctetString(b''),
            msgAuthoritativeEngineBoots=univ.Integer(0),
            msgAuthoritativeEngineTime=univ.Integer(0),
            msgUserName=univ.OctetString(b''),
            msgAuthenticationParameters=univ.OctetString(b''),
            msgPrivacyParameters=univ.OctetString(b''),
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
    )

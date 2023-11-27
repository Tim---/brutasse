#!/usr/bin/env python3

from ..asn1.ber import ber_build, ber_parse
from ..asn1.base import Integer, OctetString, ObjectIdentifier, Null
from ..asn1.rfc1157 import Message, VarBind, GetRequestPDU


def make_v1_request(community: str) -> bytes:
    return ber_build(Message(
        version=Integer(0),
        community=OctetString(community.encode()),
        data=GetRequestPDU(
            request_id=Integer(1278453590),
            error_status=Integer(0),
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

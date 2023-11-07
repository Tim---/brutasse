#!/usr/bin/env python3

from typing import Optional, Any
from pyasn1.codec.ber import encoder, decoder
from pyasn1_modules import rfc3412, rfc3414, rfc1157, rfc1901, rfc1905


def asn1_decode(raw: bytes, cls: Any) -> Any:
    msg, rest = decoder.decode(raw, asn1Spec=cls())
    assert not rest
    return msg


def make_varbind() -> rfc1157.VarBind:
    varbind = rfc1157.VarBind()
    varbind['name'] = '1.3.6.1.2.1.1.5.0'
    varbind['value']['simple']['empty'] = None
    return varbind


def make_v1_request(community: str) -> bytes:
    msg = rfc1157.Message()
    msg['version'] = 'version-1'
    msg['community'] = community
    get_request = msg['data']['get-request']
    get_request['request-id'] = 1278453590
    get_request['error-status'] = 'noError'
    get_request['error-index'] = 0
    get_request['variable-bindings'].clear()
    get_request['variable-bindings'].append(make_varbind())

    return encoder.encode(msg)


def get_v1_community(raw: bytes) -> str:
    msg = asn1_decode(raw, rfc1157.Message)
    return str(msg['community'])


def make_v2c_request(community: str) -> bytes:
    msg = rfc1901.Message()
    msg['version'] = 'version-2c'
    msg['community'] = community
    pdu = rfc1905.GetRequestPDU()
    pdu['request-id'] = 1278453590
    pdu['error-status'] = 'noError'
    pdu['error-index'] = 0
    pdu['variable-bindings'].clear()
    pdu['variable-bindings'].append(make_varbind())
    msg['data'] = pdu

    return encoder.encode(msg)


def get_v2c_community(raw: bytes) -> str:
    msg = asn1_decode(raw, rfc1901.Message)
    return str(msg['community'])


def make_v3_request() -> bytes:
    sec = rfc3414.UsmSecurityParameters()
    sec['msgAuthoritativeEngineID'] = b''
    sec['msgAuthoritativeEngineBoots'] = 0
    sec['msgAuthoritativeEngineTime'] = 0
    sec['msgUserName'] = b''
    sec['msgAuthenticationParameters'] = b''
    sec['msgPrivacyParameters'] = b''

    msg = rfc3412.SNMPv3Message()
    msg['msgVersion'] = 3
    msgGlobalData = msg['msgGlobalData']
    msgGlobalData['msgID'] = 19049
    msgGlobalData['msgMaxSize'] = 65507
    msgGlobalData['msgFlags'] = bytes([4])
    msgGlobalData['msgSecurityModel'] = 3
    msg['msgSecurityParameters'] = encoder.encode(sec)
    plaintext = msg['msgData']['plaintext']
    plaintext['contextEngineId'] = b''
    plaintext['contextName'] = b''
    get_request = plaintext['data']['get-request']
    get_request['request-id'] = 14320
    get_request['error-status'] = 'noError'
    get_request['error-index'] = 0
    get_request['variable-bindings'].clear()

    return encoder.encode(msg)


def parse_v3_vendor(raw: bytes) -> Optional[int]:
    msg = asn1_decode(raw, rfc3412.SNMPv3Message)

    # We can find the engine_id in two places:

    engine_id = bytes(msg['msgData']['plaintext']['contextEngineId'])

    if not engine_id:
        sec = asn1_decode(msg['msgSecurityParameters'],
                          rfc3414.UsmSecurityParameters)
        engine_id = bytes(sec['msgAuthoritativeEngineID'])

    if not engine_id:
        return None

    assert len(engine_id) >= 4
    enterprise_num = int.from_bytes(engine_id[:4], 'big') & 0x7fffffff
    return enterprise_num

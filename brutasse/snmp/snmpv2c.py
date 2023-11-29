#!/usr/bin/env python3

import asyncio
from types import TracebackType
from typing import Optional, Self
from collections.abc import AsyncIterator
import anyio
from ..asn1.ber import ber_build, ber_parse
from ..asn1.base import Integer, OctetString, Null
from ..asn1.rfc1901 import Message
from ..asn1.rfc1902 import ObjectName
from ..asn1.rfc1905 import (
    GetRequestPDU, GetNextRequestPDU, SetRequestPDU, ResponsePDU, VarBind,
    VarBindList, PDUs, _BindValue
)


def make_v2c_request(community: str) -> bytes:
    return ber_build(Message(
        version=Integer(1),
        community=OctetString(community.encode()),
        data=GetRequestPDU(
            request_id=Integer(1278453590),
            error_status=Integer(0),
            error_index=Integer(0),
            variable_bindings=[VarBind(
                name=ObjectName.from_string('1.3.6.1.2.1.1.5.0'),
                value=Null()
            )]
        )
    ))


def get_v2c_community(raw: bytes) -> str:
    msg = ber_parse(raw, Message)
    return msg.community.decode()


GenericRequestPdu = GetRequestPDU | GetNextRequestPDU | SetRequestPDU


class Snmpv2c:
    def __init__(self, host: str, port: int, community: str):
        self.host = host
        self.port = port
        self.community = community
        self.request_id = 0
        self.retries = 2
        self.timeout = 1.0

    async def __aenter__(self) -> Self:
        self.udp = await anyio.create_connected_udp_socket(self.host,
                                                           self.port)
        return self

    async def __aexit__(self, exc_type: Optional[type[BaseException]],
                        exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]) -> None:
        await self.udp.aclose()

    async def walk_branch(self, base_oid: ObjectName
                          ) -> AsyncIterator[VarBind]:
        begin_oid = base_oid

        # tweak: oid size must be >= 2
        while len(begin_oid) < 2:
            begin_oid = ObjectName((*begin_oid, 0))

        if not base_oid:
            # tweak: oids are always lower than this
            end_oid = ObjectName((3, ))
        else:
            end_oid = ObjectName((*base_oid[:-1], base_oid[-1] + 1))

        async for vb in self.walk(begin_oid, end_oid):
            yield vb

    async def walk(self, begin_oid: ObjectName,
                   end_oid: ObjectName) -> AsyncIterator[VarBind]:
        oid = begin_oid
        while True:
            vb, = await self.get_next([oid])
            assert vb.name > oid
            oid = vb.name
            if oid >= end_oid:
                break
            yield vb

    async def get(self, oids: list[ObjectName]
                  ) -> list[_BindValue]:
        req_varbinds = [VarBind(name=oid, value=Null()) for oid in oids]
        resp_varbinds = await self.generic_request(GetRequestPDU, req_varbinds)
        assert len(resp_varbinds) == len(oids)
        for oid, vb in zip(oids, resp_varbinds):
            assert vb.name == oid
        return [vb.value for vb in resp_varbinds]

    async def get_next(self, oids: list[ObjectName]
                       ) -> VarBindList:
        req_varbinds = [VarBind(name=oid, value=Null()) for oid in oids]
        resp_varbinds = await self.generic_request(GetNextRequestPDU,
                                                   req_varbinds)
        assert len(resp_varbinds) == len(oids)
        return resp_varbinds

    async def get_request(self, req_varbinds: VarBindList) -> VarBindList:
        return await self.generic_request(GetRequestPDU, req_varbinds)

    async def generic_request(self, cls: type[GenericRequestPdu],
                              req_varbinds: VarBindList) -> VarBindList:
        request_id = self.request_id
        self.request_id += 1
        req = cls(
            request_id=Integer(request_id),
            error_status=Integer(0),
            error_index=Integer(0),
            variable_bindings=req_varbinds,
        )
        resp = await self.send_receive_pdu(req)
        match resp:
            case ResponsePDU(received_request_id, error_status,
                             error_index, resp_varbinds):
                assert received_request_id == request_id
                assert error_status == 0
                assert error_index == 0
                return resp_varbinds
            case _:
                raise ValueError(f'Unexpected PDU: {resp}')

    async def send_receive_pdu(self, pdu: PDUs) -> PDUs:
        for _ in range(self.retries + 1):
            await self.send_pdu(pdu)
            try:
                return await asyncio.wait_for(self.recv_pdu(), self.timeout)
            except TimeoutError:
                continue
        raise TimeoutError('Max retries exceeded')

    async def send_pdu(self, pdu: PDUs) -> None:
        req = Message(
            version=Integer(0),
            community=OctetString(self.community.encode()),
            data=pdu
        )
        await self.udp.send(ber_build(req))

    async def recv_pdu(self) -> PDUs:
        raw = await self.udp.receive()
        resp = ber_parse(raw, Message)
        match resp:
            case Message(Integer(0), OctetString(community), pdu) \
                    if community == self.community.encode():
                return pdu
            case _:
                raise ValueError(f'Unexpected message: {resp}')

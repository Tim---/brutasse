#!/usr/bin/env python3

import asyncio
from types import TracebackType
from typing import Optional, Self
from collections.abc import AsyncIterator
import anyio
from ..asn1.ber import ber_build, ber_parse
from ..asn1.base import Integer, OctetString, ObjectIdentifier, Null
from ..asn1.snmp import (
    ObjectSyntax, Message, VarBind, GetRequestPDU, ResponsePDU,
    GetNextRequestPDU, SetRequestPDU, PDUs, Version, ErrorStatus
)


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


GenericRequestPdu = GetRequestPDU | GetNextRequestPDU | SetRequestPDU


class Snmpv1:
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

    async def walk_branch(self, base_oid: ObjectIdentifier
                          ) -> AsyncIterator[VarBind]:
        begin_oid = base_oid

        # tweak: oid size must be >= 2
        while len(begin_oid) < 2:
            begin_oid = ObjectIdentifier((*begin_oid, 0))

        if not base_oid:
            # tweak: oids are always lower than this
            end_oid = ObjectIdentifier((3, ))
        else:
            end_oid = ObjectIdentifier((*base_oid[:-1], base_oid[-1] + 1))

        async for vb in self.walk(begin_oid, end_oid):
            yield vb

    async def walk(self, begin_oid: ObjectIdentifier,
                   end_oid: ObjectIdentifier) -> AsyncIterator[VarBind]:
        oid = begin_oid
        while True:
            vb, = await self.get_next([oid])
            if not vb:
                break
            assert vb.name > oid
            oid = vb.name
            if oid >= end_oid:
                break
            yield vb

    async def get(self, oids: list[ObjectIdentifier]
                  ) -> list[Optional[ObjectSyntax]]:
        d = await self.generic_request(GetRequestPDU, oids)
        res: list[Optional[ObjectSyntax]] = []
        for oid in oids:
            if oid in d:
                assert d[oid].name == oid
                res.append(d[oid].value)
            else:
                res.append(None)
        return res

    async def get_next(self, oids: list[ObjectIdentifier]
                       ) -> list[Optional[VarBind]]:
        d = await self.generic_request(GetNextRequestPDU, oids)
        res: list[Optional[VarBind]] = []
        for oid in oids:
            if oid in d:
                assert d[oid].name > oid
                res.append(d[oid])
            else:
                res.append(None)
        return res

    async def generic_request(self, cls: type[GenericRequestPdu],
                              oids: list[ObjectIdentifier]
                              ) -> dict[ObjectIdentifier, VarBind]:
        current_oids = list(oids)
        while True:
            resp = await self.send_receive_request(cls, [
                VarBind(name=oid, value=Null()) for oid in current_oids
            ])
            match resp.error_status:
                case ErrorStatus.NO_ERROR:
                    result = dict(zip(current_oids, resp.variable_bindings))
                case ErrorStatus.NO_SUCH_NAME:
                    bad_oid = current_oids[resp.error_index-1]
                    current_oids.remove(bad_oid)
                    continue
                case _:
                    raise ValueError(
                        f'Unhandled SNMP error: {resp.error_status}')
            return result

    async def send_receive_request(self, cls: type[GenericRequestPdu],
                                   req_varbinds: list[VarBind]
                                   ) -> ResponsePDU:
        request_id = self.request_id
        self.request_id += 1
        req = cls(
            request_id=Integer(request_id),
            error_status=ErrorStatus.NO_ERROR,
            error_index=Integer(0),
            variable_bindings=req_varbinds,
        )
        resp = await self.send_receive_pdu(req)

        if not isinstance(resp, ResponsePDU):
            raise ValueError(f'Unexpected PDU type: {resp.__class__}')

        if resp.request_id != request_id:
            raise ValueError(f'Unexpected request_id: {resp.request_id}')

        return resp

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
            version=Version.V1,
            community=OctetString(self.community.encode()),
            data=pdu
        )
        await self.udp.send(ber_build(req))

    async def recv_pdu(self) -> PDUs:
        raw = await self.udp.receive()
        resp = ber_parse(raw, Message)
        match resp:
            case Message(Version.V1, OctetString(community), pdu) \
                    if community == self.community.encode():
                return pdu
            case _:
                raise ValueError(f'Unexpected message: {resp}')

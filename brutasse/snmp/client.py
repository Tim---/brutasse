#!/usr/bin/env python3

from pysnmp.hlapi.asyncio import (
    SnmpEngine, getCmd, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity)
from pyasn1.type.base import Asn1Item
from typing import cast


class Clientv2:
    def __init__(self, ip: str, port: int, community: str):
        self.ip = ip
        self.snmp_engine = SnmpEngine()
        self.auth_data = CommunityData(community, mpModel=1)
        self.transport_target = UdpTransportTarget((ip, port))
        self.context_data = ContextData()

    async def get_sys_info(self) -> dict[str, str]:
        res = await self.get_several([
            ObjectIdentity('1.3.6.1.2.1.1.1.0'),
            ObjectIdentity('1.3.6.1.2.1.1.2.0'),
            ObjectIdentity('1.3.6.1.2.1.1.4.0'),
            ObjectIdentity('1.3.6.1.2.1.1.5.0'),
            ObjectIdentity('1.3.6.1.2.1.1.6.0'),
        ])
        descr, object_id, contact, name, location = res
        return {
            'descr': str(descr),
            'object_id': str(object_id),
            'contact': str(contact),
            'name': str(name),
            'location': str(location)
        }

    async def get_one(self, oid: ObjectIdentity) -> Asn1Item:
        value, = await self.get_several([oid])
        return value

    async def get_several(self, oids: list[ObjectIdentity]) -> list[Asn1Item]:
        in_var_binds = [ObjectType(oid) for oid in oids]
        iterator = getCmd(
            self.snmp_engine,
            self.auth_data,
            self.transport_target,
            self.context_data,
            *in_var_binds,
            lookupMib=False,
        )

        # TODO: if any varbind fails, we raise an Exception
        # We might want to handle that a bit better. Or not.
        (error_indication, error_status,
         error_index, out_var_binds) = await iterator
        assert not error_indication
        assert not error_status
        assert not error_index

        return [cast(Asn1Item, value) for _, value in out_var_binds]

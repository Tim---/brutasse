#!/usr/bin/env python3

from brutasse.snmp.snmpv2c import Snmpv2c
from brutasse.asn1.rfc1902 import ObjectName, OctetString
from brutasse.asn1.rfc1905 import _BindValue


def as_string(value: _BindValue) -> str:
    match value:
        case OctetString():
            return value.decode(errors='backslashreplace')
        case ObjectName():
            return str(value)
        case _:
            raise NotImplementedError()


async def get_sys_info(ip: str, port: int, community: str) -> dict[str, str]:
    columns = {
        1: 'description',
        2: 'object_id',
        4: 'contact',
        5: 'name',
        6: 'location',
    }
    oids = [ObjectName.from_string(f'1.3.6.1.2.1.1.{i}.0')
            for i in columns]
    async with Snmpv2c(ip, port, community) as client:
        values = await client.get(oids)
        return {column: as_string(value)
                for column, value in zip(columns.values(), values)}

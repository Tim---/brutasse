#!/usr/bin/env python3

from typing import Optional

from brutasse.snmp.packet import ObjectIdentifier, ObjectSyntax, OctetString
from brutasse.snmp.snmpv2c import Snmpv2c


def as_string(value: Optional[ObjectSyntax]) -> str:
    match value:
        case OctetString():
            return value.decode(errors="backslashreplace")
        case ObjectIdentifier():
            return str(value)
        case _:
            raise NotImplementedError(f"Unsupported type {value!r}")


async def get_sys_info(
    address: str, port: int, community: str
) -> tuple[str, int, dict[str, str]]:
    """Retrieve the system information.

    :param address: IP/hostname of the target
    :param port: UDP port
    :param community: SNMP community
    :return: a tuple (IP, port, attributes)
    """
    columns = {
        1: "description",
        2: "object_id",
        4: "contact",
        5: "name",
        6: "location",
    }
    oids = [ObjectIdentifier.from_string(f"1.3.6.1.2.1.1.{i}.0") for i in columns]
    async with Snmpv2c(address, port, community) as client:
        values = await client.get(oids)
        res = {
            column: as_string(value) for column, value in zip(columns.values(), values)
        }

        return address, port, res

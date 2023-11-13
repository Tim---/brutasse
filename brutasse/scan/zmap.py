#!/usr/bin/env python3

import json
from ipaddress import IPv4Address, IPv4Network
from collections.abc import AsyncIterator
from asyncio.subprocess import create_subprocess_exec, PIPE
from ..utils import get_default_interface, argunparse
import os


async def zmap_scan(options: dict[str, str], ranges: list[IPv4Network]
                    ) -> AsyncIterator[dict[str, str]]:
    interface = get_default_interface()
    base_options = {
        'output-module': 'json',
        'interface': interface
    }
    args = argunparse(base_options | options, map(str, ranges))

    read, write = os.pipe()
    zmap_proc = await create_subprocess_exec('zmap', *args, stdout=write)
    os.close(write)
    ztee_proc = await create_subprocess_exec('ztee', '-r', '/dev/null',
                                             stdin=read, stdout=PIPE)
    os.close(read)
    assert ztee_proc.stdout
    async for line in ztee_proc.stdout:
        j = json.loads(line)
        assert isinstance(j, dict)
        yield j
    await zmap_proc.wait()
    await ztee_proc.wait()


async def udp_scan(ranges: list[IPv4Network], rate: int, port: int,
                   payload: bytes
                   ) -> AsyncIterator[tuple[IPv4Address, bytes]]:
    options = {
        'probe-module': 'udp',
        'target-port': str(port),
        'probe-args': f'hex:{payload.hex()}',
        'rate': str(rate),
        'output-fields': 'saddr,data',
        'output-filter': f'success = 1 && repeat = 0 && sport = {port}',
    }
    async for j in zmap_scan(options, ranges):
        yield IPv4Address(j['saddr']), bytes.fromhex(j.get('data', ''))


async def tcp_scan(ranges: list[IPv4Network], rate: int, port: int
                   ) -> AsyncIterator[IPv4Address]:
    options = {
        'probe-module': 'tcp_synscan',
        'target-port': str(port),
        'rate': str(rate),
        'output-fields': 'saddr',
        'output-filter': f'success = 1 && repeat = 0 && sport = {port}',
    }
    async for j in zmap_scan(options, ranges):
        yield IPv4Address(j['saddr'])

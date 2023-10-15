#!/usr/bin/env python3

import json
import asyncio
from ipaddress import IPv4Address, IPv4Network
from collections.abc import AsyncGenerator
from ..utils import get_default_interface, argunparse


async def zmap_scan(options: dict[str, str], ranges: list[IPv4Network]) -> AsyncGenerator[dict[str, str], None]:
    interface = get_default_interface()
    base_options = {
        'output-module': 'json',
        'interface': interface
    }
    args = argunparse(base_options | options, map(str, ranges))
    proc = await asyncio.subprocess.create_subprocess_exec('zmap', *args, stdout=asyncio.subprocess.PIPE)
    assert proc.stdout
    async for line in proc.stdout:
        j = json.loads(line)
        assert isinstance(j, dict)
        yield j
    await proc.wait()


async def udp_scan(ranges: list[IPv4Network], rate: int, port: int, payload: bytes) -> AsyncGenerator[tuple[IPv4Address, bytes], None]:
    options = {
        'probe-module': 'udp',
        'target-port': str(port),
        'probe-args': f'hex:{payload.hex()}',
        'rate': str(rate),
        'output-fields': 'saddr,data',
        'output-filter': f'success = 1 && repeat = 0 && sport = {port}',
    }
    async for j in zmap_scan(options, ranges):
        yield IPv4Address(j['saddr']), bytes.fromhex(j['data'])


async def tcp_scan(ranges: list[IPv4Network], rate: int, port: int) -> AsyncGenerator[IPv4Address, None]:
    options = {
        'probe-module': 'tcp_synscan',
        'target-port': str(port),
        'rate': str(rate),
        'output-fields': 'saddr',
        'output-filter': f'success = 1 && repeat = 0 && sport = {port}',
    }
    async for j in zmap_scan(options, ranges):
        yield IPv4Address(j['saddr'])

#!/usr/bin/env python3

import json
import asyncio
from ipaddress import IPv4Address, IPv4Network
from collections.abc import AsyncGenerator
from ..utils import get_default_interface, argunparse
import os


async def zmap_scan(options: dict[str, str], ranges: list[IPv4Network]) -> AsyncGenerator[dict[str, str], None]:
    # TODO: we can't handle 100 kpps with this implementation.
    # I guess we don't consume stdout quickly enough
    # A solution would be to redirect the output to a temporary file and consume it slowly
    # We can use --summary to properly detect the end of the scan
    interface = get_default_interface()
    base_options = {
        'output-module': 'json',
        'interface': interface
    }
    args = argunparse(base_options | options, map(str, ranges))

    read, write = os.pipe()
    zmap_proc = await asyncio.subprocess.create_subprocess_exec('zmap', *args, stdout=write)
    os.close(write)
    ztee_proc = await asyncio.subprocess.create_subprocess_exec('ztee', '-r', '/dev/null', stdin=read, stdout=asyncio.subprocess.PIPE)
    os.close(read)
    assert ztee_proc.stdout
    async for line in ztee_proc.stdout:
        j = json.loads(line)
        assert isinstance(j, dict)
        yield j
    await zmap_proc.wait()
    await ztee_proc.wait()


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

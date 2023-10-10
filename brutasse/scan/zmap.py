#!/usr/bin/env python3

import json
import asyncio
from ipaddress import IPv4Address, IPv4Network
from collections.abc import AsyncGenerator


async def udp_scan(ranges: list[IPv4Network], rate: int, port: int, payload: bytes) -> AsyncGenerator[tuple[IPv4Address, bytes], None]:
    args: list[str] = [
        '--probe-module',   'udp',
        '--target-port',    f'{port}',
        '--probe-args',     f'hex:{payload.hex()}',
        '--rate',           f'{rate}',
        '--output-module',  'json',
        '--output-fields',  'saddr,data',
        '--output-filter',  f'success = 1 && repeat = 0 && sport = {port}',
        *map(str, ranges)
    ]
    proc = await asyncio.subprocess.create_subprocess_exec('zmap', *args, stdout=asyncio.subprocess.PIPE)
    assert proc.stdout
    async for line in proc.stdout:
        j = json.loads(line)
        yield IPv4Address(j['saddr']), bytes.fromhex(j['data'])
    await proc.wait()

#!/usr/bin/env python3

import asyncio
import errno


class ConnectionFailed(Exception):
    def __init__(self, reason: str, ip: str, port: int):
        super().__init__(f'Connection to {ip}:{port} failed ({reason})')


async def tcp_connect(host: str, port: int, timeout: float) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    try:
        return await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    except TimeoutError as e:
        raise ConnectionFailed('timeout', host, port)
    except OSError as e:
        match e.errno:
            case errno.ENETUNREACH:
                raise ConnectionFailed('network unreachable', host, port)
            case errno.ECONNREFUSED:
                raise ConnectionFailed('connection refused', host, port)
            case errno.EHOSTUNREACH:
                raise ConnectionFailed('host unreachable', host, port)
            case _:
                raise e

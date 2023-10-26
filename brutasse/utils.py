#!/usr/bin/env python3

import asyncio
import errno
import resource
import contextlib
from typing import TextIO
from pyroute2 import NDB
from collections.abc import Iterable
import ipaddress

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


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


@contextlib.contextmanager
def max_file_limit():
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
    try:
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))


def ips_from_file(file: TextIO) -> set[str]:
    return {l.strip() for l in file}


def get_default_interface() -> str:
    with NDB() as ndb:
        return ndb.interfaces[ndb.routes['default']['oif']]['ifname']


def argunparse(long_options: dict[str, str], positional: Iterable[str]):
    args: list[str] = []
    for k, v in long_options.items():
        args.extend([f'--{k}', v])
    args.extend(positional)
    return args

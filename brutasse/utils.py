#!/usr/bin/env python3

import asyncio
import errno
import resource
import contextlib
from ipaddress import IPv4Address, IPv6Address, IPv6Network
import functools
from typing import TextIO, ParamSpec, TypeVar
from collections.abc import Iterable, Callable, Coroutine
from pyroute2 import NDB

IPAddress = IPv4Address | IPv6Address
HostOrIP = str | IPAddress


class ConnectionFailed(Exception):
    def __init__(self, reason: str, ip: HostOrIP, port: int):
        super().__init__(f"Connection to {ip}:{port} failed ({reason})")


async def tcp_connect(
    host: IPAddress, port: int, timeout: float
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    try:
        return await asyncio.wait_for(asyncio.open_connection(str(host), port), timeout)
    except TimeoutError as e:
        raise ConnectionFailed("timeout", host, port) from e
    except OSError as e:
        match e.errno:
            case errno.ENETUNREACH:
                raise ConnectionFailed("network unreachable", host, port)
            case errno.ECONNREFUSED:
                raise ConnectionFailed("connection refused", host, port)
            case errno.EHOSTUNREACH:
                raise ConnectionFailed("host unreachable", host, port)
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
        return ndb.interfaces[ndb.routes["default"]["oif"]]["ifname"]


def argunparse(long_options: dict[str, str], positional: Iterable[str]):
    args: list[str] = []
    for k, v in long_options.items():
        args.extend([f"--{k}", v])
    args.extend(positional)
    return args


P = ParamSpec("P")
T = TypeVar("T")


def coro(func: Callable[P, Coroutine[None, None, T]]) -> Callable[P, T]:
    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        return asyncio.run(func(*args, **kwargs))

    return wrapped


mapped = IPv6Network("::ffff:0:0/96")


def ip_to_ipv6(ip: IPAddress) -> IPv6Address:
    match ip:
        case IPv4Address():
            return mapped[int(ip)]
        case IPv6Address():
            return ip


def ipv6_to_ip(ip: IPv6Address) -> IPAddress:
    if ip in mapped:
        return IPv4Address(int(ip) - int(mapped.network_address))
    else:
        return ip

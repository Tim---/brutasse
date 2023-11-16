#!/usr/bin/env python3

import asyncio
import click
from ipaddress import IPv4Network, IPv4Address, ip_address
from typing import Any, cast, TypeVar
from collections.abc import AsyncIterable, Collection, Coroutine, AsyncIterator
from brutasse.bgp.info import bgp_open_info
import json
import logging
import types
from .snmp.scan import scan_v1, scan_v2c, scan_v3
from .snmp.brute import brute
from .tftp.scan import tftp_scan
from .tftp.enum import enumerate_files
from .msf import Metasploit
from .parallel import progressbar_execute
from .utils import ConnectionFailed, coro


async def do_scan(workspace: str, port: int,
                  scan_func: AsyncIterable[tuple[IPv4Address, Any]]) -> None:
    with Metasploit(workspace) as db:
        async for addr, info in scan_func:
            print(addr, info)
            host = db.get_or_create_host(str(addr))
            service = db.get_or_create_service(host, 'udp', port)
            service.state = 'open'
            db.commit()

T = TypeVar('T')


async def parallel_helper(coros: Collection[Coroutine[None, None, T]],
                          parallelism: int, ignore: type | types.UnionType
                          ) -> AsyncIterator[T]:
    async for fut in progressbar_execute(coros, parallelism):
        try:
            yield await fut
        except Exception as e:
            if not isinstance(e, ignore):
                logging.error(repr(e))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option('--workspace', type=str, default='default')
@coro
async def tftp_enum(workspace: str) -> None:
    files = ['running-config', 'startup-config']
    with Metasploit(workspace) as db:
        services = db.get_services_by_port('udp', 69)
        addresses = ((ip_address(service.host.address), service.port)
                     for service in services)
        coros = [enumerate_files(ip, port, files=files)
                 for ip, port in addresses]
        async for (ip, filenames) in parallel_helper(coros, 100,
                                                     ignore=TimeoutError):
            for filename in filenames:
                print(ip, filename)


@cli.command()
@click.option('--workspace', type=str, default='default')
@coro
async def bgp_info(workspace: str) -> None:
    with Metasploit(workspace) as db:
        services = db.get_services_by_port('tcp', 179)
        addresses = ((ip_address(service.host.address), service.port)
                     for service in services)
        coros = [bgp_open_info(ip, port) for ip, port in addresses]
        ignore = (ConnectionFailed | asyncio.IncompleteReadError
                  | ConnectionResetError | TimeoutError)
        async for res in parallel_helper(coros, 100, ignore=ignore):
            print(res)


@cli.command()
@click.option('--workspace', type=str, default='default')
@coro
async def snmp_brute(workspace: str) -> None:
    communities = ['public', 'private']
    with Metasploit(workspace) as db:
        services = db.get_services_by_port('udp', 161)
        ips = [ip_address(service.host.address) for service in services]
        async for ip, port, community in brute(ips, communities):
            host = db.get_or_create_host(str(ip))
            service = db.get_or_create_service(host, 'udp', 161)
            note = db.get_or_create_note(service, 'brutasse.snmp.community')
            if not note.data:
                data: set[str] = set()
            else:
                data = set(cast(list[str], json.loads(note.data)))
            data.add(community)
            note.data = json.dumps(list(data))
            db.commit()
            print(ip, port, community)


@cli.group()
def scan() -> None:
    pass


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.option('--community', type=str, default='public')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
@coro
async def snmpv1(network: list[IPv4Network], rate: int, workspace: str,
                 community: str) -> None:
    scan_it = scan_v1(network, rate, community)
    await do_scan(workspace, 161, scan_it)


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.option('--community', type=str, default='public')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
@coro
async def snmpv2c(network: list[IPv4Network], rate: int, workspace: str,
                  community: str) -> None:
    scan_it = scan_v2c(network, rate, community)
    await do_scan(workspace, 161, scan_it)


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
@coro
async def snmpv3(network: list[IPv4Network], rate: int, workspace: str
                 ) -> None:
    scan_it = scan_v3(network, rate)
    await do_scan(workspace, 161, scan_it)


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
@coro
async def tftp(network: list[IPv4Network], rate: int, workspace: str) -> None:
    scan_it = tftp_scan(network, rate)
    await do_scan(workspace, 69, scan_it)

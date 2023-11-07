#!/usr/bin/env python3

import asyncio
import click
from ipaddress import IPv4Network, IPv4Address, ip_address
from typing import Any, cast
from collections.abc import AsyncIterable
from brutasse.bgp.info import bgp_open_info
import json
from .snmp.scan import scan_v3, scan_v2c
from .snmp.brute import brute
from .tftp.scan import tftp_scan
from .tftp.enum import enumerate_files
from .msf.db import Metasploit
from .parallel import progressbar_execute
from .utils import ConnectionFailed, coro


async def do_scan(workspace: str, port: int,
                  scan_func: AsyncIterable[tuple[IPv4Address, Any]]) -> None:
    msfdb = Metasploit(workspace)
    with msfdb.session() as session:
        async for addr, info in scan_func:
            print(addr, info)
            host = msfdb.get_or_create_host(session, str(addr))
            service = msfdb.get_or_create_service(
                session, host, 'udp', port)
            service.state = 'open'
            session.commit()


@click.group()
def cli() -> None:
    pass


@cli.command()
@coro
async def tftp_enum() -> None:
    msfdb = Metasploit('default')
    files = ['running-config', 'startup-config']
    with msfdb.session() as session:
        services = msfdb.get_services_by_port(session, 'udp', 69)
        addresses = [service.host.address for service in services]
        coros = [enumerate_files(addr, files) for addr in addresses]
        async for fut in progressbar_execute(coros, 100):
            try:
                ip, filenames = await fut
                for filename in filenames:
                    print(ip, filename)
            except Exception as e:
                print(repr(e))


@cli.command()
@coro
async def bgp_info() -> None:
    msfdb = Metasploit('default')
    with msfdb.session() as session:
        services = msfdb.get_services_by_port(session, 'tcp', 179)
        addresses = [ip_address(service.host.address) for service in services]
        coros = [bgp_open_info(addr, 179) for addr in addresses]
        async for fut in progressbar_execute(coros, 100):
            try:
                res = fut.result()
                print(res)
            except ConnectionFailed:
                pass
            except (asyncio.IncompleteReadError, ConnectionResetError,
                    TimeoutError):
                pass
            except Exception as e:
                print(repr(e))


@cli.command()
@coro
async def snmp_brute() -> None:
    communities = ['public', 'private', 'Public',
                   'Private', 'ro', 'rw', 'RO', 'RW']
    msfdb = Metasploit('default')
    with msfdb.session() as session:
        services = msfdb.get_services_by_port(session, 'udp', 161)
        ips = [IPv4Address(service.host.address) for service in services]
        async for ip, port, community in brute(ips, communities):
            host = msfdb.get_or_create_host(session, str(ip))
            service = msfdb.get_or_create_service(session, host, 'udp', 161)
            note = msfdb.get_or_create_note(
                session, service, 'brutasse.snmp.community')
            if not note.data:
                data: set[str] = set()
            else:
                data = set(cast(list[str], json.loads(note.data)))
            data.add(community)
            note.data = json.dumps(list(data))
            session.commit()
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

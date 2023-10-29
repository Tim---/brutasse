#!/usr/bin/env python3

import click
import asyncio
from ipaddress import IPv4Network, IPv4Address
from typing import Any
from collections.abc import AsyncIterable
from .snmp.scan import scan_v3, scan_v2c
from .tftp.scan import tftp_scan
from .tftp.enum import enumerate_files
from .msf.db import Metasploit
from .parallel import progressbar_execute


async def do_scan(workspace: str, port: int, scan_func: AsyncIterable[tuple[IPv4Address, Any]]) -> None:
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
def tftp_enum() -> None:
    async def func():
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
    asyncio.run(func())


@cli.group()
def scan() -> None:
    pass


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.option('--community', type=str, default='public')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
def snmpv2c(network: list[IPv4Network], rate: int, workspace: str, community: str) -> None:
    scan_it = scan_v2c(network, rate, community)
    asyncio.run(do_scan(workspace, 161, scan_it))


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
def snmpv3(network: list[IPv4Network], rate: int, workspace: str) -> None:
    scan_it = scan_v3(network, rate)
    asyncio.run(do_scan(workspace, 161, scan_it))


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.argument('network', type=IPv4Network, nargs=-1, required=True)
def tftp(network: list[IPv4Network], rate: int, workspace: str) -> None:
    scan_it = tftp_scan(network, rate)
    asyncio.run(do_scan(workspace, 69, scan_it))

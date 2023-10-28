#!/usr/bin/env python3

import click
import asyncio
from ipaddress import IPv4Network, IPv4Address
from typing import Any
from collections.abc import AsyncIterable
from .snmp.scan import scan_v3, scan_v2c
from .msf.db import Metasploit


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


@cli.group()
def scan() -> None:
    pass


@scan.command()
@click.option('--rate', type=int, default=10000)
@click.option('--workspace', type=str, default='default')
@click.option('--community', type=str, default='default')
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


if __name__ == "__main__":
    cli()

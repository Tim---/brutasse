#!/usr/bin/env python3

import asyncio
import json
import logging
import types
from collections.abc import AsyncIterable, AsyncIterator, Collection, Coroutine
from ipaddress import IPv4Address, IPv4Network, ip_address
from typing import Any, Optional, TypeVar, cast

import click
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from brutasse import bgp, snmp, tftp
from brutasse.msf import Metasploit, Note, Service
from brutasse.parallel import progressbar_execute
from brutasse.utils import ConnectionFailed, IPAddress, coro


async def do_scan(
    workspace: str, port: int, scan_func: AsyncIterable[tuple[IPv4Address, Any]]
) -> None:
    with Metasploit(workspace) as db:
        async for addr, info in scan_func:
            print(addr, info)
            host = db.get_or_create_host(str(addr))
            service = db.get_or_create_service(host, "udp", port)
            service.state = "open"
            db.commit()


T = TypeVar("T")


async def parallel_helper(
    coros: Collection[Coroutine[None, None, T]],
    parallelism: int,
    ignore: Optional[type | types.UnionType] = None,
) -> AsyncIterator[T]:
    async for fut in progressbar_execute(coros, parallelism):
        try:
            yield await fut
        except Exception as e:
            if ignore is None or not isinstance(e, ignore):
                logging.error(repr(e))
                # logging.exception(e)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--workspace", type=str, default="default")
@coro
async def tftp_enum(workspace: str) -> None:
    filenames = ["running-config", "startup-config"]
    with Metasploit(workspace) as db:
        services = db.get_services_by_port("udp", 69)
        addresses = (
            (ip_address(service.host.address), service.port) for service in services
        )

        async def inner(ip: IPAddress, port: int) -> tuple[IPAddress, int, list[str]]:
            found = await tftp.enumerate_files(ip, port, filenames=filenames)
            return ip, port, found

        coros = [inner(ip, port) for ip, port in addresses]
        async for ip, port, found in parallel_helper(coros, 100, ignore=TimeoutError):
            for filename in found:
                print(ip, port, filename)


@cli.command()
@click.option("--workspace", type=str, default="default")
@coro
async def bgp_info(workspace: str) -> None:
    with Metasploit(workspace) as db:
        services = db.get_services_by_port("tcp", 179)
        addresses = (
            (ip_address(service.host.address), service.port) for service in services
        )

        async def inner(
            ip: IPAddress, port: int
        ) -> tuple[IPAddress, int, int, IPv4Address]:
            asn, bgp_id = await bgp.bgp_open_info(ip, port)
            return ip, port, asn, bgp_id

        coros = [inner(ip, port) for ip, port in addresses]
        ignore = (
            ConnectionFailed
            | asyncio.IncompleteReadError
            | ConnectionResetError
            | TimeoutError
        )
        async for ip, port, asn, bgp_id in parallel_helper(coros, 100, ignore=ignore):
            print(ip, port, asn, bgp_id)


@cli.command()
@click.option("--workspace", type=str, default="default")
@coro
async def snmp_brute(workspace: str) -> None:
    communities = ["public", "private"]
    with Metasploit(workspace) as db:
        services = db.get_services_by_port("udp", 161)
        ips = [ip_address(service.host.address) for service in services]
        async for ip, port, community in snmp.bruteforce_communities_v2c(
            ips, communities
        ):
            host = db.get_or_create_host(str(ip))
            service = db.get_or_create_service(host, "udp", 161)
            note = db.get_or_create_note(service, "brutasse.snmp.community")
            if not note.data:
                data: set[str] = set()
            else:
                data = set(cast(list[str], json.loads(note.data)))
            data.add(community)
            note.data = json.dumps(list(data))
            db.commit()
            print(ip, port, community)


def get_authenticated_snmp_services(db: Metasploit):
    stmt = (
        select(Note)
        .where(Note.ntype == "brutasse.snmp.community")
        .options(joinedload(Note.service).joinedload(Service.host))
    )

    for note in db.session.execute(stmt).scalars():
        ip = note.service.host.address
        port = note.service.port
        communities = set(json.loads(note.data))
        # TODO: try all communities ?
        yield ip, port, communities.pop()


@cli.command()
@click.option("--workspace", type=str, default="default")
@coro
async def snmp_info(workspace: str) -> None:
    with Metasploit(workspace) as db:

        async def inner(
            ip: str, port: int, community: str
        ) -> tuple[str, int, dict[str, str]]:
            infos = await asyncio.wait_for(snmp.get_sys_info(ip, port, community), 5)
            return ip, port, infos

        coros = [
            inner(ip, port, community)
            for ip, port, community in get_authenticated_snmp_services(db)
        ]
        async for ip, port, res in parallel_helper(
            coros, parallelism=100, ignore=TimeoutError
        ):
            print(f"{ip}:{port} {res}")


@cli.group()
def scan() -> None:
    pass


@scan.command("snmpv1")
@click.option("--rate", type=int, default=10000)
@click.option("--workspace", type=str, default="default")
@click.option("--community", type=str, default="public")
@click.argument("network", type=IPv4Network, nargs=-1, required=True)
@coro
async def scan_snmpv1(
    network: list[IPv4Network], rate: int, workspace: str, community: str
) -> None:
    scan_it = snmp.scan_v1(network, rate, community)
    await do_scan(workspace, 161, scan_it)


@scan.command("snmpv2c")
@click.option("--rate", type=int, default=10000)
@click.option("--workspace", type=str, default="default")
@click.option("--community", type=str, default="public")
@click.argument("network", type=IPv4Network, nargs=-1, required=True)
@coro
async def scan_snmpv2c(
    network: list[IPv4Network], rate: int, workspace: str, community: str
) -> None:
    scan_it = snmp.scan_v2c(network, rate, community)
    await do_scan(workspace, 161, scan_it)


@scan.command("snmpv3")
@click.option("--rate", type=int, default=10000)
@click.option("--workspace", type=str, default="default")
@click.argument("network", type=IPv4Network, nargs=-1, required=True)
@coro
async def scan_snmpv3(network: list[IPv4Network], rate: int, workspace: str) -> None:
    scan_it = snmp.scan_v3(network, rate)
    await do_scan(workspace, 161, scan_it)


@scan.command("tftp")
@click.option("--rate", type=int, default=10000)
@click.option("--workspace", type=str, default="default")
@click.argument("network", type=IPv4Network, nargs=-1, required=True)
@coro
async def scan_tftp(network: list[IPv4Network], rate: int, workspace: str) -> None:
    scan_it = tftp.tftp_scan(network, rate)
    await do_scan(workspace, 69, scan_it)

#!/usr/bin/env python3

import asyncio
import json
import os
from asyncio.subprocess import PIPE, create_subprocess_exec
from collections.abc import AsyncIterator, Iterable
from ipaddress import IPv4Address, IPv4Network, IPv6Address
from typing import Any, Optional

from brutasse.utils import (
    IPAddress,
    argunparse,
    get_default_interface,
    ip_to_ipv6,
    ipv6_to_ip,
)


async def zmap_scan(
    options: dict[str, str], networks: list[IPv4Network]
) -> AsyncIterator[dict[str, str]]:
    interface = get_default_interface()
    base_options = {"output-module": "json", "interface": interface}
    args = argunparse(base_options | options, map(str, networks))

    read, write = os.pipe()
    zmap_proc = await create_subprocess_exec("zmap", *args, stdout=write)
    os.close(write)
    ztee_proc = await create_subprocess_exec(
        "ztee", "-r", "/dev/null", stdin=read, stdout=PIPE
    )
    os.close(read)
    assert ztee_proc.stdout
    async for line in ztee_proc.stdout:
        j = json.loads(line)
        assert isinstance(j, dict)
        yield j
    await zmap_proc.wait()
    await ztee_proc.wait()


async def net_udp_scan(
    networks: list[IPv4Network], rate: int, port: int, payload: bytes
) -> AsyncIterator[tuple[IPv4Address, bytes]]:
    """Perform a zmap UDP scan on IPv4 networks.

    :param networks: networks to scan
    :param rate: sending rate in packets per second
    :param port: UDP port to scan
    :param payload: data to send
    :return: an iterator of responding IPs with their payload
    """
    options = {
        "probe-module": "udp",
        "target-port": str(port),
        "probe-args": f"hex:{payload.hex()}",
        "rate": str(rate),
        "output-fields": "saddr,data",
        "output-filter": f"success = 1 && repeat = 0 && sport = {port}",
    }
    async for j in zmap_scan(options, networks):
        yield IPv4Address(j["saddr"]), bytes.fromhex(j.get("data", ""))


async def net_tcp_scan(
    networks: list[IPv4Network], rate: int, port: int
) -> AsyncIterator[IPv4Address]:
    """Perform a zmap TCP SYN scan on IPv4 networks.

    :param networks: networks to scan
    :param rate: sending rate in packets per second
    :param port: TCP port to scan
    :return: an iterator of responding IPs
    """
    options = {
        "probe-module": "tcp_synscan",
        "target-port": str(port),
        "rate": str(rate),
        "output-fields": "saddr",
        "output-filter": f"success = 1 && repeat = 0 && sport = {port}",
    }
    async for j in zmap_scan(options, networks):
        yield IPv4Address(j["saddr"])


Addr = tuple[IPAddress, int]
Pkt = tuple[IPAddress, int, bytes]


class _UdpScanProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue[Optional[Pkt]]):
        self.queue = queue

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def datagram_received(
        self, data: bytes, addr: tuple[str | Any, int, int, int]
    ) -> None:
        ip, port, _, _ = addr
        ip = ipv6_to_ip(IPv6Address(ip))
        self.queue.put_nowait((ip, port, data))

    def connection_lost(self, exc: Exception | None) -> None:
        pass


async def ip_udp_sender(
    transport: asyncio.DatagramTransport,
    queue: asyncio.Queue[Optional[Pkt]],
    pkt_gen: Iterable[Pkt],
    cooldown: float,
    delay: float,
) -> None:
    for ip, port, data in pkt_gen:
        transport.sendto(data, (str(ip_to_ipv6(ip)), port))
        await asyncio.sleep(delay)
    await asyncio.sleep(cooldown)
    await queue.put(None)


async def ip_udp_scan(
    pkt_gen: Iterable[Pkt],
    delay: float = 0.001,
    cooldown: float = 1,
) -> AsyncIterator[Pkt]:
    """Perform an UDP scan on IP addresses.

    This is a "slow" scanner, in pure Python.
    However, it supports IPv6 and allows to specify a different port and payload per host.

    :param pkt_gen: list of (IP, port, data) to send
    :param delay: delay between each outgoing packet
    :param cooldown: time to wait for packets after the last one has been sent
    :return: an iterator of responding IPs with their payload
    """
    queue: asyncio.Queue[Optional[Pkt]] = asyncio.Queue()

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _UdpScanProtocol(queue), local_addr=("::", 0)
    )

    try:
        task = asyncio.create_task(
            ip_udp_sender(transport, queue, pkt_gen, cooldown, delay)
        )
        while item := await queue.get():
            yield item
        await task
    finally:
        transport.close()

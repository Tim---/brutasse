#!/usr/bin/env python3

import asyncio

from anyio import create_connected_udp_socket

from ..utils import IPAddress
from .packet import Data, Error, ErrorCode, Msg, ReadRequest


async def enumerate_files(
    ip: IPAddress,
    port: int,
    files: list[str],
    timeout: int = 1,
    retries: int = 1,
    mode: str = "netascii",
) -> tuple[IPAddress, list[str]]:
    res: list[str] = []
    async with await create_connected_udp_socket(
        remote_host=ip, remote_port=port
    ) as udp:
        for filename in files:
            for _ in range(retries + 1):
                msg = ReadRequest(filename=filename, mode=mode)
                await udp.send(msg.build())

                try:
                    raw = await asyncio.wait_for(udp.receive(), timeout)
                except TimeoutError:
                    continue
                resp = Msg.parse(raw)
                break
            else:
                raise TimeoutError(f"Max retries exceeded for {ip}")

            match resp:
                case Error():
                    pass
                case Data():
                    res.append(filename)
                    msg = Error(code=ErrorCode.NOT_DEFINED, msg="Plz stop")
                    await udp.send(msg.build())
                case _:
                    raise NotImplementedError(f"Unexpected response {resp}")
    return ip, res

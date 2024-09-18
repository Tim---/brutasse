#!/usr/bin/env python3

import asyncio

from anyio import create_connected_udp_socket

from brutasse.tftp.packet import Data, Error, ErrorCode, Msg, ReadRequest
from brutasse.utils import IPAddress


async def enumerate_files(
    address: IPAddress,
    port: int,
    filenames: list[str],
    timeout: float = 1.0,
    retries: int = 1,
    mode: str = "netascii",
) -> list[str]:
    """Enumerate files over TFTP.

    :param address: IP address of the target
    :param port: UDP port
    :param files: list of filenames to try
    :param timeout: time to wait for each response
    :param retries: number of retries for each request
    :param mode: TFTP mode
    :return: a list of discovered files
    """
    res: list[str] = []
    async with await create_connected_udp_socket(
        remote_host=address, remote_port=port
    ) as udp:
        for filename in filenames:
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
                raise TimeoutError(f"Max retries exceeded for {address}")

            match resp:
                case Error():
                    pass
                case Data():
                    res.append(filename)
                    msg = Error(code=ErrorCode.NOT_DEFINED, msg="Plz stop")
                    await udp.send(msg.build())
                case _:
                    raise NotImplementedError(f"Unexpected response {resp}")
    return res

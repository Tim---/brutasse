#!/usr/bin/env python3

import asyncio
from .packet import Msg, ReadRequest, Error, Data
from anyio import create_connected_udp_socket


async def enumerate_files(ip: str, files: list[str], timeout: int = 1,
                          retries: int = 1, mode: str = 'netascii'
                          ) -> tuple[str, list[str]]:
    res: list[str] = []
    async with await create_connected_udp_socket(remote_host=ip,
                                                 remote_port=69) as udp:
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
                raise TimeoutError(f'Max retries exceeded for {ip}')

            match resp:
                case Error(msg=msg):
                    pass
                case Data():
                    res.append(filename)
                    msg = Error(code=0, msg='Plz stop')
                    await udp.send(msg.build())
                case _:
                    raise NotImplementedError(
                        f'Unexpected response {resp}')
    return ip, res

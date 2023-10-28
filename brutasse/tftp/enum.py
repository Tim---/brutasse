#!/usr/bin/env python3

import asyncio
from .proto import Pkt, ReadRequest, Error, Data
from anyio import create_connected_udp_socket


async def enumerate_files(ip: str, files: list[str], timeout: int = 1, retries: int = 1):
    async with await create_connected_udp_socket(remote_host=ip, remote_port=69) as udp:
        for filename in files:
            for _ in range(retries + 1):
                msg = Pkt(body=ReadRequest(filename=filename, mode='octet'))
                await udp.send(msg.build())

                try:
                    raw = await asyncio.wait_for(udp.receive(), timeout)
                except TimeoutError:
                    continue
                resp = Pkt.parse(raw)
                break
            else:
                raise TimeoutError(f'Max retries exceeded for {ip}')

            match resp:
                case Pkt(body=Error(code=code, msg=msg)):
                    pass
                case Pkt(body=Data(block_num=block_num, data=data)):
                    print(ip, filename)
                    msg = Pkt(body=Error(code=0, msg='Plz stop'))
                    await udp.send(msg.build())
                case _:
                    raise NotImplementedError(
                        f'Unexpected response {resp}')

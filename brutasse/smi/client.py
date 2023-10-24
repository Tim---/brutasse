#!/usr/bin/env python3

from .proto import SmiStream, Pkt, CapabilitiesReq, CapabilitiesResp


class IbdClient:
    def __init__(self, stream: SmiStream):
        self.stream = stream

    async def get_capabilities(self):
        req = Pkt(version=1, body=CapabilitiesReq(1, 0))
        await self.stream.write_msg(req)
        resp = await self.stream.read_msg()
        match resp:
            case Pkt(version=0, body=CapabilitiesResp(1, 0)):
                pass
            case _:
                raise Exception(f'Unexpected message {resp}')

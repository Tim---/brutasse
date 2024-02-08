#!/usr/bin/env python3

from .proto import (
    CapabilitiesReq,
    CapabilitiesResp,
    ConfigBackupReqResp,
    Pkt,
    SelfConfigBackupReq,
    SmiStream,
    TlvLocal,
    TlvRemote,
    TlvSeq,
)


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
                raise Exception(f"Unexpected message {resp}")

    async def backup_local(self):
        req = Pkt(
            version=0,
            body=SelfConfigBackupReq(
                tlvs=[
                    TlvSeq(1, 0, bytes(6)),
                    TlvLocal("configure tftp-server nvram:startup-config"),
                ]
            ),
        )
        await self.stream.write_msg(req)

        # Note: the switch will connect back on port 4786 to send a response

        # TODO: do the tftp get

        req = Pkt(version=0, body=ConfigBackupReqResp(result=1))
        await self.stream.write_msg(req)

        # Note: the switch will connect back on port 4786 to send a response

    async def backup_remote(self, ip: str):
        # TODO: listen with tftp server

        req = Pkt(
            version=0,
            body=SelfConfigBackupReq(
                tlvs=[
                    TlvSeq(1, 0, bytes(6)),
                    TlvRemote(
                        "copy system:running-config flash:/config.text",
                        "copy flash:/config.text tftp://{ip}/config.text",
                        "",
                    ),
                ]
            ),
        )
        await self.stream.write_msg(req)

        # Note: the switch will connect back on port 4786 to send a response

#!/usr/bin/env python3

from brutasse.smi.proto import (
    BackupDone,
    BackupReq,
    CapabilitiesReq,
    CapabilitiesResp,
    Pkt,
    TlvLocal,
    TlvRemote,
    TlvSeq,
)
from brutasse.utils import Stream


class IbdClient:
    def __init__(self, stream: Stream):
        self.stream = stream

    async def get_capabilities(self):
        req = Pkt(version=0, body=CapabilitiesReq(1, 0))
        await req.build_stream(self.stream)

        resp = await Pkt.parse_stream(self.stream)
        match resp:
            case Pkt(version=0, body=CapabilitiesResp(1, 0)):
                pass
            case _:
                raise Exception(f"Unexpected message {resp}")

    async def backup_local(self):
        req = Pkt(
            version=0,
            body=BackupReq(
                tlvs=[
                    TlvSeq(1, 0, bytes(6)),
                    TlvLocal("configure tftp-server nvram:startup-config"),
                ]
            ),
        )
        await req.build_stream(self.stream)

        # Note: the switch will connect back on port 4786 to send a response

        # TODO: do the tftp get

        req = Pkt(version=0, body=BackupDone(result=1))
        await req.build_stream(self.stream)

        # Note: the switch will connect back on port 4786 to send a response

    async def backup_remote(self, ip: str):
        # TODO: listen with tftp server

        req = Pkt(
            version=0,
            body=BackupReq(
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
        await req.build_stream(self.stream)

        # Note: the switch will connect back on port 4786 to send a response

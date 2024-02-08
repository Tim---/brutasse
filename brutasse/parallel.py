#!/usr/bin/env python3

import asyncio
from collections.abc import AsyncIterator, Collection, Coroutine, Iterable
from typing import TypeVar

import progressbar
from termcolor import colored

T = TypeVar("T")

# TODO: maybe it would be better to take the coroutine function
# and iterator of parameters as an argument ?
# This would avoid creating coroutines (which need to be closed)


async def parallel_execute(
    coros: Iterable[Coroutine[None, None, T]], parallelism: int
) -> AsyncIterator[asyncio.Task[T]]:
    dltasks: set[asyncio.Task[T]] = set()
    it = iter(coros)
    try:
        for coro in it:
            dltasks.add(asyncio.create_task(coro))
            if len(dltasks) >= parallelism:
                done, dltasks = await asyncio.wait(
                    dltasks, return_when=asyncio.FIRST_COMPLETED
                )
                for d in done:
                    yield d
    except asyncio.CancelledError:
        for coro in it:
            coro.close()
    while dltasks:
        done, dltasks = await asyncio.wait(dltasks, return_when=asyncio.FIRST_COMPLETED)
        for d in done:
            yield d


class MyProgressBar(progressbar.ProgressBar):
    OK = 0
    ERROR = 1
    PENDING = 2

    def __init__(self, n: int):
        markers = [
            colored("█", "green"),  # ok
            colored("█", "red"),  # ko
            " ",  # not started/processing
        ]
        widgets = [
            progressbar.Variable("done"),
            ", ",
            progressbar.Variable("error"),
            progressbar.MultiRangeBar("amounts", markers=markers),
        ]
        self.amounts = [0, 0, n]
        super().__init__(widgets=widgets, redirect_stdout=True, redirect_stderr=True)

    def move(self, src: int, dst: int):
        self.amounts[src] -= 1
        self.amounts[dst] += 1
        self.update(
            done=self.amounts[self.OK],
            error=self.amounts[self.ERROR],
            amounts=self.amounts,
            force=True,
        )


async def progressbar_execute(
    coros: Collection[Coroutine[None, None, T]], parallelism: int
) -> AsyncIterator[asyncio.Task[T]]:
    with MyProgressBar(len(coros)) as bar:
        async for fut in parallel_execute(coros, parallelism):
            bar.move(bar.PENDING, bar.OK if fut.exception() is None else bar.ERROR)
            yield fut

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def async_retry(
    func: Callable[..., Awaitable[T]],
    *args,
    retries: int = 2,
    delay: float = 0.25,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs,
) -> T:
    attempt = 0
    wait_time = delay
    while True:
        try:
            return await func(*args, **kwargs)
        except exceptions:
            attempt += 1
            if attempt > retries:
                raise
            await asyncio.sleep(wait_time)
            wait_time *= backoff

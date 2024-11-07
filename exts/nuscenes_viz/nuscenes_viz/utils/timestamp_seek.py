'''Utilities for seeking timestamps'''

import bisect
from typing import TypeVar

__all__ = ['seek_by']

T = TypeVar('T')


def seek_by(
    timestamp: int,
    timestamps: list[int],
    values: list[T],
) -> T:
    '''Seek the value by given timestamps'''
    index = bisect.bisect_left(
        a=timestamps,
        x=timestamp,
        hi=len(timestamps) - 1,
    )
    if timestamp < timestamps[index]:
        index = max(0, index - 1)
    return values[index]

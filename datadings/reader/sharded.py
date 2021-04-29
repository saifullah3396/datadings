from typing import Union
from typing import Iterable
import itertools as it
from bisect import bisect_left
from bisect import bisect_right
from glob import glob
from pathlib import Path

from .reader import Reader
from .msgpack import MsgpackReader


def _canonical_reader(v):
    if isinstance(v, Reader):
        return v
    elif isinstance(v, (str, Path)):
        return MsgpackReader(v)
    else:
        raise ValueError('need either msgpack path or Reader instance')


class ShardedReader(Reader):
    """
    A Reader that combines several shards into one.
    Shards can be specified either as a glob pattern ``dir/*.msgpack``
    for msgpack files, or an iterable of individual shards.
    Each shard can be a string, :py:class:`Path <pathlib.Path>`,
    or :class:`Reader <.reader.Reader>`.

    Parameters:
        shards: glob pattern or a list of strings, Path objects or Readers
    """
    def __init__(self, shards: Union[str, Path, Iterable[Union[str, Path, Reader]]]):
        super().__init__()
        if isinstance(shards, (str, Path)):
            shards = sorted(glob(str(shards)))
        self._readers = [_canonical_reader(shard) for shard in shards]
        self._offsets = list(it.accumulate(it.chain(
            (0,), (len(reader) for reader in self._readers)
        )))
        self._len = self._offsets.pop(-1)

    def __len__(self):
        return self._len

    def __contains__(self, key):
        return any(key in reader for reader in self._readers)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for reader in self._readers:
            reader.__exit__(exc_type, exc_val, exc_tb)

    def find_key(self, index):
        reader_i = bisect_right(self._offsets, index) - 1
        offset = index - self._offsets[reader_i]
        with self._readers[reader_i] as reader:
            return reader.find_key(offset)

    def find_index(self, key):
        for i, reader in enumerate(self._readers):
            if key in reader:
                with reader:
                    return self._offsets[i] + reader.find_index(key)
        raise KeyError(key)

    def get(self, index, yield_key=False, raw=False, copy=True):
        reader_i = bisect_right(self._offsets, index) - 1
        offset = index - self._offsets[reader_i]
        with self._readers[reader_i] as reader:
            return reader.get(offset, yield_key, raw, copy)

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        return self.iter(start, stop, yield_key, raw, copy)

    def _iter_impl(
            self,
            start=None,
            stop=None,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        reader_start = bisect_right(self._offsets, start) - 1
        reader_stop = bisect_left(self._offsets, stop)
        for i in range(reader_start, reader_stop):
            offset = self._offsets[i]
            with self._readers[i] as reader:
                yield from reader.iter(
                        max(0, start-offset),
                        stop-offset,
                        yield_key,
                        raw,
                        copy,
                        chunk_size,
                )

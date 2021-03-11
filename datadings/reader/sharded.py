import itertools as it
from bisect import bisect_left

from .reader import Reader


class ShardedReader(Reader):
    def __init__(self, readers):
        super().__init__()
        self._readers = readers
        self._offsets = list(it.accumulate(it.chain(
            (0,), (len(reader) for reader in readers)
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
        reader_i = bisect_left(self._offsets, index)
        offset = index - self._offsets[reader_i]
        return self._readers[reader_i].find_key(offset)

    def find_index(self, key):
        for i, reader in enumerate(self._readers):
            if key in reader:
                return self._offsets[i] + reader.find_index(key)
        raise KeyError(key)

    def get(self, index, yield_key=False, raw=False, copy=True):
        reader_i = bisect_left(self._offsets, index)
        offset = index - self._offsets[reader_i]
        return self._readers[reader_i].get(offset, yield_key, raw, copy)

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
        reader_start = bisect_left(self._offsets, start)
        reader_stop = bisect_left(self._offsets, stop)
        for reader, offset in zip(
                self._readers[reader_start:reader_stop],
                self._offsets[reader_start:reader_stop],
        ):
            for sample in reader.iter(
                    max(0, start-offset),
                    stop-offset,
                    yield_key,
                    raw,
                    copy,
                    chunk_size,
            ):
                self._i += 1
                yield sample

import itertools as it
from bisect import bisect_left
from glob import glob

from .reader import Reader
from .msgpack import MsgpackReader


class ShardedReader(Reader):
    def __init__(self, paths):
        super().__init__()
        if isinstance(paths, str):
            if '*' in paths:
                paths = glob(paths)
            else:
                raise ValueError('need multiple paths or glob pattern')
        self._paths = paths
        self._num_shards = len(paths)
        self._offsets = list(it.accumulate(it.chain(
            (0,), (self._reader(i) for i in range(self._num_shards))
        )))
        self._len = self._offsets.pop(-1)

    def _reader(self, index):
        return MsgpackReader(self._paths[index])

    def __len__(self):
        return self._len

    def __contains__(self, key):
        return any(key in self._reader(i) for i in range(self._num_shards))

    def __exit__(self, exc_type, exc_val, exc_tb):
        # for reader in self._readers:
        #     reader.__exit__(exc_type, exc_val, exc_tb)
        pass

    def find_key(self, index):
        reader_i = bisect_left(self._offsets, index)
        offset = index - self._offsets[reader_i]
        with self._reader(reader_i) as reader:
            return reader.find_key(offset)

    def find_index(self, key):
        for i in range(self._num_shards):
            with self._reader(i) as reader:
                if key in reader:
                    return self._offsets[i] + reader.find_index(key)
        raise KeyError(key)

    def get(self, index, yield_key=False, raw=False, copy=True):
        reader_i = bisect_left(self._offsets, index)
        offset = index - self._offsets[reader_i]
        with self._reader(reader_i) as reader:
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
        reader_start = bisect_left(self._offsets, start)
        reader_stop = bisect_left(self._offsets, stop) + 1
        for i in range(reader_start, reader_stop):
            offset = self._offsets[i]
            with self._reader(i) as reader:
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

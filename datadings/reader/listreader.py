from __future__ import print_function, division, unicode_literals

from .reader import Reader, pack


class ListReader(Reader):
    """
    Abstract base class for dataset readers.

    Subclasses must implement iteration and seeking methods.

    Readers can be used as a context manager:

        with Reader('dataset.msgpack') as reader:
            for sample in reader:
                [do dataset things]
    """
    def __init__(self, samples):
        self._samples = samples
        self._index = {s.get('key', 1): i for i, s in enumerate(samples)}
        self._keys = {i: s.get('key', i) for i, s in enumerate(samples)}
        self._i = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter(self, yield_key=False):
        """
        :param yield_key: if True, yields (key, sample) pairs
        """
        if yield_key:
            while 1:
                yield self.get_key(), self.next()
        else:
            while 1:
                yield self.next()

    __iter__ = iter

    def __len__(self):
        return len(self._samples)

    def __next__(self):
        return self._samples[self._i]

    next = __next__

    def rawnext(self):
        """
        Return the next sample as raw bytes.
        :return:
        """
        return pack(self.next())

    def rawiter(self, yield_key=False):
        """
        Like iter, but yields raw bytes.

        :param yield_key: if True, yields (key, sample) pairs
        """
        if yield_key:
            while 1:
                yield self.get_key(), self.rawnext()
        else:
            while 1:
                yield self.rawnext()

    def seek_index(self, index):
        """
        Seek to the given index.
        """
        self._i = index

    seek = seek_index

    def seek_key(self, key):
        self._i = self._index.get(key, None) or self._i

    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        return self._keys.get(index or self._i, self._i)
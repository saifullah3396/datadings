from __future__ import print_function, division, unicode_literals

import random
from abc import ABCMeta, abstractmethod


class _Augment(object):
    """
    Augment the iteration order of reader.
    Not thread safe!
    """
    __metaclass__ = ABCMeta

    def __init__(self, reader):
        """
        Reader to shuffle.
        Not thread safe!

        :param reader: Reader to shuffle
        """
        self._reader = reader

    def __enter__(self):
        self._reader.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._reader.__exit__(exc_type, exc_val, exc_tb)

    def __len__(self):
        return len(self._reader)

    @abstractmethod
    def iter(self, yield_key=False):
        pass

    @abstractmethod
    def rawiter(self, yield_key=False):
        pass


class Shuffler(_Augment):
    """
    Iterate over the contents of a Reader in random order.
    Not thread safe!
    """
    def iter(self, yield_key=False):
        """
        Iterate over the wrapper Reader in random order.

        :param yield_key: if True, yields (key, sample) pairs
        """
        n = len(self._reader)
        order = list(range(n))
        random.shuffle(order)
        if yield_key:
            for i in order:
                self._reader.seek_index(i)
                yield self._reader.get_key(), self._reader.next()
        else:
            for i in order:
                self._reader.seek_index(i)
                yield self._reader.next()

    __iter__ = iter

    def rawiter(self, yield_key=False):
        """
        Iterate over the wrapper Reader in random order.
        Yields samples as raw bytes.

        :param yield_key: if True, yields (key, sample) pairs
        """
        n = len(self._reader)
        order = list(range(n))
        random.shuffle(order)
        if yield_key:
            for i in order:
                self._reader.seek_index(i)
                yield self._reader.get_key(), self._reader.rawnext()
        else:
            for i in order:
                self._reader.seek_index(i)
                yield self._reader.rawnext()


class Cycler(_Augment):
    """
    Cycle over the contents of a Reader or Shuffler.
    Not thread safe!
    """
    def iter(self, yield_key=False):
        """
        Cycle over the wrapper Reader.

        :param yield_key: if True, yields (key, sample) pairs
        """
        while 1:
            for sample in self._reader.iter(yield_key):
                yield sample
            self._reader.seek_index(0)

    __iter__ = iter

    def rawiter(self, yield_key=False):
        """
        Cycle over the wrapper Reader.
        Yields samples as raw bytes.

        :param yield_key: if True, yields (key, sample) pairs
        """
        while 1:
            for sample in self._reader.rawiter(yield_key):
                yield sample
            self._reader.seek_index(0)
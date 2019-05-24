from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import random
from abc import ABCMeta, abstractmethod
from copy import copy


class Augment(object):
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

    @abstractmethod
    def seek(self, index):
        pass


class Shuffler(Augment):
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
                self._reader.seek(i)
                yield self._reader.get_key(), self._reader.next()
        else:
            for i in order:
                self._reader.seek(i)
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

    def seek(self, index):
        self._reader.seek(index)


class Cycler(Augment):
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
            self._reader.seek(0)

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
            self._reader.seek(0)

    def seek(self, index):
        self._reader.seek(index)


class Range(Augment):
    def __init__(self, reader, start=0, stop=None, num=None):
        """
        Extract a range of samples from a given reader.
        Not thread safe!

        Either stop or num must be given.
        If both are given, an assert will be triggered if
        stop - start != num.
        An assert will also trigger if stop > len(reader).
        Same holds for start + num > len(reader)

        :param reader: Reader to sample
        :param start: index to start from
        :param stop: index to stop at
        :param num: number of samples iterators will yield
        """
        Augment.__init__(self, reader)
        self.start = start
        if stop is None:
            if num is None:
                stop = len(reader)
            else:
                stop = start + num
        self.stop = stop
        if num is None:
            num = stop - start
        self.num = num
        assert stop <= len(reader)
        assert stop - start == num

    def __len__(self):
        return self.num

    def iter(self, yield_key=False):
        self._reader.seek(self.start)
        gen = self._reader.iter(yield_key)
        for _ in range(self.num):
            yield next(gen)

    __iter__ = iter

    def rawiter(self, yield_key=False):
        self._reader.seek(self.start)
        gen = self._reader.rawiter(yield_key)
        for _ in range(self.num):
            yield next(gen)

    def seek(self, index):
        self._reader.seek(index - self.start)


def split_reader(reader, num_ranges):
    """
    Split the given reader into a number of equally-sized Ranges.
    The length of ranges may vary by up to 1
    if len(reader) is not divisible by num_ranges.

    :param reader: reader to split
    :param num_ranges: number of ranges to create
    :return: list of Range augments wrapping reader
    """
    num = len(reader) / num_ranges
    ind = [int(round(num * i)) for i in range(num_ranges)] + [len(reader)]
    ranges = [Range(copy(reader), start, num=stop - start)
              for start, stop in zip(ind[:-1], ind[1:])]
    return ranges

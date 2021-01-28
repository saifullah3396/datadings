"""
An Augment wraps a
:py:class:`Reader <datadings.reader.reader.Reader`
and changes how samples are iterated over.
How readers are used is largely unaffected.
"""

import random
from abc import ABCMeta, abstractmethod
from copy import copy
from math import ceil
from random import Random


class Augment(object):
    """
    Abstract base class for Augments.

    Warning:
        Augments are not thread safe!

    Parameters:
        reader: The reader to augment.
    """
    __metaclass__ = ABCMeta

    def __init__(self, reader):
        self._reader = reader

    def __enter__(self):
        self._reader.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._reader.__exit__(exc_type, exc_val, exc_tb)

    def __len__(self):
        return len(self._reader)

    def __iter__(self):
        return self.iter()

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
    Iterate over a
    :py:class:`Reader <datadings.reader.reader.Reader` in random order.

    Warning:
        Augments are not thread safe!
    """

    def iter(self, yield_key=False):
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


class _Placeholder(int):
    def __eq__(self, other):
        return int.__eq__(self, other)


class QuasiShuffler(Augment):
    def __init__(self, reader, buf_size, chunk_size, seed=None):
        super().__init__(reader)
        self._i = 0
        self._n = len(reader)
        self.reader = reader
        # buf size is a multiple of chunk_size
        self.buf_size = int(ceil(buf_size / chunk_size)) * chunk_size
        self.chunk_size = chunk_size
        self.num_chunks = ceil(self._n / chunk_size)
        self._seed = len(reader) * self.buf_size * chunk_size if seed is None else seed
        self._offset = 0

    def seek(self, index):
        self._i = index
        self._offset = index // self._n * self._n

    # noinspection PyStatementEffect
    def iter(self, yield_key=False, raw=False):
        rand = Random()
        rand.seed(self._seed + self._offset, version=2)

        chunk_order = list(range(self.num_chunks))
        rand.shuffle(chunk_order)
        chunks = ((
            c * self.chunk_size,
            min(self._n, (c + 1) * self.chunk_size)
        ) for c in chunk_order)

        # create buffer
        buffer = []

        # for index < buffer size, fill buffer with actual data
        if self._i < self.buf_size:
            for _, (a, b) in zip(range(self.buf_size // self.chunk_size), chunks):
                buffer.extend(self.reader.slice(a, b, yield_key=yield_key, raw=raw))
        # for larger index, fill with placeholders
        else:
            for _, (a, b) in zip(range(self.buf_size // self.chunk_size), chunks):
                buffer.extend(map(_Placeholder, range(a, b)))
        buf_size = len(buffer)

        i = 0
        # yield from remaining chunks
        for a, b in chunks:
            index = a
            # store placeholders until current index is reached
            if i < self._i:
                for index in range(a, b):
                    if i >= self._i:
                        break
                    buffer_pos = rand.randrange(buf_size)
                    buffer[buffer_pos] = _Placeholder(index)
                    i += 1
            # once index is reached, read samples from reader
            if i >= self._i:
                for sample in self.reader.slice(index, b, yield_key=yield_key, raw=raw):
                    buffer_pos = rand.randrange(buf_size)
                    buffer_value = buffer[buffer_pos]
                    if type(buffer_value) is _Placeholder:
                        buffer_value = self.reader.get(buffer_value, yield_key=yield_key, raw=raw)
                    yield buffer_value
                    buffer[buffer_pos] = sample
                    self._i += 1
                    i += 1

        # yield rest of buffer
        buffer_start = max(0, buf_size - self._n + self._i)
        for buffer_value in buffer[buffer_start:]:
            if type(buffer_value) is _Placeholder:
                buffer_value = self.reader.get(buffer_value, yield_key=yield_key, raw=raw)
            yield buffer_value
            self._i += 1

        self._i = 0
        self._offset += self._n

    __iter__ = iter

    def rawiter(self, yield_key=False):
        return self.iter(yield_key=yield_key, raw=True)


class Cycler(Augment):
    """
    Infinitely cycle a :py:class:`Reader <datadings.reader.reader.Reader`.

    Warning:
        Augments are not thread safe!
    """
    def iter(self, yield_key=False):
        while 1:
            for sample in self._reader.iter(yield_key):
                yield sample
            self._reader.seek(0)

    __iter__ = iter

    def rawiter(self, yield_key=False):
        while 1:
            for sample in self._reader.rawiter(yield_key):
                yield sample
            self._reader.seek(0)

    def seek(self, index):
        self._reader.seek(index)


class Range(Augment):
    """
    Extract a range of samples from a given reader.

    Warning:
        Augments are not thread safe!

    Either stop or num must be given.
    If both are given, an assert will be triggered if
    stop - start != num.
    An assert will also trigger if stop > len(reader).
    Same holds for start + num > len(reader)

    Parameters:
        reader: Reader to sample from.
        start: Index to start from.
        stop: Index to stop at.
        num: Number of samples iterators will yield.
    """
    def __init__(self, reader, start=0, stop=None, num=None):
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
        self._reader.seek(self.start + index)


def split_reader(reader, num_ranges):
    """
    Split the given reader into a number of equally-sized Ranges.
    The length of ranges may vary by up to 1
    if len(reader) is not divisible by num_ranges.

    Parameters:
        reader: Reader to split.
        num_ranges: Number of ranges to create.

    Returns:
        list of Range augments wrapping reader.
    """
    num = len(reader) / num_ranges
    ind = [int(round(num * i)) for i in range(num_ranges)] + [len(reader)]
    ranges = [Range(copy(reader), start, num=stop - start)
              for start, stop in zip(ind[:-1], ind[1:])]
    return ranges

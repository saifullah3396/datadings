"""
An Augment wraps a
:py:class:`Reader <datadings.reader.reader.Reader`
and changes how samples are iterated over.
How readers are used is largely unaffected.
"""

from abc import ABCMeta, abstractmethod
from math import ceil
from random import Random


__all__ = ('Range', 'Repeater', 'Cycler', 'Shuffler', 'QuasiShuffler')


class Augment(object):
    """
    Base class for Augments.

    Warning:
        Augments are not thread safe!

    Parameters:
        reader: the reader to augment
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
    def iter(
            self,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        """
        Create an iterator.

        Parameters:
            yield_key: if True, yields (key, sample) pairs.
            raw: if True, yields samples as msgpacked messages.
            copy: if False, allow the reader to return data as
                  ``memoryview`` objects instead of ``bytes``
            chunk_size: number of samples read at once;
                        bigger values can increase throughput,
                        but also memory

        Returns:
            Iterator
        """
        pass

    def rawiter(self, yield_key=False):
        """
        Create an iterator that yields samples as msgpacked messages.
        Order and number of samples is determined by the Augment.

        Included for backwards compatibility and may be deprecated and
        subsequently removed in the future.

        Parameters:
            yield_key: If True, yields (key, sample) pairs.

        Returns:
            Iterator
        """
        return self.iter(yield_key=yield_key, raw=True)

    @abstractmethod
    def seek(self, index):
        pass


class Range(Augment):
    """
    Extract a range of samples from a given reader.

    ``start`` and ``stop`` behave like the parameters of the
    ``range`` function.

    Parameters:
        reader: reader to sample from
        start: start of range
        stop: stop of range
    """
    def __init__(self, reader, start=0, stop=None):
        super().__init__(reader)
        n = len(reader)

        if start < 0:
            start += n
        if start < 0 or start >= n:
            raise IndexError(f'index {start} out of range for length {n} reader')

        self.start, self.stop, _ = slice(start, stop).indices(n)

    def iter(
            self,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        return self._reader.iter(
            start=self.start,
            stop=self.stop,
            yield_key=yield_key,
            raw=raw,
            copy=copy,
            chunk_size=chunk_size,
        )

    def seek(self, index):
        self._reader.seek(self.start + index)


class Shuffler(Augment):
    """
    Iterate over a
    :py:class:`Reader <datadings.reader.reader.Reader` in random order.

    Parameters:
        reader: The reader to augment.
        seed: optional random seed; defaults to len(reader)

    Warning:
        Augments are not thread safe!
    """
    def __init__(self, reader, seed=None):
        super().__init__(reader)
        self._n = len(reader)
        self._seed = self._n if seed is None else seed
        self._offset = 0
        self._i = 0

    def seek(self, index):
        self._i = index
        self._offset = index // self._n * self._n

    def iter(
            self,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        n = self._n
        rand = Random()
        rand.seed(self._seed + self._offset, version=2)
        order = list(range(n))
        rand.shuffle(order)
        for i in order[self._i:]:
            yield self._reader.get(i, yield_key=yield_key, raw=raw, copy=copy)
            self._i += 1

        self._i = 0
        self._offset += self._n


class _Placeholder(int):
    def __eq__(self, other):
        return int.__eq__(self, other)


class QuasiShuffler(Augment):
    """
    A slightly less random than a true
    :py:class:`Reader <datadings.reader.augment.Shuffler` but much faster.

    The dataset is divided into equal-size chunks that are read in random
    order.
    Shuffling follows these steps:

    1. Fill the buffer with chunks.
    2. Read the next chunk.
    3. Select a random sample from the buffer and yield it.
    4. Replace the sample with the next sample from the current chunk.
    5. If there are chunks left, goto 2.

    This means there are typically more samples from the current chunk
    in the buffer than there would be if a true shuffle was used.
    This effect is more pronounced for smaller fractions :math:`\\frac{B}{C}`
    where :math:`C` is the chunk size and :math:`B` the buffer size.
    As a rule of thumb it is sufficient to keep :math:`\\frac{B}{C}` roughly
    equal to the number of classes in the dataset.

    Note:
        Seeking and resuming iteration with a new iterator are relatively
        costly operations. If possible create one iterator and use it
        repeatedly.

    Parameters:
        reader: the reader to wrap
        buf_size: size of the buffer; values less than 1 are interpreted
                  as fractions of the dataset length; bigger values improve
                  randomness, but use more memory
        chunk_size: size of each chunk; bigger values improve performance,
                    but reduce randomness
        seed: random seed to use;
              defaults to ``len(reader) * self.buf_size * chunk_size``
    """
    def __init__(self, reader, buf_size=0.01, chunk_size=16, seed=None):
        super().__init__(reader)
        self._i = 0
        self._n = len(reader)
        if buf_size < 1:
            buf_size = int(ceil(self._n * 0.01))
        self.reader = reader
        # buf size is a multiple of chunk_size
        self.buf_size = int(ceil(buf_size / chunk_size)) * chunk_size
        self.chunk_size = chunk_size
        self.num_chunks = ceil(self._n / chunk_size)
        self._seed = len(reader) * self.buf_size * chunk_size if seed is None else seed
        self._offset = 0

    def seek(self, index):
        if index < 0:
            raise IndexError('index must be > 0')
        self._i = index % self._n
        self._offset = index // self._n * self._n

    # noinspection PyMethodOverriding
    def iter(
            self,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=None,
    ):
        chunk_size = chunk_size or self.chunk_size
        rand = Random()
        rand.seed(self._seed + self._offset, version=2)

        chunk_order = list(range(self.num_chunks))
        rand.shuffle(chunk_order)
        chunks = ((
            c * chunk_size,
            min(self._n, (c + 1) * chunk_size)
        ) for c in chunk_order)

        reader = self.reader

        # create buffer
        buffer = []

        # for index < buffer size, fill buffer with actual data
        if self._i < self.buf_size:
            for _, (a, b) in zip(range(self.buf_size // chunk_size), chunks):
                buffer.extend(reader.slice(a, b, yield_key=yield_key, raw=raw))
        # for larger index, fill with placeholders
        else:
            for _, (a, b) in zip(range(self.buf_size // chunk_size), chunks):
                buffer.extend(map(_Placeholder, range(a, b)))

        # buffer may be smaller than requested if last chunk is used and
        # dataset does not cleanly divide into chunks
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
                for sample in reader.slice(index, b, yield_key=yield_key, raw=raw):
                    buffer_pos = rand.randrange(buf_size)
                    buffer_value = buffer[buffer_pos]
                    if type(buffer_value) is _Placeholder:
                        buffer_value = reader.get(buffer_value, yield_key=yield_key, raw=raw)
                    yield buffer_value
                    buffer[buffer_pos] = sample
                    self._i += 1
                    i += 1

        # yield rest of buffer
        buffer_start = max(0, buf_size - self._n + self._i)
        for buffer_value in buffer[buffer_start:]:
            if type(buffer_value) is _Placeholder:
                buffer_value = reader.get(buffer_value, yield_key=yield_key, raw=raw)
            yield buffer_value
            self._i += 1

        self._i = 0
        self._offset += self._n


class Repeater(Augment):
    """
    Repeat a :py:class:`Reader <datadings.reader.reader.Reader`
    a fixed number of times.

    Warning:
        Augments are not thread safe!
    """
    def __init__(self, reader, times):
        super().__init__(reader)
        self.times = times

    def iter(
            self,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        for _ in range(self.times):
            yield from self._reader.iter(
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )

    def seek(self, index):
        self._reader.seek(index % len(self._reader))


class Cycler(Augment):
    """
    Infinitely cycle a :py:class:`Reader <datadings.reader.reader.Reader`.

    Warning:
        Augments are not thread safe!
    """
    def iter(
            self,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        while 1:
            yield from self._reader.iter(
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )

    def seek(self, index):
        self._reader.seek(index % len(self._reader))

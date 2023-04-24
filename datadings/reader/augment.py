"""
An Augment wraps a
:py:class:`Reader <datadings.reader.reader.Reader`
and changes how samples are iterated over.
How readers are used is largely unaffected.
"""

from abc import ABCMeta
from math import ceil
from random import Random

from .reader import Reader


__all__ = ('Range', 'Repeater', 'Cycler', 'Shuffler', 'QuasiShuffler')


class Augment(Reader, metaclass=ABCMeta):
    """
    Base class for Augments.

    Warning:
        Augments are not thread safe!

    Parameters:
        reader: the reader to augment
    """
    __metaclass__ = ABCMeta

    def __init__(self, reader):
        super().__init__()
        self._len = len(reader)
        self._reader = reader

    def __enter__(self):
        self._reader.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._reader.__exit__(exc_type, exc_val, exc_tb)

    def __len__(self):
        return self._len

    def __contains__(self, key):
        return key in self._reader

    def find_key(self, index):
        return self._reader.find_key(index)

    def find_index(self, key):
        return self._reader.find_index(key)

    def get(self, index, yield_key=False, raw=False, copy=True):
        return self._reader.get(index=index, yield_key=yield_key, raw=raw, copy=copy)

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        return self._reader.slice(start=start, stop=stop, yield_key=yield_key, raw=raw, copy=copy)


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

        if start < 0:
            start += self._len
        if start < 0 or start >= self._len:
            raise IndexError(f'index {start} out of range for length {self._len} reader')

        self.start, self.stop, _ = slice(start, stop).indices(self._len)
        self.n = self.stop - self.start

    def __len__(self):
        return self.stop - self.start

    def __contains__(self, key):
        try:
            self.find_index(key)
            return True
        except KeyError:
            return False

    def find_key(self, index):
        if index >= self.n:
            raise IndexError("index out of range")
        return self._reader.find_key(index + self.start)

    def find_index(self, key):
        i = self._reader.find_index(key)
        if i < self.start or i >= self.stop:
            raise KeyError(key)
        return i - self.start

    def get(self, index, yield_key=False, raw=False, copy=True):
        if index > self.n or index < -self.n:
            raise IndexError("index out of range")
        if index < 0:
            index = self.stop - index
        else:
            index += self.start
        return self._reader.get(index=index, yield_key=yield_key, raw=raw, copy=copy)

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        start += self.start
        if stop is None:
            stop = self.n
        stop += self.start
        return self._reader.slice(start=start, stop=stop, yield_key=yield_key, raw=raw, copy=copy)


class Shuffler(Augment):
    """
    Iterate over a
    :py:class:`Reader <datadings.reader.reader.Reader` in random order.
    If no seed is given the length of the reader is used for reproducibility.
    Creating an iterator increments the seed by 1.
    Use :py:meth:`Shuffler.seed` to set the desired seed instead.

    Warning:
        Shuffler only implements iteration.
        Random access methods ``find_index``, ``find_key``, ``get``,
        and ``slice`` raise ``NotImplementedError``.

    Parameters:
        reader: The reader to augment.
        seed: optional random seed; defaults to len(reader)

    Warning:
        Augments are not thread safe!
    """
    def __init__(self, reader, seed=None):
        super().__init__(reader)
        self._seed = self._len if seed is None else seed

    def seed(self, seed):
        self._seed = seed

    def _iter_impl(
            self,
            start,
            stop,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        rand = Random()
        rand.seed(self._seed, version=2)
        self._seed += 1
        order = list(range(self._len))
        rand.shuffle(order)
        for i in order[start:stop]:
            yield self._reader.get(i, yield_key=yield_key, raw=raw, copy=copy)

    def find_key(self, index):
        raise NotImplementedError("Shuffler does not implement random access")

    def find_index(self, key):
        raise NotImplementedError("Shuffler does not implement random access")

    def get(self, index, yield_key=False, raw=False, copy=True):
        raise NotImplementedError("Shuffler does not implement random access")

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        raise NotImplementedError("Shuffler does not implement random access")


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
        if buf_size < 1:
            buf_size = ceil(self._len * 0.01)
        buf_size = int(buf_size)
        self.reader = reader
        # buf size is a multiple of chunk_size
        self.buf_size = int(ceil(buf_size / chunk_size)) * chunk_size
        self.chunk_size = chunk_size
        self.num_chunks = ceil(self._len / chunk_size)
        self._seed = len(reader) * self.buf_size * chunk_size if seed is None else seed
        self._offset = 0

    def seed(self, seed):
        self._seed = seed
        self._offset = 0

    def _iter_impl(
            self,
            start,
            stop,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        self._offset += 1
        n = stop - start
        # early stop if nothing to do
        if n <= 0:
            return

        chunk_size = chunk_size or self.chunk_size
        rand = Random()
        # -1 because we incremented earlier, before early stop
        rand.seed(self._seed + self._offset - 1, version=2)

        chunk_order = list(range(self.num_chunks))
        rand.shuffle(chunk_order)
        chunks = ((
            c * chunk_size,
            min(self._len, (c + 1) * chunk_size)
        ) for c in chunk_order)

        reader = self.reader

        # create buffer
        buffer = []

        # for index < buffer size, fill buffer with actual data
        if start < self.buf_size:
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
        n = stop - start
        # yield from remaining chunks
        for a, b in chunks:
            index = a
            # store placeholders until current index is reached
            if i < start:
                for index in range(a, b):
                    if i >= start:
                        break
                    buffer_pos = rand.randrange(buf_size)
                    buffer[buffer_pos] = _Placeholder(index)
                    i += 1
            # once index is reached, read samples from reader
            if i >= start:
                for sample in reader.slice(index, b, yield_key=yield_key, raw=raw):
                    if n <= 0:
                        break
                    buffer_pos = rand.randrange(buf_size)
                    buffer_value = buffer[buffer_pos]
                    if type(buffer_value) is _Placeholder:
                        buffer_value = reader.get(buffer_value, yield_key=yield_key, raw=raw)
                    yield buffer_value
                    buffer[buffer_pos] = sample
                    i += 1
                    n -= 1
            if n <= 0:
                break

        # yield rest of buffer
        buffer_start = max(0, buf_size - self._len + i)
        for buffer_value in buffer[buffer_start:]:
            if n <= 0:
                break
            if type(buffer_value) is _Placeholder:
                buffer_value = reader.get(buffer_value, yield_key=yield_key, raw=raw)
            yield buffer_value
            n -= 1

    def find_key(self, index):
        raise NotImplementedError("QuasiShuffler does not implement random access")

    def find_index(self, key):
        raise NotImplementedError("QuasiShuffler does not implement random access")

    def get(self, index, yield_key=False, raw=False, copy=True):
        raise NotImplementedError("QuasiShuffler does not implement random access")

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        raise NotImplementedError("QuasiShuffler does not implement random access")


def _repeater_index(i, length, total):
    if i < -total or i >= total:
        raise IndexError(f'index {i} out of range for length {total} reader')
    if i < 0:
        i += total
    return i % length, i // length


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

    def __len__(self):
        return self._len * self.times

    def __contains__(self, key):
        return key in self._reader

    def find_key(self, index):
        return self._reader.find_key(index)

    def find_index(self, key):
        return self._reader.find_index(key)

    def get(self, index, yield_key=False, raw=False, copy=True):
        total = self._len * self.times
        index, _ = _repeater_index(index, self._len, total)
        return self._reader.get(index=index, yield_key=yield_key, raw=raw, copy=copy)

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        yield from self.iter(start, stop=stop, yield_key=yield_key, raw=raw, copy=copy)

    def _iter_impl(
            self,
            start,
            stop,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        total = self._len * self.times
        # actual start/stop index in the wrapped reader
        # and which number repetition start/stop fall into
        start, start_rep = _repeater_index(start, self._len, total)
        stop, stop_rep = _repeater_index(stop, self._len, total)
        # for the simplest case, both start and stop are in the same repetition
        if start_rep == stop_rep:
            return self._reader.iter(
                start,
                stop=stop,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
        # if they're not, we first need to yield from the start index
        if start_rep != stop_rep:
            yield from self._reader.iter(
                start,
                stop=None,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
        # this is the number of full iterations between start and stop
        for _ in range(stop_rep - start_rep - 1):
            yield from self._reader.iter(
                0,
                stop=self._len,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
        # and the remaining items until stop index
        if start_rep != stop_rep:
            yield from self._reader.iter(
                0,
                stop=stop,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )


def _cycler_index(i, length):
    if i < 0:
        raise IndexError(f'Cycler does not support negative index {i}')
    return i % length, i // length


class Cycler(Augment):
    """
    Infinitely cycle a :py:class:`Reader <datadings.reader.reader.Reader`.

    Warning:
        Augments are not thread safe!
    """
    def iter(
            self,
            start=None,
            stop=None,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        if start is None:
            start = 0
        else:
            start, start_rep = _cycler_index(start, self._len)

        # loop forever from start index
        if stop is None:
            yield from self._reader.iter(
                0,
                stop=self._len,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
            while True:
                yield from self._reader.iter(
                    0,
                    stop=self._len,
                    yield_key=yield_key,
                    raw=raw,
                    copy=copy,
                    chunk_size=chunk_size,
                )
        else:
            stop, stop_rep = _cycler_index(stop, self._len)

        # for the simplest case, both start and stop are in the same repetition
        if start_rep == stop_rep:
            return self._reader.iter(
                start,
                stop=stop,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
        # if they're not, we first need to yield from the start index
        if start_rep != stop_rep:
            yield from self._reader.iter(
                start,
                stop=None,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
        # this is the number of full iterations between start and stop
        for _ in range(stop_rep - start_rep - 1):
            yield from self._reader.iter(
                0,
                stop=self._len,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )
        # and the remaining items until stop index
        if start_rep != stop_rep:
            yield from self._reader.iter(
                0,
                stop=stop,
                yield_key=yield_key,
                raw=raw,
                copy=copy,
                chunk_size=chunk_size,
            )

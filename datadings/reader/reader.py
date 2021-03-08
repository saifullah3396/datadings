from abc import ABCMeta
from abc import abstractmethod

from math import ceil


class Reader(metaclass=ABCMeta):
    """
    Abstract base class for dataset readers.

    Readers should be used as context managers::

        with Reader(...) as reader:
            for sample in reader:
                [do dataset things]

    Subclasses must implement the following methods:

    * __exit__
    * __len__
    * __contains__
    * find_key
    * find_index
    * get
    * slice
    """
    # attributes that are ignored by __copy__
    _do_not_copy = ()

    def __init__(self):
        self._i = 0
        self.getitem_max_slice_length = 512
        self.getitem_chunk_size = 64

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __contains__(self, key):
        pass

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __copy__(self):
        cls = self.__class__
        reader = cls.__new__(cls)
        reader.__dict__.update(
            (k, v) for k, v in self.__dict__.items()
            if k not in cls._do_not_copy
        )
        return reader

    @abstractmethod
    def find_key(self, index):
        """
        Returns the key of the sample with the given index.
        """
        pass

    @abstractmethod
    def find_index(self, key):
        """
        Returns the index of the sample with the given key.
        """
        pass

    def seek_index(self, index):
        """
        Seek to the given index.
        """
        n = len(self)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(f'index {index} out of range for length {n} reader')
        self._i = index

    def seek(self, index):
        """
        Seek to the given index.
        Alias for ``seek_index``.
        """
        self.seek_index(index)

    def seek_key(self, key):
        """
        Seek to the sample with the given key.
        """
        self.seek_index(self.find_index(key))

    @abstractmethod
    def get(self, index, yield_key=False, raw=False, copy=True):
        """
        Returns sample at given index.

        ``copy=False`` allows the reader to use zero-copy mechanisms.
        Data may be returned as ``memoryview`` objects rather than ``bytes``.
        This can improve performance, but also drastically increase memory
        consumption, since one sample can keep the whole slice in memory.

        Parameters:
            index: Index of the sample
            yield_key: If True, returns (key, sample)
            raw: If True, returns sample as msgpacked message
            copy: if False, allow the reader to return data as
                  ``memoryview`` objects instead of ``bytes``

        Returns:
            Sample as index.
        """
        pass

    @abstractmethod
    def slice(self, start, stop=None, step=None, yield_key=False, raw=False, copy=True):
        """
        Returns a generator of samples selected by the given slice.

        ``copy=False`` allows the reader to use zero-copy mechanisms.
        Data may be returned as ``memoryview`` objects rather than ``bytes``.
        This can improve performance, but also drastically increase memory
        consumption, since one sample can keep the whole slice in memory.

        Parameters:
            start: start index of slice
            stop: stop index of slice
            step: stride of slice
            yield_key: if True, yield (key, sample)
            raw: if True, returns sample as msgpacked message
            copy: if False, allow the reader to return data as
                  ``memoryview`` objects instead of ``bytes``

        Returns:
            Iterator of selected samples
        """
        pass

    def next(self):
        """
        Returns the next sample.

        This can be slow for file-based readers if a lot of
        samples are to be read.
        Consider using iter instead::

            it = iter(reader)
            while 1:
                next(it)
                ...

        Or simply loop over the reader::

            for sample in reader:
                ...
        """
        try:
            sample = self.get(self._i)
            self._i += 1
            return sample
        except IndexError:
            raise StopIteration

    def __next__(self):
        return self.next()

    def rawnext(self) -> bytes:
        """
        Return the next sample msgpacked as raw bytes.

        This can be slow for file-based readers if a lot of
        samples are to be read.
        Consider using iter instead::

            it = iter(reader)
            while 1:
                next(it)
                ...

        Or simply loop over the reader::

            for sample in reader:
                ...

        Included for backwards compatibility and may be deprecated and
        subsequently removed in the future.
        """
        try:
            sample = self.get(self._i, raw=True)
            self._i += 1
            return sample
        except IndexError:
            raise StopIteration

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            # use iter if number of samples is large
            if stop - start >= self.getitem_max_slice_length:
                return self.iter(start, stop, step, chunk_size=self.getitem_chunk_size)
            # otherwise use slice directly
            else:
                return self.slice(start, stop, step)
        else:
            return self.get(index)

    def _iter_impl(
            self,
            start=None,
            stop=None,
            step=None,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
            chunk_stride=16,
            chunk_threshold=3,
    ):
        # load chunks
        # if chunk size is at least as big as step size
        # and step size is small
        if chunk_size >= step and step <= chunk_threshold:
            n = stop - start
            chunks = int(ceil(n / chunk_size))
            for c in range(chunks):
                a = c * chunk_stride
                b = min(n, a + chunk_size)
                for sample in self.slice(a, b, step, yield_key, raw, copy):
                    yield sample
                    self._i += 1
        # load individual samples for large step sizes
        else:
            for i in range(start, stop, step):
                yield self.get(i, yield_key=yield_key, raw=raw)
                self._i += 1

    def iter(
            self,
            start=None,
            stop=None,
            step=None,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
            chunk_threshold=3,
    ):
        """
        Iterate over the dataset.

        ``start``, ``stop``, and ``step`` behave like the parameters of the
        ``range`` function, though ``step`` must be greater than 0.

        ``copy=False`` allows the reader to use zero-copy mechanisms.
        Data may be returned as ``memoryview`` objects rather than ``bytes``.
        This can improve performance, but also drastically increase memory
        consumption, since one sample can keep the whole slice in memory.

        Parameters:
            start: start of range; if None, current index is used
            stop: stop of range
            step: step of range; must be >= 1
            yield_key: if True, yields (key, sample) pairs.
            raw: if True, yields samples as msgpacked messages.
            copy: if False, allow the reader to return data as
                  ``memoryview`` objects instead of ``bytes``
            chunk_size: number of samples read at once;
                        bigger values can increase throughput,
                        but also memory
            chunk_threshold: for step sizes greater than this
                             threshold samples will be loaded
                             one by one instead of in chunks

        Returns:
            Iterator
        """
        n = len(self)

        if start is None:
            if self._i == n:
                # return to start
                self.seek_index(0)
            start = self._i
        else:
            if start < 0:
                start += n
            if start < 0 or start >= n:
                raise IndexError(f'index {start} out of range for length {n} reader')

        start, stop, step = slice(start, stop, step).indices(len(self))
        if step < 1:
            raise ValueError('step size must be >= 1')

        # optimize chunk size for step > 1
        # removes "dangling" samples that do not need to be loaded
        # example: chunk size 12, step 4
        # X---X---X---
        # (12 - 1) // 4 * 4 + 1 = 9
        # X---X---X
        chunk_size = (chunk_size - 1) // step * step + 1
        # since dangling samples are removed from chunk size,
        # chunks must start where the next sample in the sequence would be
        chunk_stride = chunk_size + step - 1

        yield from self._iter_impl(
            start,
            stop,
            step,
            yield_key,
            raw,
            copy,
            chunk_size,
            chunk_stride,
            chunk_threshold,
        )

    def __iter__(self):
        return self.iter()

    def rawiter(self, yield_key=False):
        """
        Create an iterator that yields samples as msgpacked messages.

        Included for backwards compatibility and may be deprecated and
        subsequently removed in the future.

        Parameters:
            yield_key: If True, yields (key, sample) pairs.

        Returns:
            Iterator
        """
        return self.iter(yield_key=yield_key, raw=True)

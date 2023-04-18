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
    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        """
        Returns a generator of samples selected by the given slice.

        ``copy=False`` allows the reader to use zero-copy mechanisms.
        Data may be returned as ``memoryview`` objects rather than ``bytes``.
        This can improve performance, but also drastically increase memory
        consumption, since one sample can keep the whole slice in memory.

        Parameters:
            start: start index of slice
            stop: stop index of slice
            yield_key: if True, yield (key, sample)
            raw: if True, returns sample as msgpacked message
            copy: if False, allow the reader to return data as
                  ``memoryview`` objects instead of ``bytes``

        Returns:
            Iterator of selected samples
        """
        pass

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                raise ValueError('step must be 1')
            # use iter if number of samples is large
            if stop - start >= self.getitem_max_slice_length:
                return self.iter(start, stop, chunk_size=self.getitem_chunk_size)
            # otherwise use slice directly
            else:
                return self.slice(start, stop)
        else:
            return self.get(index)

    def _iter_impl(
            self,
            start,
            stop,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        chunks = int(ceil((stop - start) / chunk_size))
        for c in range(chunks):
            a = c * chunk_size + start
            b = min(stop, a + chunk_size)
            yield from self.slice(a, b, yield_key, raw, copy)

    def iter(
            self,
            start=None,
            stop=None,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        """
        Iterate over the dataset.

        ``start`` and ``stop`` behave like the parameters of the
        ``range`` function0.

        ``copy=False`` allows the reader to use zero-copy mechanisms.
        Data may be returned as ``memoryview`` objects rather than ``bytes``.
        This can improve performance, but also drastically increase memory
        consumption, since one sample can keep the whole slice in memory.

        Parameters:
            start: start of range; if None, current index is used
            stop: stop of range
            yield_key: if True, yields (key, sample) pairs.
            raw: if True, yields samples as msgpacked messages.
            copy: if False, allow the reader to return data as
                  ``memoryview`` objects instead of ``bytes``
            chunk_size: number of samples read at once;
                        bigger values can increase throughput,
                        but require more memory

        Returns:
            Iterator
        """
        n = len(self)

        if start is None:
            start = 0
        else:
            if start < 0:
                start += n
            if start < 0 or start >= n:
                raise IndexError(f'index {start} out of range for length {n} reader')

        start, stop, _ = slice(start, stop).indices(len(self))
        yield from self._iter_impl(
            start,
            stop,
            yield_key=yield_key,
            raw=raw,
            copy=copy,
            chunk_size=chunk_size,
        )

    def __iter__(self):
        return self.iter()

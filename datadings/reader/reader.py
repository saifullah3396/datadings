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
    * find_key
    * find_index
    * get
    * slice
    """
    _do_not_copy = ()

    def __init__(self):
        self._i = 0

    @abstractmethod
    def __len__(self):
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

    seek = seek_index

    def seek_key(self, key):
        """
        Seek to the sample with the given key.
        """
        self.seek_index(self.find_index(key))

    @abstractmethod
    def get(self, index, yield_key=False, raw=False):
        """
        Returns sample at given index.

        Parameters:
            index: Index of the sample
            yield_key: If True, returns (key, sample)
            raw: If True, returns sample as msgpacked message

        Returns:
            Sample as index.
        """
        pass

    @abstractmethod
    def slice(self, start, stop=None, step=None, yield_key=False, raw=False):
        """
        Returns a generator of samples selected by the given slice.

        Parameters:
            start: start index of slice
            stop: stop index of slice
            step: stride of slice
            yield_key: if True, yield (key, sample)
            raw: if True, returns sample as msgpacked message

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
        sample = self.get(self._i)
        self._i += 1
        return sample

    __next__ = next

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
        """
        sample = self.get(self._i, raw=True)
        self._i += 1
        return sample

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            return self.slice(start, stop, step)
        else:
            return self.get(index)

    def iter(
            self,
            start=None,
            stop=None,
            step=None,
            yield_key=False,
            raw=False,
            chunk_size=16,
            chunk_threshold=3,
    ):
        """
        Iterate over the dataset.

        Start, stop, and step behave like the parameters of the
        ``range`` function.
        Step must be >= 1.

        Parameters:
            start: start of range
            stop: stop of range
            step: step of range; must be >= 1
            yield_key: If True, yields (key, sample) pairs.
            raw: If True, yields samples as msgpacked messages.
            chunk_size: number of samples read at once;
                        bigger values can increase throughput,
                        but also memory
            chunk_threshold: for step sizes greater than this
                             threshold samples will be loaded
                             one by one instead of in chunks
        Returns:
            Iterator
        """
        start = start or self._i
        start, stop, step = slice(start, stop, step).indices(len(self))
        if step < 1:
            raise ValueError('step size must be >= 1')

        # load chunks
        # if chunk size is at least as big as step size
        # and step size is small
        if chunk_size >= step and step <= chunk_threshold:
            n = stop - start
            # optimize chunk size for step > 2
            # removes "dangling" samples that do not need to be loaded
            # example: chunk size 12, step 4
            # X---X---X---
            # (12 - 1) // 4 * 4 + 1 = 9
            # X---X---X
            chunk_size = (chunk_size - 1) // step * step + 1
            # since dangling samples are removed from chunk size,
            # chunks must start where the next sample in the sequence would be
            chunk_stride = chunk_size + step - 1
            chunks = int(ceil(n / chunk_size))
            for c in range(chunks):
                a = c * chunk_stride
                b = min(n, a + chunk_size)
                for sample in self.slice(a, b, step, yield_key=yield_key, raw=raw):
                    yield sample
                    self._i += 1
        # load individual samples for large step sizes
        else:
            for i in range(start, stop, step):
                yield self.get(i, yield_key=yield_key, raw=raw)
                self._i += 1

    __iter__ = iter

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

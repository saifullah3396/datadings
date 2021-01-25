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

    @abstractmethod
    def __len__(self):
        pass

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

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

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, stride = index.indices(len(self))
            return self.slice(start, stop, stride)
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
    ):
        """
        Iterate over the dataset.
        Start, stop and

        Parameters:
            start: start of slice
            stop: stop of slice
            step: step of slice
            yield_key: If True, yields (key, sample) pairs.
            raw: If True, yields samples as msgpacked messages.
            chunk_size: number of samples read at once;
                        bigger values can increase throughput,
                        but also memory

        Returns:
            Iterator
        """
        n = len(self)
        start, stop, stride = slice(start, stop, step).indices(n)
        if stride > 3:
            n = stop - start
            chunk_size = chunk_size // stride * stride + 1
            chunk_stride = chunk_size + stride - 1
            chunks = int(ceil(n / chunk_size))
            for c in range(chunks):
                a = c * chunk_stride
                b = min(n, a + chunk_size)
                yield from self.slice(a, b, stride, yield_key=yield_key, raw=raw)
        else:
            for i in range(start, stop, stride):
                yield self.get(i, yield_key=yield_key, raw=raw)

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

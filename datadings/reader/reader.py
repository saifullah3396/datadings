from abc import ABCMeta, abstractmethod


class Reader(object):
    """
    Abstract base class for dataset readers.

    Subclasses must implement iteration and seeking methods.

    Readers should be used as context managers::

        with Reader('dataset.msgpack') as reader:
            for sample in reader:
                [do dataset things]
    """
    __metaclass__ = ABCMeta

    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter(self, yield_key=False):
        """
        Iterate over the dataset, starting with the current index.

        Parameters:
            yield_key: If True, yields (key, sample) pairs.
        """
        try:
            if yield_key:
                while 1:
                    yield self.get_key(), self.next()
            else:
                while 1:
                    yield self.next()
        except IndexError:
            return

    __iter__ = iter

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __next__(self):
        pass

    @abstractmethod
    def next(self):
        """
        Returns the next sample.
        """
        pass

    @abstractmethod
    def rawnext(self) -> bytes:
        """
        Return the next sample msgpacked as raw bytes.
        """
        pass

    def rawiter(self, yield_key=False):
        """
        Like iter, but yields samples msgpacked as raw bytes.

        Parameters:
            yield_key: If True, yields (key, sample) pairs.
        """
        try:
            if yield_key:
                while 1:
                    yield self.get_key(), self.rawnext()
            else:
                while 1:
                    yield self.rawnext()
        except IndexError:
            return

    @abstractmethod
    def seek_index(self, index):
        """
        Seek to the given index.
        """
        pass

    @abstractmethod
    def seek(self, index):
        """
        Seek to the given index.
        """
        pass

    @abstractmethod
    def seek_key(self, key):
        """
        Seek to the sample with the given key.
        """
        pass

    @abstractmethod
    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        pass

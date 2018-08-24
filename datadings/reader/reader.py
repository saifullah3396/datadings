from __future__ import print_function, division, unicode_literals

from abc import ABCMeta, abstractmethod

from msgpack import packb as _packb, unpackb as _unpackb
from msgpack_numpy import encode as _encode, decode as _decode


class Reader(object):
    """
    Abstract base class for dataset readers.

    Subclasses must implement iteration and seeking methods.

    Readers can be used as a context manager:

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
        :param yield_key: if True, yields (key, sample) pairs
        """
        if yield_key:
            while 1:
                yield self.get_key(), self.next()
        else:
            while 1:
                yield self.next()

    __iter__ = iter

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __next__(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def rawnext(self):
        """
        Return the next sample as raw bytes.
        :return:
        """
        pass

    def rawiter(self, yield_key=False):
        """
        Like iter, but yields raw bytes.

        :param yield_key: if True, yields (key, sample) pairs
        """
        if yield_key:
            while 1:
                yield self.get_key(), self.rawnext()
        else:
            while 1:
                yield self.rawnext()

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


def pack(b):
    return _packb(b, encoding='utf8', use_bin_type=True, default=_encode)


def unpack(b):
    return _unpackb(b, encoding='utf8', object_hook=_decode)

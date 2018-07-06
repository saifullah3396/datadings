from __future__ import print_function, division, unicode_literals

import io
import codecs
import hashlib
import os.path as pt
import random
from collections import OrderedDict
from abc import ABCMeta
from abc import abstractmethod

from msgpack import packb as _packb
from msgpack import unpackb as _unpackb
from msgpack import unpackb as _unpack
from msgpack_numpy import encode as _encode
from msgpack_numpy import decode as _decode


def _load_index(path):
    """
    Load an index file as list of (file, position) pairs.

    @param path: path to index file
    @return: list of (file, position) index pairs
    """
    try:
        with io.FileIO(path, 'rb') as f:
            return _unpack(f, encoding='utf8', object_pairs_hook=list)
    except IOError:
        return OrderedDict()


def hash_md5hex(path, read_size=64*1024):
    """
    Calculate the (hexadecimal) MD5 hash of a file.

    @param path: file path
    @param read_size: read-ahead size
    @return: hexadecimal MD5 hash as string
    """
    with io.FileIO(path, 'rb') as f:
        md5 = hashlib.md5()
        while 1:
            data = f.read(read_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def load_md5file(path):
    """
    Load a text-based "md5".

    :param path: path to md5 file
    :return: dict {file: hash}
    """
    with codecs.open(path, encoding='utf-8') as f:
        return dict(l.strip().split('  ')[::-1] for l in f)


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


class ListReader(Reader):
    """
    Abstract base class for dataset readers.

    Subclasses must implement iteration and seeking methods.

    Readers can be used as a context manager:

        with Reader('dataset.msgpack') as reader:
            for sample in reader:
                [do dataset things]
    """
    def __init__(self, samples):
        self._samples = samples
        self._index = {s.get('key', 1): i for i, s in enumerate(samples)}
        self._keys = {i: s.get('key', i) for i, s in enumerate(samples)}
        self._i = 0

    def __enter__(self):
        return self

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

    def __len__(self):
        return len(self._samples)

    def __next__(self):
        return self._samples[self._i]

    next = __next__

    def rawnext(self):
        """
        Return the next sample as raw bytes.
        :return:
        """
        return pack(self.next())

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

    def seek_index(self, index):
        """
        Seek to the given index.
        """
        self._i = index

    seek = seek_index

    def seek_key(self, key):
        self._i = self._index.get(key, None) or self._i

    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        return self._keys.get(index or self._i, self._i)


def pack(b):
    return _packb(b, encoding='utf8', use_bin_type=True, default=_encode)


def unpack(b):
    return _unpackb(b, encoding='utf8', object_hook=_decode)


class MsgpackReader(Reader):
    """
    Simple, iterable and seekable reader for messagepack dataset files.
    Needs dataset and index file.
    Can Optionally verify the integrity of dataset and index files
    if md5 file is present.
    """
    def __init__(self, infile):
        """
        :param infile: dataset file to load
        :raises IOError: if dataset or index cannot be loaded
        """
        self._path = infile
        self._infile = io.FileIO(infile, 'rb')
        key_to_position = _load_index(infile + '.index')
        self._keys = [v for v, _ in key_to_position]
        self._positions = [v for _, v in key_to_position]
        self._key_to_index_dict = None
        self._len = len(self._positions)
        self._i = 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._infile.close()

    def __del__(self):
        if not self._infile.closed:
            self._infile.close()

    def __len__(self):
        return self._len

    def __next__(self):
        return unpack(self.rawnext())

    next = __next__

    def rawnext(self):
        """
        Return the next sample as raw bytes.
        :return:
        """
        try:
            n = self._positions[self._i + 1] - self._positions[self._i]
            self._i += 1
            return self._infile.read(n)
        except IndexError:
            raw = self._infile.read()
            if not raw:
                raise StopIteration()
            return raw

    def seek_index(self, index):
        """
        Seek to the given index.
        """
        self._infile.seek(self._positions[index], 0)
        self._i = index

    seek = seek_index

    @property
    def _key_to_index(self):
        if self._key_to_index_dict is None:
            self._key_to_index_dict = dict(enumerate(self._keys))
        return self._key_to_index_dict

    def seek_key(self, key):
        """
        Seek to the sample with the given key.
        """
        index = self._key_to_index[key]
        self.seek_index(index)

    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        return self._keys[index or self._i]

    def verify_data(self, read_size=64*1024):
        """
        Hash the dataset file and verify against the md5 file.

        :param read_size: read-ahead size
        :return: True if verification was successful
        """
        hashes = load_md5file(self._path + '.md5')
        dataname = pt.basename(self._path)
        return hashes[dataname] == hash_md5hex(self._path, read_size)

    def verify_index(self, read_size=64*1024):
        """
        Hash the index file and verify against the md5 file.

        :param read_size: read-ahead size
        :return: True if verification was successful
        """
        hashes = load_md5file(self._path + '.md5')
        indexname = pt.basename(self._path) + '.index'
        return hashes[indexname] == hash_md5hex(self._path + '.index', read_size)


IdentityReader = MsgpackReader


class _Augment(object):
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


class Shuffler(_Augment):
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
                self._reader.seek_index(i)
                yield self._reader.get_key(), self._reader.next()
        else:
            for i in order:
                self._reader.seek_index(i)
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


class Cycler(_Augment):
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
            self._reader.seek_index(0)

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
            self._reader.seek_index(0)

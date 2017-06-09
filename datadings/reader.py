import io
import codecs
import hashlib
import os.path as pt
import random
from collections import OrderedDict
from abc import ABCMeta
from abc import abstractmethod

import msgpack


def _load_index(path):
    """
    Load an index file as list of (file, position) pairs.

    @param path: path to index file
    @return: list of (file, position) index pairs
    """
    try:
        with io.FileIO(path, 'rb') as f:
            return msgpack.unpack(f, encoding='utf8',
                                  object_pairs_hook=list)
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
    Simple, iterable and seekable reader for dataset files.
    Needs dataset and index file.
    Optionally md5 file to verify integrity of dataset and index.

    This is an abstract class.
    It cannot be instantiated.
    Reader subclasses have to implement the _convert method.

    Readers can be used as a context manager in "with"
    statements:

        with Reader('dataset.msgpack') as reader:
            for sample in reader:
                [do dataset things]
    """
    __metaclass__ = ABCMeta

    def __init__(self, infile):
        """
        :param infile: dataset file to load
        :raises IOError: if dataset or index cannot be loaded
        """
        self._path = infile
        self._infile = io.FileIO(infile, 'rb')
        try:
            key_to_position = _load_index(infile + '.index')
            e = None
        except IOError as e:
            key_to_position = []
        self._keys = [v for v, _ in key_to_position]
        self._positions = [v for _, v in key_to_position]
        self._key_to_index_dict = None
        self._len = len(self._positions)
        self._i = 0
        if e:
            raise e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._infile.close()

    def __iter__(self):
        return self

    iter = __iter__

    def __len__(self):
        return self._len

    def __next__(self):
        return self._convert(
            msgpack.unpackb(self.rawnext(), encoding='utf8')
        )

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

    def rawiter(self):
        """
        Like iter, but yields raw bytes.
        :return:
        """
        while 1:
            yield self.rawnext()

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

    @abstractmethod
    def _convert(self, item):
        """
        Implement this method to convert samples to proper
        data types they are returned.
        """
        pass


class IdentityReader(Reader):
    """
    Simple reader that does no conversion.
    Use this if you don't know the dataset type.
    """
    def _convert(self, sample):
        return sample


class Shuffler(object):
    """
    Iterate over the contents of a Reader in random order.
    Not thread safe!
    """
    def __init__(self, reader):
        """
        Reader to shuffle.
        Not thread safe!

        :param reader: Reader to shuffle
        """
        self._reader = reader

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

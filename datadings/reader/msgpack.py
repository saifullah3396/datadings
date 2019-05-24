from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import codecs
import hashlib
import io
from collections import OrderedDict
from os import path as pt

from msgpack import unpack as _unpack

from .reader import Reader
from .reader import unpack


class MsgpackReader(Reader):
    """
    Simple, iterable and seekable reader for messagepack dataset files.
    Needs dataset and index file.
    Can Optionally verify the integrity of dataset and index files
    if md5 file is present.
    """
    def __init__(self, infile, buffering=4*1024*1024):
        """
        :param infile: dataset file to load
        :raises IOError: if dataset or index cannot be loaded
        """
        self._path = infile
        self._buffering = buffering
        self._infile = io.open(infile, 'rb', buffering)
        key_to_position = _load_index(infile + '.index')
        self._keys = [v for v, _ in key_to_position]
        self._positions = [v for _, v in key_to_position]
        self._key_to_index_dict = None
        self._len = len(self._positions)
        self._i = 0

    def __copy__(self):
        reader = MsgpackReader.__new__(MsgpackReader)
        reader.__dict__.update(self.__dict__)
        reader._infile = io.open(self._path, 'rb', self._buffering)
        return reader

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
                raise
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
            self._key_to_index_dict = dict(
                (k, i) for i, k in enumerate(self._keys)
            )
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

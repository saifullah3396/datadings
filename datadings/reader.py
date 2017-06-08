import io
import codecs
import hashlib
import os.path as pt
import random
from collections import OrderedDict

import msgpack


def _load_index(path):
    try:
        with io.FileIO(path, 'rb') as f:
            return msgpack.unpack(f, encoding='utf8',
                                  object_pairs_hook=list)
    except IOError:
        return OrderedDict()


def hash_md5hex(path, read_size=64*1024):
    with io.FileIO(path, 'rb') as f:
        md5 = hashlib.md5()
        while 1:
            data = f.read(read_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def load_md5file(path):
    with codecs.open(path, encoding='utf-8') as f:
        return dict(l.strip().split('  ')[::-1] for l in f)


class Reader(object):
    def __init__(self, infile):
        self._path = infile
        self._infile = io.FileIO(infile, 'rb')
        key_to_position = _load_index(infile + '.index')
        self._keys = [v for v, _ in key_to_position]
        self._positions = [v for _, v in key_to_position]
        self._key_to_index_dict = None
        self._len = len(self._positions)
        self._i = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._infile.close()

    def __iter__(self):
        return self

    def __len__(self):
        return self._len

    def __next__(self):
        return self._convert(msgpack.unpackb(self.rawnext(), encoding='utf8'))

    next = __next__

    def rawnext(self):
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
        while 1:
            yield self.rawnext()

    def seek_index(self, index):
        self._infile.seek(self._positions[index], 0)
        self._i = index

    seek = seek_index

    @property
    def _key_to_index(self):
        if self._key_to_index_dict is None:
            self._key_to_index_dict = dict(enumerate(self._keys))
        return self._key_to_index_dict

    def seek_key(self, key):
        index = self._key_to_index[key]
        self.seek_index(index)

    def get_key(self, index=None):
        return self._keys[index or self._i]

    def verify_data(self, read_size=64*1024):
        hashes = load_md5file(self._path + '.md5')
        dataname = pt.basename(self._path)
        return hashes[dataname] == hash_md5hex(self._path, read_size)

    def verify_index(self, read_size=64*1024):
        hashes = load_md5file(self._path + '.md5')
        indexname = pt.basename(self._path) + '.index'
        return hashes[indexname] == hash_md5hex(self._path + '.index', read_size)

    def _convert(self, item):
        raise NotImplementedError()


class IdentityReader(Reader):
    def _convert(self, sample):
        return sample


class Shuffler(object):
    def __init__(self, reader):
        self._reader = reader

    def __iter__(self):
        n = len(self._reader)
        order = list(range(n))
        random.shuffle(order)
        for i in order:
            self._reader.seek_index(i)
            yield self._reader.next()

    def rawiter(self, yield_key=False):
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

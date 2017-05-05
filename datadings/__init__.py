from __future__ import print_function, division

import io
from collections import OrderedDict

import numpy as np
import msgpack


def _default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()


class Writer(object):
    def __init__(self, outfile):
        self._path = outfile
        self._outfile = io.open(outfile, 'wb', 1024*1024)
        self._packer = msgpack.Packer(
            default=_default, use_bin_type=True, encoding='utf8'
        )
        self._indices = OrderedDict()
        self.written = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._outfile.flush()
        self._outfile.close()
        with io.FileIO(self._path + '.index', 'w') as f:
            msgpack.pack(self._indices, f)

    def _write(self, data):
        self._outfile.write(self._packer.pack(data))
        self.written += 1

    def write(self, *args):
        raise NotImplementedError()


class ImageWriter(Writer):
    def write(self, jpegdata, image):
        self._indices[image.filename] = self._outfile.tell()
        Writer._write(self, (jpegdata, image))


def _load_index(path):
    try:
        with io.FileIO(path, 'rb') as f:
            return msgpack.unpack(f, encoding='utf8',
                                  object_pairs_hook=OrderedDict)
    except IOError:
        return OrderedDict()


class Reader(object):
    def __init__(self, infile):
        self._infile = io.FileIO(infile, 'rb')
        self._name_index = _load_index(infile + '.index')
        self._name_to_index = {f: i for i, f in enumerate(self._name_index)}
        self._index = list(self._name_index.values())
        self._len = len(self._index)
        self._i = 0
        self._unpacker = msgpack.Unpacker(self._infile, encoding='utf8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._infile.close()

    def __iter__(self):
        return self

    def __len__(self):
        return self._len

    def __next__(self):
        self._i += 1
        return self._convert(next(self._unpacker))

    next = __next__

    def rawiter(self):
        while self._i < self._len - 1:
            self._i += 1
            yield self._infile.read(
                self._index[self._i] - self._index[self._i - 1]
            )
        yield self._infile.read()

    def seek_index(self, i):
        self._infile.seek(self._index[i], 0)
        self._i = i
        self._unpacker = msgpack.Unpacker(self._infile, encoding='utf8')

    def seek_file(self, name):
        self._infile.seek(self._name_index[name], 0)
        self._i = self._name_to_index[name]
        self._unpacker = msgpack.Unpacker(self._infile, encoding='utf8')

    def _convert(self, item):
        raise NotImplementedError()

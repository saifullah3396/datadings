import os.path as pt
import io
import codecs
import hashlib
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
        self._indices = OrderedDict()
        self.written = 0
        self._hash = hashlib.md5()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._outfile.flush()
        self._outfile.close()
        with io.FileIO(self._path + '.index', 'wb') as f:
            indexdata = msgpack.packb(self._indices)
            f.write(indexdata)
            indexhash = hashlib.md5(indexdata).hexdigest()
        with codecs.open(self._path + '.md5', 'w') as f:
            name = pt.basename(self._path)
            f.write('%s  %s\n' % (self._hash.hexdigest(), name))
            f.write('%s  %s\n' % (indexhash, name + '.index'))

    def _write_data(self, packed):
        self._hash.update(packed)
        self._outfile.write(packed)
        self.written += 1

    def _write(self, sample):
        packed = msgpack.packb(
            sample,
            default=_default, use_bin_type=True, encoding='utf8'
        )
        self._write_data(packed)

    def write(self, *args):
        raise NotImplementedError()


class ImageWriter(Writer):
    def write(self, image):
        self._indices[image.filename] = self._outfile.tell()
        self._write(image)

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

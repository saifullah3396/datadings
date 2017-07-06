import os.path as pt
import io
import codecs
import hashlib
from collections import OrderedDict
from abc import ABCMeta
from abc import abstractmethod

import numpy as np
import msgpack


def _default(o):
    """
    Convert numpy arrays to lists.
    Other objects are untouched.
    """
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


class Writer(object):
    """
    Writers can be used to create dataset files along with index
    and md5 hash.

    Writer is an abstract class.
    It cannot be instantiated.
    Subclasses must implement the abstract write method.

    Can be used as context manager in "with" statements:

        with Writer('dataset.msgpack') as writer:
            for sample in samples:
                writer.write(sample)

    The writer is then automatically closed and index and md5
    files are written.
    """
    __metaclass__ = ABCMeta

    def __init__(self, outfile):
        """
        :param outfile: path to the dataset file
        """
        self._path = outfile
        self._outfile = io.open(outfile, 'wb', 1024*1024)
        self._indices = OrderedDict()
        self.written = 0
        self._hash = hashlib.md5()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """
        Flush and close the dataset file and write index and
        md5 files.
        """
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

    @abstractmethod
    def write(self, *args):
        """
        Write a sample to the dataset file.

        :param args: sample data to write
        """
        pass


class RawWriter(Writer):
    """
    Writer for raw data.
    No packing is done.
    write requires key and data as arguments.
    """
    def write(self, key, data):
        self._indices[key] = self._outfile.tell()
        self._write_data(data)


class FileWriter(Writer):
    """
    Writer for file-based datasets.
    Requires samples with a "filename" attribute to use as key.
    """
    def write(self, image):
        self._indices[image.filename] = self._outfile.tell()
        self._write(image)

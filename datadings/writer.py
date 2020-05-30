from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os
import os.path as pt
import io
import codecs
import hashlib
from collections import OrderedDict
from abc import ABCMeta
from abc import abstractmethod

from .msgpack import make_packer
from .msgpack import packb
from .tools import make_printer


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

    def __init__(self, outfile, **kwargs):
        """
        :param outfile: path to the dataset file
        :param kwargs: keyword arguments for datadings.tools.make_printer
        """
        self._path = outfile
        outdir = pt.dirname(outfile)
        if not pt.exists(outdir):
            os.makedirs(outdir)
        self._outfile = io.open(outfile, 'wb', 1024*1024)
        self._indices = OrderedDict()
        self.written = 0
        self._hash = hashlib.md5()
        self._packer = make_packer()
        if 'desc' not in kwargs:
            kwargs['desc'] = pt.basename(outfile)
        self._printer = make_printer(**kwargs)

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
            indexdata = packb(self._indices)
            f.write(indexdata)
            indexhash = hashlib.md5(indexdata).hexdigest()
        with codecs.open(self._path + '.md5', 'w') as f:
            name = pt.basename(self._path)
            f.write('%s  %s\n' % (self._hash.hexdigest(), name))
            f.write('%s  %s\n' % (indexhash, name + '.index'))
        self._printer.close()
        print('%d samples written' % self.written)

    def _write_data(self, packed):
        self._hash.update(packed)
        self._outfile.write(packed)
        self.written += 1
        self._printer()

    def _write(self, sample):
        self._write_data(self._packer.pack(sample))

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
        if key in self._indices:
            raise ValueError('duplicate key %r not allowed' % key)
        self._indices[key] = self._outfile.tell()
        self._write_data(data)


class FileWriter(Writer):
    """
    Writer for file-based datasets.
    Requires sample dicts with a unique "key" value.
    """
    def write(self, sample):
        key = sample['key']
        if key in self._indices:
            raise ValueError('duplicate key %r not allowed' % key)
        self._indices[key] = self._outfile.tell()
        self._write(sample)

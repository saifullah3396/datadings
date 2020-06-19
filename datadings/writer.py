import os
import os.path as pt
import hashlib
from collections import OrderedDict
from abc import ABCMeta
from abc import abstractmethod

from .msgpack import make_packer
from .msgpack import packb
from .tools import make_printer
from .tools import query_user


class Writer(object):
    """
    Writers can be used to create dataset files along with index
    and MD5 hash.

    Writer is an abstract class.
    It cannot be instantiated.
    Subclasses must implement the abstract write method.

    It is recommended to use writers as context manager in "with" statements:

        with Writer('dataset.msgpack') as writer:
            for sample in samples:
                writer.write(sample)

    The writer is then automatically closed and index and md5
    files are written.

    Important:
        If ``overwrite`` is ``False``, the user will be prompted to overwrite
        an existing file.
        The user can now:

        - Accept to overwrite the file.
        - Decline, which raises a :py:class:`FileExistsError`.
          The program should continue as if writing had finished.
        - Abort, which raises a :py:class:`KeyboardInterrupt`.
          The program should abort immediately.

    Parameters:
        outfile: Path to the dataset file.
        overwrite: If outfile exists, force overwriting.
        kwargs: Keyword arguments for :py:func:`datadings.tools.make_printer`.
    """
    __metaclass__ = ABCMeta

    def __init__(self, outfile, buffering=4*1024*1024, overwrite=False, **kwargs):
        self._path = outfile
        outdir = pt.dirname(outfile)
        if not pt.exists(outdir):
            os.makedirs(outdir)
        if pt.exists(outfile) and not overwrite:
            answer = query_user(pt.basename(outfile) + ' exists, overwrite?')
            if answer == 'no':
                raise FileExistsError(outfile)
            elif answer == 'abort':
                raise KeyboardInterrupt(outfile)
        self._outfile = open(outfile, 'wb', buffering)
        self._index = OrderedDict()
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
        Flush and close the dataset file and write index and MD5 files.
        """
        self._outfile.flush()
        self._outfile.close()
        with open(self._path + '.index', 'wb') as f:
            indexdata = packb(self._index)
            f.write(indexdata)
            indexhash = hashlib.md5(indexdata).hexdigest()
        with open(self._path + '.md5', 'w', encoding='utf-8') as f:
            name = pt.basename(self._path)
            f.write('%s  %s\n' % (self._hash.hexdigest(), name))
            f.write('%s  %s\n' % (indexhash, name + '.index'))
        self._printer.close()
        print('%d samples written' % self.written)

    def _write_data(self, key, packed):
        if key in self._index:
            raise ValueError('duplicate key %r not allowed' % key)
        self._index[key] = self._outfile.tell()
        self._hash.update(packed)
        self._outfile.write(packed)
        self.written += 1
        self._printer()

    def _write(self, key, sample):
        self._write_data(key, self._packer.pack(sample))

    @abstractmethod
    def write(self, *args):
        """
        Write a sample to the dataset file.

        Parameters:
            args: Sample data to write.
        """
        pass


class RawWriter(Writer):
    """
    Writer for raw data.
    No packing is done.
    :py:meth:`write` requires ``key`` and ``data`` as arguments.
    """
    def write(self, key, data):
        self._write_data(key, data)


class FileWriter(Writer):
    """
    Writer for file-based datasets.
    Requires sample dicts with a unique ``"key"`` value.
    """
    def write(self, sample):
        self._write(sample['key'], sample)

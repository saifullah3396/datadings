from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
import hashlib

from ..tools import make_printer
from ..tools import query_user
from ..tools import hash_md5hex
from ..tools import path_append
from ..tools.msgpack import make_packer
from ..index import write_offsets
from ..index import write_keys
from ..index import write_key_hashes
from ..index import write_filter


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

    def __init__(self, outfile, buffering=0, overwrite=False, **kwargs):
        outfile = Path(outfile)
        self._path = outfile
        outfile.parent.mkdir(parents=True, exist_ok=True)
        if outfile.exists() and not overwrite:
            answer = query_user(f'{outfile.name} exists, overwrite?')
            if answer == 'no':
                raise FileExistsError(outfile)
            elif answer == 'abort':
                raise KeyboardInterrupt(outfile)
        self._outfile = outfile.open('wb', buffering)
        self._keys = []
        self._keys_set = set()
        self._offsets = [0]
        self.written = 0
        self._hash = hashlib.md5()
        self._packer = make_packer()
        if 'desc' not in kwargs:
            kwargs['desc'] = outfile.name
        self._disable = kwargs.get('disable', False)
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
        paths = [
            write_offsets(self._offsets, self._path),
            write_keys(self._keys, self._path),
            write_key_hashes(self._keys, self._path),
            write_filter(self._keys, self._path),
        ]
        with path_append(self._path, '.md5').open('w', encoding='utf-8') as f:
            f.write(f'{self._hash.hexdigest()}  {self._path.name}\n')
            for path in paths:
                f.write(f'{hash_md5hex(path)}  {path.name}\n')
        self._printer.close()
        if not self._disable:
            print('%d samples written' % self.written)

    def _write_data(self, key, packed):
        if key in self._keys_set:
            raise ValueError('duplicate key %r not allowed' % key)
        self._keys.append(key)
        self._keys_set.add(key)
        self._hash.update(packed)
        self._outfile.write(packed)
        self._offsets.append(self._outfile.tell())
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

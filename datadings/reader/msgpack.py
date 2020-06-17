from typing import Union

import os
from os import path as pt
from pathlib import Path

from .reader import Reader
from ..msgpack import unpack
from ..msgpack import unpackb
from ..tools import load_md5file
from ..tools import hash_md5hex


class MsgpackReader(Reader):
    """
    Reader for msgpack files in the
    :ref:`datadings format description<file-format>`.

    Needs at least data and index file.
    For example, if the dataset file is ``some_dir/dataset.msgpack``,
    then the reader will attempt to load the index from
    ``some_dir/dataset.msgpack.index``.

    Can optionally verify the integrity of data and index files if
    the md5 file ``some_dir/dataset.msgpack.md5`` is present.

    Note:
        The default read-ahead buffer size is 4MB.
        That's a lot of bytes, which is good for fast sequential access.
        Reduce this to roughly the size of a single sample for best
        random access performance.

    Parameters:
        path: Dataset file to load.
        buffering: Read buffer size in bytes.
                   Reduce this for faster random access.

    Raises:
        IOError: If dataset or index cannot be loaded.
    """
    def __init__(
            self,
            path: Union[str, Path],
            buffering=4 * 1024 * 1024
    ):
        self._path = str(path)
        self._buffering = buffering
        self._infile = open(path, 'rb', buffering)
        self._keys, self._positions = _load_index(path, buffering)
        self._positions.append(os.stat(path).st_size)
        self._key_to_index_dict = None
        self._len = len(self._keys)
        self._i = 0

    def __copy__(self):
        reader = MsgpackReader.__new__(MsgpackReader)
        reader.__dict__.update(self.__dict__)
        reader._infile = open(self._path, 'rb', self._buffering)
        return reader

    def _close(self):
        if hasattr(self, 'infile') and not self._infile.closed:
            self._infile.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def __del__(self):
        self._close()

    def __len__(self):
        return self._len

    def __next__(self):
        return unpackb(self.rawnext())

    next = __next__

    def rawnext(self):
        n = self._positions[self._i+1] - self._positions[self._i]
        self._infile.seek(self._positions[self._i], 0)
        self._i += 1
        return self._infile.read(n)

    def seek_index(self, index):
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
        index = self._key_to_index[key]
        self.seek_index(index)

    def get_key(self, index=None):
        return self._keys[index or self._i]

    def verify_data(self, read_size=64*1024, progress=False):
        """
        Hash the dataset file and verify against the md5 file.

        Parameters:
            read_size: Read-ahead size in bytes.
            progress: display progress

        Returns:
            True if verification was successful.
        """
        hashes = load_md5file(self._path + '.md5')
        dataname = pt.basename(self._path)
        md5 = hash_md5hex(self._path, read_size, progress)
        return hashes[dataname] == md5

    def verify_index(self, read_size=64*1024, progress=False):
        """
        Hash the index file and verify against the md5 file.

        Parameters:
            read_size: Read-ahead size in bytes.
            progress: display progress

        Returns:
            True if verification was successful.
        """
        hashes = load_md5file(self._path + '.md5')
        indexname = pt.basename(self._path) + '.index'
        md5 = hash_md5hex(self._path + '.index', read_size, progress)
        return hashes[indexname] == md5


def _load_index(path, buffering=4*1024*1024):
    """
    Load dataset index as two lists of keys and positions.

    Parameters:
        path: Path to dataset file without ``.index``.

    Returns:
        Keys and positions lists of equal length.
    """
    if pt.exists(path + '.index'):
        with open(path + '.index', 'rb', buffering) as f:
            pairs = unpack(f, object_hook=None, object_pairs_hook=list)
            return [k for k, _ in pairs], [p for _, p in pairs]
    else:
        raise IOError('index for %r not found' % path)

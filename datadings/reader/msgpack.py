from typing import Union

from pathlib import Path

from .reader import Reader
from ..tools import path_append
from ..tools import load_md5file
from ..tools import hash_md5hex
from ..tools import hash_string
from ..tools.cached_property import cached_property
from ..tools.msgpack import unpackb
from ..index import keys_len
from ..index import load_keys
from ..index import load_key_hashes
from ..index import load_offsets
from ..index import legacy_index_len
from ..index import legacy_load_index


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
    _do_not_copy = '_infile'

    def __init__(
            self,
            path: Union[str, Path],
            buffering=0
    ):
        super().__init__()
        path = Path(path)

        # check existence of data file
        if not path.exists():
            raise FileNotFoundError(f'{path} not found')

        # check existence of legacy or new-style index
        legacy_index_path = path_append(path, '.index')
        offsets_path = path_append(path, '.offsets')
        if not (offsets_path.exists() or legacy_index_path.exists()):
            raise FileNotFoundError(f'neither {offsets_path} nor {legacy_index_path} found')

        self._path = path
        self._buffering = buffering
        # try to init from new-style index
        try:
            self._len = keys_len(path)
        # new-style index not found, try legacy index
        except FileNotFoundError:
            self._len = legacy_index_len(path)

    def __len__(self):
        return self._len

    def _close(self):
        if hasattr(self, 'infile') and not self._infile.closed:
            self._infile.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def __del__(self):
        self._close()

    @cached_property
    def _legacy_index(self):
        return legacy_load_index(self._path)

    @cached_property
    def _keys(self):
        try:
            return load_keys(self._path)
        except FileNotFoundError:
            return self._legacy_index[0]

    @cached_property
    def _offsets(self):
        try:
            return load_offsets(self._path)
        except FileNotFoundError:
            return self._legacy_index[1]

    @cached_property
    def _hash_to_index(self):
        try:
            hashes = load_key_hashes(self._path)
        except FileNotFoundError:
            hashes = map(hash_string, self._keys)
        return {h: i for i, h in enumerate(hashes)}

    @cached_property
    def _infile(self):
        return open(self._path, 'rb', self._buffering)

    def find_index(self, key):
        h = hash_string(key)
        try:
            return self._hash_to_index[h]
        except KeyError:
            raise KeyError(key)

    def __contains__(self, key):
        h = hash_string(key)
        return h in self._hash_to_index

    def find_key(self, index):
        return self._keys[index]

    def get(self, index, yield_key=False, raw=False, copy=True):
        pos = self._offsets
        offset = pos[index]
        n = pos[index+1] - offset
        self._infile.seek(offset, 0)
        data = self._infile.read(n)
        if not raw:
            data = unpackb(data)
        if yield_key:
            return self._keys[index], data
        else:
            return data

    def slice(self, start, stop=None, step=None, yield_key=False, raw=False, copy=True):
        start, stop, step = slice(start, stop, step).indices(self._len)
        if step < 1:
            raise ValueError('step size must be >= 1')

        # optimize slice length for step > 2
        # removes "dangling" samples that do not need to be loaded
        # example: chunk size 12, step 4
        # X---X---X---
        # (12 - 1) // 4 * 4 + 1 = 9
        # X---X---X
        n = stop - start
        n = (n - 1) // step * step + 1
        stop = start + n

        pos = self._offsets
        # avoid lazy-loading keys if not necessary
        if yield_key:
            key = self._keys
        else:
            key = None

        offset = pos[start]
        n = pos[stop] - offset
        self._infile.seek(offset, 0)
        buf = self._infile.read(n)
        if not copy:
            buf = memoryview(buf)

        if yield_key:
            if raw:
                for i in range(start, stop, step):
                    yield key[i], buf[pos[i] - offset:pos[i+1] - offset]
            else:
                for i in range(start, stop, step):
                    yield key[i], unpackb(buf[pos[i] - offset:pos[i+1] - offset])
        else:
            if raw:
                for i in range(start, stop, step):
                    yield buf[pos[i] - offset:pos[i+1] - offset]
            else:
                for i in range(start, stop, step):
                    yield unpackb(buf[pos[i] - offset:pos[i+1] - offset])

    def verify_data(self, read_size=512*1024, progress=False):
        """
        Hash the dataset file and verify against the md5 file.

        Parameters:
            read_size: Read-ahead size in bytes.
            progress: display progress

        Returns:
            True if verification was successful.
        """
        path = self._path
        hashes = load_md5file(path_append(path, '.md5'))
        md5 = hash_md5hex(path, read_size, progress)
        return hashes[path.name] == md5

    def verify_index(self, read_size=512*1024, progress=False):
        """
        Hash the index file and verify against the md5 file.

        Parameters:
            read_size: Read-ahead size in bytes.
            progress: display progress

        Returns:
            True if verification was successful.
        """
        path = self._path
        hashes = load_md5file(path_append(path, '.md5'))
        index_path = path_append(path, '.index')
        md5 = hash_md5hex(index_path, read_size, progress)
        return hashes[index_path.name] == md5

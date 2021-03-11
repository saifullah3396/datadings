from typing import Union

from pathlib import Path
import warnings

from .reader import Reader
from ..tools import path_append
from ..tools import load_md5file
from ..tools import hash_md5hex
from ..tools import hash_string
from ..tools.cached_property import cached_property
from ..tools.msgpack import unpackb
from ..index import keys_len
from ..index import load_offsets
from ..index import load_keys
from ..index import hash_keys
from ..index import load_key_hashes
from ..index import load_filter
from ..index import legacy_index_len
from ..index import legacy_load_index
from ..index import SUFFIX_LEGACY_INDEX
from ..index import SUFFIX_OFFSETS
from ..index import SUFFIX_KEYS
from ..index import SUFFIX_KEY_HASHES
from ..index import SUFFIX_FILTER


def _raise_if_none_of_paths_exists(*paths):
    if not any(path.exists() for path in paths):
        if len(paths) > 1:
            raise FileNotFoundError(
                'need at least one of '
                + (', '.join(map(str, paths)))
                + ' but none found'
            )
        else:
            raise FileNotFoundError(f'{paths[0]} not found')


def _warn_if_path_not_exists(path, suffix):
    path = path_append(path, suffix)
    if not path.exists():
        warnings.warn(f'{path} not found, some functionality may not be available')


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

    Parameters:
        path: Dataset file to load.
        buffering: Read buffer size in bytes.

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
        _raise_if_none_of_paths_exists(
            path_append(path, SUFFIX_OFFSETS),
            path_append(path, SUFFIX_LEGACY_INDEX),
        )
        # check existence of optional files
        _warn_if_path_not_exists(path, SUFFIX_KEYS)
        _warn_if_path_not_exists(path, SUFFIX_KEY_HASHES)
        _warn_if_path_not_exists(path, SUFFIX_FILTER)

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
        if '_infile' in self.__dict__:
            f = self._infile
            if not f.closed:
                f.close()
            del self.__dict__['_infile']

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
    def _filter(self):
        return load_filter(self._path)

    @cached_property
    def _hash_to_index(self):
        try:
            salt, hashes = load_key_hashes(self._path)
        except FileNotFoundError:
            salt, hashes = hash_keys(self._keys)
        return salt, {int(h): i for i, h in enumerate(hashes)}

    @cached_property
    def _infile(self):
        return open(self._path, 'rb', self._buffering)

    def find_index(self, key):
        salt, hash_to_index = self._hash_to_index
        h = hash_string(key, salt)
        try:
            return hash_to_index[h]
        except KeyError:
            raise KeyError(key)

    def __contains__(self, key):
        if key in self._filter:
            salt, hash_to_index = self._hash_to_index
            h = hash_string(key, salt)
            return h in hash_to_index
        else:
            return False

    def find_key(self, index):
        return self._keys[index]

    def get(self, index, yield_key=False, raw=False, copy=True):
        pos = self._offsets
        offset = pos[index]
        n = pos[index+1] - offset
        f = self._infile
        f.seek(offset, 0)
        data = f.read(n)
        if not raw:
            data = unpackb(data)
        if yield_key:
            return self._keys[index], data
        else:
            return data

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        start, stop, _ = slice(start, stop).indices(self._len)

        pos = self._offsets
        # avoid lazy-loading keys if not necessary
        if yield_key:
            key = self._keys
        else:
            key = None

        offset = pos[start]
        n = pos[stop] - offset
        f = self._infile
        f.seek(offset, 0)
        buf = f.read(n)
        if not copy:
            buf = memoryview(buf)

        if yield_key:
            if raw:
                for i in range(start, stop):
                    yield key[i], buf[pos[i] - offset:pos[i+1] - offset]
            else:
                for i in range(start, stop):
                    yield key[i], unpackb(buf[pos[i] - offset:pos[i+1] - offset])
        else:
            if raw:
                for i in range(start, stop):
                    yield buf[pos[i] - offset:pos[i+1] - offset]
            else:
                for i in range(start, stop):
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
        index_path = path_append(path, SUFFIX_LEGACY_INDEX)
        md5 = hash_md5hex(index_path, read_size, progress)
        return hashes[index_path.name] == md5

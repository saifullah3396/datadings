from typing import Union

from pathlib import Path

from .reader import Reader
from ..msgpack import unpackb
from ..tools import load_md5file
from ..tools import hash_md5hex
from ..cached_property import cached_property


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
            buffering=0
    ):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'{path} not found')
        self._path = path
        self._buffering = buffering
        self._keys, self._positions = _load_index(path)
        self._positions.append(path.stat().st_size)
        self._len = len(self._keys)

    def __len__(self):
        return self._len

    def _close(self):
        if hasattr(self, 'infile') and not self._infile.closed:
            self._infile.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def __del__(self):
        self._close()

    def __copy__(self):
        reader = MsgpackReader.__new__(MsgpackReader)
        reader.__dict__.update(
            (k, v) for k, v in self.__dict__
            if k not in ('_infile', '_key_to_index_dict')
        )
        return reader

    def find_key(self, index):
        return self._keys[index]

    @cached_property
    def _key_to_index(self):
        return {k: i for i, k in enumerate(self._keys)}

    def find_index(self, key):
        return self._key_to_index[key]

    @cached_property
    def _infile(self):
        return open(self._path, 'rb', self._buffering)

    def get(self, index, yield_key=False, raw=False):
        offset = self._positions[index]
        n = self._positions[index+1] - offset
        self._infile.seek(offset, 0)
        data = self._infile.read(n)
        if not raw:
            data = unpackb(data)
        if yield_key:
            return self._keys[index], data
        else:
            return data

    def slice(self, start, stop=None, step=None, yield_key=False, raw=False):
        start, stop, step = slice(start, stop, step).indices(self._len)
        pos = self._positions
        key = self._keys
        offset = pos[start]
        n = pos[stop] - offset
        self._infile.seek(offset, 0)
        buf = memoryview(self._infile.read(n))
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
        hashes = load_md5file(str(self._path) + '.md5')
        md5 = hash_md5hex(self._path, read_size, progress)
        return hashes[self._path.name] == md5

    def verify_index(self, read_size=512*1024, progress=False):
        """
        Hash the index file and verify against the md5 file.

        Parameters:
            read_size: Read-ahead size in bytes.
            progress: display progress

        Returns:
            True if verification was successful.
        """
        hashes = load_md5file(self._path + '.md5')
        md5 = hash_md5hex(str(self._path) + '.index', read_size, progress)
        return hashes[self._path.name + '.index'] == md5


def _load_index(path: Path):
    """
    Load dataset index as two lists of keys and positions.

    Parameters:
        path: Path to dataset file without ``.index``.

    Returns:
        Keys and positions lists of equal length.
    """
    path = path.parent / (path.name + '.index')
    if path.exists():
        with path.open('rb', 0) as f:
            data = f.read()
        pairs = unpackb(data, object_hook=None, object_pairs_hook=list)
        return [k for k, _ in pairs], [p for _, p in pairs]
    else:
        raise IOError('%r not found' % path)

from typing import Sequence
from typing import Tuple

from pathlib import Path
import logging

from ..tools import path_append_suffix
from ..tools import hash_string_bytes
from ..tools import hash_string
from ..tools.msgpack import make_unpacker
from ..tools.msgpack import unpack
from ..tools.msgpack import unpackb
from ..tools.msgpack import pack

import numpy as np
from simplebloom import BloomFilter


SUFFIX_LEGACY_INDEX = '.index'
SUFFIX_KEYS = '.keys'
SUFFIX_KEY_HASHES = '.key_hashes'
SUFFIX_FILTER = '.filter'
SUFFIX_OFFSETS = '.offsets'


def keys_len(path: Path) -> int:
    """
    Read the dataset length from the keys file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: path to data or keys file

    Returns:
        length of dataset
    """
    with path_append_suffix(path, SUFFIX_KEYS).open('rb') as f:
        return make_unpacker(f, read_size=5).read_array_header()


def load_keys(path: Path) -> Sequence[str]:
    """
    Load keys from file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: path to data or keys file

    Returns:
        list of keys
    """
    with path_append_suffix(path, SUFFIX_KEYS).open('rb') as f:
        return unpack(f)


def load_key_hashes(path: Path) -> Tuple[bytes, Sequence[int]]:
    """
    Load key hashes from file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: path to data or key hashes file

    Returns:
        hash salt and list of key hashes
    """
    with path_append_suffix(path, SUFFIX_KEY_HASHES).open('rb') as f:
        salt = f.read(8)
        return salt, np.fromfile(f, dtype=np.dtype('>u8')).astype(np.uint64)


def load_filter(path: Path) -> BloomFilter:
    """
    Load a Bloom filter from file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: path to data or filter file

    Returns:
        the Bloom filter
    """
    with path_append_suffix(path, SUFFIX_FILTER).open('rb') as f:
        return BloomFilter.load(f)


def load_offsets(path: Path) -> Sequence[int]:
    """
    Load sample offsets from file.
    First value is always 0 and last is size of data file in bytes,
    so ``len(offsets) = len(dataset) + 1``.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: path to data or offsets file

    Returns:
        sample offsets in data file
    """
    return np.fromfile(path_append_suffix(path, SUFFIX_OFFSETS),
                       dtype=np.dtype('>u8')).astype(np.uint64)


def legacy_index_len(path: Path) -> int:
    """
    Read the dataset length from the legacy index file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: path to data or index file

    Returns:
        length of dataset
    """
    with path_append_suffix(path, SUFFIX_LEGACY_INDEX).open('rb') as f:
        return make_unpacker(f, read_size=5).read_map_header()


def legacy_load_index(path: Path) -> Tuple[Sequence[str], Sequence[int]]:
    """
    Load legacy index as two lists of keys and offsets.
    Semantics of the returned lists are the same as for
    ``load_keys`` and ``load_offsets``.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        path: Path to dataset or index file

    Returns:
        keys and offsets list
    """
    with path_append_suffix(path, SUFFIX_LEGACY_INDEX).open('rb', 0) as f:
        data = f.read()
    pairs = unpackb(data, object_hook=None, object_pairs_hook=list)
    positions = [p for _, p in pairs]
    positions.append(path.stat().st_size)
    return [k for k, _ in pairs], positions


def write_offsets(offsets: Sequence[int], path: Path) -> Path:
    """
    Write list of offsets to file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        offsets: list of offsets
        path: path to data or offsets file

    Returns:
        Path that was written to
    """
    offsets = np.array(offsets, dtype=np.dtype('>u8'))
    path = path_append_suffix(path, SUFFIX_OFFSETS)
    with path.open('wb') as f:
        f.write(memoryview(offsets))
    return path


def write_keys(keys: Sequence[str], path: Path) -> Path:
    """
    Write list of offsets to file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        keys: list of keys
        path: path to data or keys file

    Returns:
        Path that was written to
    """
    path = path_append_suffix(path, SUFFIX_KEYS)
    with path.open('wb') as f:
        pack(keys, f)
    return path


def hash_keys(keys: Sequence[str], max_tries: int = 1000) -> Tuple[bytes, Sequence[int]]:
    """
    Apply the :py:func:`hash_string` function to the given
    list of keys, so the returned hashes are 64 bit integers.
    All hashes are salted and guaranteed collision free.
    If necessary this method will try different salt values

    Parameters:
        keys: list of keys
        max_tries: how many different salt values to try
                   to find collision-free hashes

    Returns:
        used salt and list of key hashes
    """
    hashes = np.zeros(len(keys), dtype=np.dtype('>u8'))
    salt_int = 0
    # change the salt until there are no more hash collisions
    for tri in range(max_tries):
        salt = hash_string_bytes(str(salt_int))
        seen = set()
        for i, key in enumerate(keys):
            h = hash_string(key, salt=salt)
            if h in seen:
                logging.info('hash collision, retry with different salt')
                salt_int += 1
                break
            seen.add(h)
            hashes[i] = h
        else:
            return salt, hashes
    raise RuntimeError(
        f'hash collisions after {max_tries} tries;'
        'try increasing max_tries'
    )


def write_key_hashes(keys: Sequence[str], path: Path) -> Path:
    """
    Hash list of keys and write result to file.

    See ``hash_keys`` for details on hash method.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        keys: list of keys
        path: path to data or offsets file

    Returns:
        Path that was written to
    """
    salt, hashes = hash_keys(keys)
    path = path_append_suffix(path, SUFFIX_KEY_HASHES)
    with path.open('wb') as f:
        f.write(salt)
        f.write(memoryview(hashes))
    return path


def write_filter(keys: Sequence[str], path: Path) -> Path:
    """
    Create a Bloom filter for the given keys and write result to file.

    Correct suffix is appended if path ends with a different suffix.

    Parameters:
        keys: list of keys
        path: path to data or filter file

    Returns:
        Path that was written to
    """
    bf = BloomFilter(max(2, len(keys)))
    for k in keys:
        bf += k
    path = path_append_suffix(path, SUFFIX_FILTER)
    with path.open('wb') as f:
        bf.dump(f)
    return path

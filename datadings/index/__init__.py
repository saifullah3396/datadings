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


SUFFIX_INDEX = '.index'
SUFFIX_KEYS = '.keys'
SUFFIX_KEY_HASHES = '.key_hashes'
SUFFIX_FILTER = '.filter'
SUFFIX_OFFSETS = '.offsets'


def keys_len(path: Path):
    with path_append_suffix(path, SUFFIX_KEYS).open('rb') as f:
        return make_unpacker(f).read_array_header()


def load_keys(path: Path):
    with path_append_suffix(path, SUFFIX_KEYS).open('rb') as f:
        return unpack(f)


def load_key_hashes(path: Path):
    with path_append_suffix(path, SUFFIX_KEY_HASHES).open('rb') as f:
        salt = f.read(8)
        return salt, np.fromfile(f, dtype=np.dtype('>u8')).astype(np.uint64)


def load_filter(path: Path):
    with path_append_suffix(path, SUFFIX_FILTER).open('rb') as f:
        return BloomFilter.load(f)


def load_offsets(path: Path):
    return np.fromfile(path_append_suffix(path, SUFFIX_OFFSETS),
                       dtype=np.dtype('>u8')).astype(np.uint64)


def legacy_index_len(path: Path):
    with path_append_suffix(path, SUFFIX_INDEX).open('rb') as f:
        return make_unpacker(f).read_map_header()


def legacy_load_index(path: Path):
    """
    Load legacy dataset index as two lists of keys and positions.

    Parameters:
        path: Path to dataset or index file

    Returns:
        Keys and positions lists of equal length.
    """
    with path_append_suffix(path, SUFFIX_INDEX).open('rb', 0) as f:
        data = f.read()
    pairs = unpackb(data, object_hook=None, object_pairs_hook=list)
    positions = [p for _, p in pairs]
    positions.append(path.stat().st_size)
    return [k for k, _ in pairs], positions


def write_offsets(positions, path):
    offsets = np.array(positions, dtype=np.dtype('>u8'))
    path = path_append_suffix(path, SUFFIX_OFFSETS)
    with path.open('wb') as f:
        f.write(memoryview(offsets))
    return path


def write_keys(keys, path):
    path = path_append_suffix(path, SUFFIX_KEYS)
    with path.open('wb') as f:
        pack(keys, f)
    return path


def hash_keys(keys):
    hashes = np.zeros(len(keys), dtype=np.dtype('>u8'))
    salt_int = 0
    # change the salt until there are no more hash collisions
    while True:
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
            break
    return salt, hashes


def write_key_hashes(keys, path):
    salt, hashes = hash_keys(keys)
    path = path_append_suffix(path, SUFFIX_KEY_HASHES)
    with path.open('wb') as f:
        f.write(salt)
        f.write(memoryview(hashes))
    return path


def write_bloom_filter(keys, path):
    bf = BloomFilter(len(keys))
    for k in keys:
        bf += k
    path = path_append_suffix(path, SUFFIX_FILTER)
    with path.open('wb') as f:
        bf.dump(f)
    return path

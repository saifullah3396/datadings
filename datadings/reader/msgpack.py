import os
from os import path as pt
import hashlib

from .reader import Reader
from ..msgpack import unpack
from ..msgpack import unpackb


class MsgpackReader(Reader):
    """
    Simple, iterable and seekable reader for messagepack dataset files.
    Needs dataset and index file.
    Can Optionally verify the integrity of dataset and index files
    if md5 file is present.
    """
    def __init__(self, infile, buffering=4*1024*1024):
        """
        :param infile: dataset file to load
        :raises IOError: if dataset or index cannot be loaded
        """
        self._path = infile
        self._buffering = buffering
        self._infile = open(infile, 'rb', buffering)
        self._keys, self._positions = _load_index(infile, buffering)
        self._positions.append(os.stat(infile).st_size)
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
        """
        Return the next sample as raw bytes.
        :return:
        """
        n = self._positions[self._i+1] - self._positions[self._i]
        self._infile.seek(self._positions[self._i], 0)
        self._i += 1
        return self._infile.read(n)

    def seek_index(self, index):
        """
        Seek to the given index.
        """
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
        """
        Seek to the sample with the given key.
        """
        index = self._key_to_index[key]
        self.seek_index(index)

    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        return self._keys[index or self._i]

    def verify_data(self, read_size=64*1024):
        """
        Hash the dataset file and verify against the md5 file.

        :param read_size: read-ahead size
        :return: True if verification was successful
        """
        hashes = load_md5file(self._path + '.md5')
        dataname = pt.basename(self._path)
        return hashes[dataname] == hash_md5hex(self._path, read_size)

    def verify_index(self, read_size=64*1024):
        """
        Hash the index file and verify against the md5 file.

        :param read_size: read-ahead size
        :return: True if verification was successful
        """
        hashes = load_md5file(self._path + '.md5')
        indexname = pt.basename(self._path) + '.index'
        return hashes[indexname] == hash_md5hex(self._path + '.index', read_size)


def _load_index(path, buffering=4*1024*1024):
    """
    Load index as two lists of keys and positions.

    @param path: path to dataset file
    @return: keys and positions lists of equal length
    """
    if pt.exists(path + '.index'):
        with open(path + '.index', 'rb', buffering) as f:
            pairs = unpack(f, object_hook=None, object_pairs_hook=list)
            return [k for k, _ in pairs], [p for _, p in pairs]
    else:
        raise IOError('index for %r not found' % path)


def hash_md5hex(path, read_size=64*1024):
    """
    Calculate the (hexadecimal) MD5 hash of a file.

    @param path: file path
    @param read_size: read-ahead size
    @return: hexadecimal MD5 hash as string
    """
    with open(path, 'rb', read_size) as f:
        md5 = hashlib.md5()
        while 1:
            data = f.read(read_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


def load_md5file(path):
    """
    Load a text-based "md5".

    :param path: path to md5 file
    :return: dict {file: hash}
    """
    with open(path, encoding='utf-8') as f:
        return dict(l.strip().split('  ')[::-1] for l in f)

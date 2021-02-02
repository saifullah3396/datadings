import os

from datadings.reader import DirectoryReader

from .dataset import DIRECTORY_PATH
from .common import missing_keys
from .common import return_after_iter
from .common import seek_index
from .common import seek_key
from .common import find_index
from .common import find_key


PATTERN = str(DIRECTORY_PATH / '{LABEL}' / '*')


def drop_label_directory(sample):
    sample['key'] = sample['key'].rpartition(os.sep)[2]


def test_missing_keys():
    missing_keys(DirectoryReader(PATTERN, initfun=drop_label_directory))


def test_return_after_iter():
    return_after_iter(DirectoryReader(PATTERN, initfun=drop_label_directory))


def test_seek_key():
    seek_key(DirectoryReader(PATTERN, initfun=drop_label_directory))


def test_find_key():
    find_key(DirectoryReader(PATTERN, initfun=drop_label_directory))

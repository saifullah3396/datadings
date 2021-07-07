import os

from datadings.reader import ZipFileReader

from .dataset import ZIP_PATH
from .common import missing_keys
from .common import return_after_iter
from .common import seek_index
from .common import seek_key
from .common import find_index
from .common import find_key
from .common import iter_start
from .common import iter_stop
from .common import iter_range


def drop_label_directory(sample):
    sample['key'] = sample['key'].rpartition('/')[2]


def test_missing_keys():
    missing_keys(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_return_after_iter():
    return_after_iter(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_seek_index():
    seek_index(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_seek_key():
    seek_key(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_find_index():
    find_index(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_find_key():
    find_key(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_iter_start():
    iter_start(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_iter_stop():
    iter_stop(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))


def test_iter_range():
    iter_range(ZipFileReader(ZIP_PATH, initfun=drop_label_directory))

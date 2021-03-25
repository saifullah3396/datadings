import os

from datadings.reader import MsgpackReader

from .dataset import MSGPACK_PATH
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
    sample['key'] = sample['key'].rpartition(os.sep)[2]


def test_missing_keys():
    missing_keys(MsgpackReader(MSGPACK_PATH))


def test_return_after_iter():
    return_after_iter(MsgpackReader(MSGPACK_PATH))


def test_seek_index():
    seek_index(MsgpackReader(MSGPACK_PATH))


def test_seek_key():
    seek_key(MsgpackReader(MSGPACK_PATH))


def test_find_index():
    find_index(MsgpackReader(MSGPACK_PATH))


def test_find_key():
    find_key(MsgpackReader(MSGPACK_PATH))


def test_iter_start():
    iter_start(MsgpackReader(MSGPACK_PATH))


def test_iter_stop():
    iter_stop(MsgpackReader(MSGPACK_PATH))


def test_iter_range():
    iter_range(MsgpackReader(MSGPACK_PATH))
